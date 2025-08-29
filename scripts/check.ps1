$ErrorActionPreference = "Stop"

Copy-Item .env.example .env -ErrorAction Ignore

# Start only the database for migrations
docker compose up -d db
$cid = (docker compose ps -q db)
Write-Host "⏳ wait db..."
for ($i=0; $i -lt 120; $i++) {
  if ((docker inspect -f '{{.State.Health.Status}}' $cid) -eq 'healthy') { break }
  Start-Sleep -Seconds 1
}
if ((docker inspect -f '{{.State.Health.Status}}' $cid) -ne 'healthy') { throw "DB not healthy" }

python -m alembic upgrade head

# lint/format/type (optional if already configured)
black --check app/ 2>$null
isort --check-only app/ 2>$null
flake8 app/ --max-line-length 88 --extend-ignore E203,W503 2>$null

pytest

python validate_contract.py --output validation_result.json
python openapi_export.py > openapi.json

# smoke API
$env:UVICORN_LOG_LEVEL="warning"
$api = Start-Process -FilePath python -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000" -PassThru
Start-Sleep -Seconds 2
try {
  $r = Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
  if ($r.StatusCode -ne 200) { throw "Health failed" }
} finally {
  Stop-Process -Id $api.Id -Force
}
Write-Host "✅ all checks passed"
