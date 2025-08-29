# Minimal AST/inspect-based extractor for FastAPI routers, endpoints, and RBAC hints
# Python 3.11

from __future__ import annotations
import ast
import json
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "app" / "api" / "v1"
MAIN_FILE = ROOT / "app" / "main.py"

@dataclass
class Endpoint:
    method: str
    path: str
    file: str
    name: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    request_model: Optional[str] = None
    response_model: Optional[str] = None

@dataclass
class Extraction:
    base_paths: List[str]
    endpoints: List[Endpoint]

ROLE_HINTS = {
    "admin_required": ["admin"],
    "responsable_required": ["responsable"],
    "technicien_required": ["technicien"],
    "client_required": ["client"],
    # Custom wrappers/aliases used in routers
    "allowed_planning_roles": ["admin", "responsable"],
    "auth_required": ["admin", "responsable", "technicien", "client"],
}

ROUTER_METHODS = {"get", "post", "put", "patch", "delete"}

class RouterVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.router_names: set[str] = set()
        self.router_prefix: dict[str, str] = {}
        self.endpoints: List[Endpoint] = []
        super().__init__()

    def visit_Assign(self, node: ast.Assign):
        # Detect APIRouter() names
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "APIRouter":
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.router_names.add(t.id)
                    # read prefix kwarg if present
                    prefix = ""
                    for kw in node.value.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            prefix = kw.value.value or ""
                    self.router_prefix[t.id] = prefix
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Keep generic traversal; endpoint detection handled in visit_FunctionDef
        self.generic_visit(node)

    def _extract_dep_roles_from_depends(self, call: ast.Call) -> tuple[list[str], list[str]]:
        """Given a Depends(...) call, return (dependencies, roles) extracted."""
        deps: list[str] = []
        roles: list[str] = []
        if isinstance(call.func, ast.Name) and call.func.id == "Depends" and call.args:
            dep = call.args[0]
            if isinstance(dep, ast.Name):
                deps.append(dep.id)
                roles.extend(ROLE_HINTS.get(dep.id, []))
            elif isinstance(dep, ast.Call) and isinstance(dep.func, ast.Name):
                # e.g., Depends(require_roles("admin", "responsable"))
                if dep.func.id == "require_roles":
                    for a in dep.args:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str):
                            roles.append(a.value)
        return deps, roles

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect FastAPI endpoints via decorators and collect roles from both decorator dependencies and parameter-level Depends()."""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ROUTER_METHODS and isinstance(dec.func.value, ast.Name) and dec.func.value.id in self.router_names:
                method = dec.func.attr.upper()
                path = None
                response_model = None
                dependencies: list[str] = []
                roles: list[str] = []

                # Positional args: first string starting with '/'
                for arg in dec.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("/"):
                        path = arg.value
                        break

                # Keyword args in decorator
                for kw in dec.keywords:
                    if kw.arg == "response_model" and isinstance(kw.value, ast.Name):
                        response_model = kw.value.id
                    if kw.arg == "dependencies" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Call):
                                deps, r = self._extract_dep_roles_from_depends(elt)
                                dependencies.extend(deps)
                                roles.extend(r)

                # Parameter-level dependencies (defaults)
                # positional defaults map to the last N args
                for d in (node.args.defaults or []):
                    if isinstance(d, ast.Call):
                        deps, r = self._extract_dep_roles_from_depends(d)
                        dependencies.extend(deps)
                        roles.extend(r)
                # keyword-only defaults
                for d in (node.args.kw_defaults or []):
                    if isinstance(d, ast.Call):
                        deps, r = self._extract_dep_roles_from_depends(d)
                        dependencies.extend(deps)
                        roles.extend(r)

                if path:
                    rname = dec.func.value.id
                    prefix = self.router_prefix.get(rname, "")
                    full_path = f"{prefix.rstrip('/')}{path}" if prefix else path
                    if not full_path.startswith("/"):
                        full_path = "/" + full_path
                    self.endpoints.append(
                        Endpoint(
                            method=method,
                            path=full_path,
                            file=str(self.filename),
                            name=node.name,
                            response_model=response_model,
                            dependencies=sorted(set(dependencies)),
                            roles=sorted(set(roles)),
                        )
                    )
        self.generic_visit(node)


def extract_api_endpoints() -> List[Endpoint]:
    endpoints: List[Endpoint] = []
    for py in API_DIR.glob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except Exception:
            continue
        rv = RouterVisitor(str(py.relative_to(ROOT)))
        rv.visit(tree)
        endpoints.extend(rv.endpoints)
    return endpoints


def detect_base_paths() -> List[str]:
    base_paths = ["/api/v1"]
    try:
        # Check if routers also included without prefix in main
        text = MAIN_FILE.read_text(encoding="utf-8")
        if "app.include_router(auth.router)" in text or "app.include_router(users.router)" in text or "app.include_router(techniciens.router)" in text:
            base_paths.append("/")
    except Exception:
        pass
    return sorted(set(base_paths))


def main():
    endpoints = extract_api_endpoints()
    data = Extraction(base_paths=detect_base_paths(), endpoints=endpoints)
    print(json.dumps({
        "base_paths": data.base_paths,
        "endpoints": [asdict(e) for e in data.endpoints]
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
