# API Contract & Robustness

## OpenAPI Validation

Command: curl /openapi.json

Output: Not run (backend not running)

## Schemathesis Test

Command: schemathesis run openapi.json --base-url=http://localhost:8000

Output: Not run (backend not running)

## Controls

- Pagination, tri stable, filtres whitelist: To be verified
- Erreurs JSON propres: To be verified

## Criteria

- 0 crash property-based: To be verified
- Codes HTTP corrects: To be verified

## Artifacts

- openapi.json: Exists
- This report
