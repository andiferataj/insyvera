param([switch]$Browser, [switch]$Infrastructure)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')))
& .\.venv\Scripts\python.exe -m ruff check apps/api tests
if ($LASTEXITCODE -ne 0) { throw 'Python lint failed.' }
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
if ($Browser) {
    npm run test:e2e
    if ($LASTEXITCODE -ne 0) { throw 'Browser tests failed.' }
}
if ($Infrastructure) {
    docker compose exec api python infrastructure/scripts/check_infrastructure.py
    if ($LASTEXITCODE -ne 0) { throw 'Infrastructure checks failed.' }
}
