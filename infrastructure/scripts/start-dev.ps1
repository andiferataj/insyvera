param([switch]$Install)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 or 3.13 and ensure python is on PATH.' }
}
if ($Install) {
    & .\.venv\Scripts\python.exe -m pip install -r requirements.lock
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency restore failed.' }
    & .\.venv\Scripts\python.exe -m pip install -e . --no-deps
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Root npm restore failed.' }
    npm --prefix apps/web ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend restore failed.' }
}
if (-not (Test-Path -LiteralPath '.local')) { New-Item -ItemType Directory -Path '.local' | Out-Null }
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$apiProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8100') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput '.local\api.log' -RedirectStandardError '.local\api-error.log' -PassThru
$webDirectory = Join-Path $projectRoot 'apps\web'
$webProcess = Start-Process -FilePath 'node' -ArgumentList @('node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '5180') -WorkingDirectory $webDirectory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.local\web.log') -RedirectStandardError (Join-Path $projectRoot '.local\web-error.log') -PassThru
@{ api = $apiProcess.Id; web = $webProcess.Id; root = $projectRoot } | ConvertTo-Json | Set-Content -LiteralPath '.local\dev-processes.json'
Write-Host 'Local development: http://127.0.0.1:5180'
Write-Host 'This mode uses SQLite, local objects, background tasks and extractive retrieval. Docker enables PostgreSQL, Redis, MinIO and Celery.'
