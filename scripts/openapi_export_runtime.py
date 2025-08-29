#!/usr/bin/env python3
"""
Exporte le schéma OpenAPI en important l'app FastAPI (runtime),
et écrit le résultat dans openapi.json à la racine du projet.
Utilise un encodage UTF-8 et ne force pas l'ASCII.
"""
import json
import os
import sys

# Garantir un env minimal pour l'initialisation de l'app
os.environ.setdefault("ENV", os.getenv("ENV", "test"))
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///:memory:"))

# Assurer que la racine du projet est dans sys.path pour pouvoir importer 'app'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import après configuration de l'env
from app.main import app  # noqa: E402

# Assurer l'UTF-8 sur stdout si besoin (Python 3.7+)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

openapi = app.openapi()
output_path = os.path.join(os.path.dirname(__file__), "..", "openapi.json")
output_path = os.path.abspath(output_path)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(openapi, f, ensure_ascii=False, indent=2)

print(f"OpenAPI exporté -> {output_path}")
