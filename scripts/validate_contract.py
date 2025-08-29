#!/usr/bin/env python3
"""
Validate that the frontend_contract.json matches the actual FastAPI endpoints
detected via scripts/ast_extract.py.

- Normalizes path parameter names (e.g., {id} vs {user_id}).
- Treats unknown detected roles as warnings.
- Fails on missing endpoints, extra endpoints, or concrete role differences.
"""

from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DEFAULT = ROOT / "frontend_contract.json"
AST_EXTRACT = ROOT / "scripts" / "ast_extract.py"


def load_contract(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_ast_extract() -> dict:
    out = subprocess.check_output([sys.executable, str(AST_EXTRACT)], cwd=str(ROOT))
    return json.loads(out.decode("utf-8"))


_PARAM_RE = re.compile(r"\{[^}]+\}")


def canonicalize_path(path: str) -> str:
    # Replace any {param_name} with {param}
    p = _PARAM_RE.sub("{param}", path)
    # Uniform trailing slash handling
    if p != "/":
        p = p.rstrip("/")
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=str(CONTRACT_DEFAULT))
    parser.add_argument("--output", help="Write JSON result also to this file")
    args = parser.parse_args()

    contract = load_contract(Path(args.contract))
    detected = run_ast_extract()

    contract_eps_raw = [(e["method"].upper(), e["path"]) for e in contract.get("endpoints", [])]
    detected_eps_raw = [(e["method"].upper(), e["path"]) for e in detected.get("endpoints", [])]

    contract_eps = {(m, canonicalize_path(p)) for (m, p) in contract_eps_raw}
    detected_eps = {(m, canonicalize_path(p)) for (m, p) in detected_eps_raw}

    missing = sorted(list(contract_eps - detected_eps))
    extra = sorted(list(detected_eps - contract_eps))

    # Ignore extras declared in contract (internal endpoints not required by FE)
    ignore_cfg = contract.get("ignoreExtras", []) or []
    ignore_set = {
        (item.get("method", "").upper(), canonicalize_path(item.get("path", "")))
        for item in ignore_cfg
        if isinstance(item, dict) and item.get("method") and item.get("path")
    }
    extra_filtered = [e for e in extra if (e[0], e[1]) not in ignore_set]

    # Role diffs: compare only where both sides define roles
    role_diffs = []
    role_unknown = []
    detected_by_key = { (e["method"].upper(), canonicalize_path(e["path"])): e for e in detected.get("endpoints", []) }
    for e in contract.get("endpoints", []):
        key = (e["method"].upper(), canonicalize_path(e["path"]))
        det = detected_by_key.get(key)
        if not det:
            continue
        exp_roles = sorted((e.get("auth", {}) or {}).get("roles", []) or e.get("roles", []))
        det_roles = sorted(det.get("roles", []))
        if exp_roles and det_roles:
            if exp_roles != det_roles:
                role_diffs.append({"method": key[0], "path": key[1], "expected_roles": exp_roles, "detected_roles": det_roles})
        elif exp_roles and not det_roles:
            role_unknown.append({"method": key[0], "path": key[1], "expected_roles": exp_roles, "detected_roles": []})

    result = {
        "missing_endpoints": [{"method": m, "path": p} for (m, p) in missing],
        "extra_endpoints": [{"method": m, "path": p} for (m, p) in extra_filtered],
        "role_differences": role_diffs,
        "role_unknown": role_unknown,
        "detected_base_paths": detected.get("base_paths", []),
    }

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_json)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")

    if missing or extra_filtered or role_diffs:
        print("Contract validation FAILED", file=sys.stderr)
        sys.exit(1)
    else:
        print("Contract validation OK")


if __name__ == "__main__":
    main()
