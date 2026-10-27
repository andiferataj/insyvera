param([string]$Destination = '.local\backups')
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location -LiteralPath $projectRoot
$backupRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot $Destination))
if (-not $backupRoot.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Choose a backup directory inside this project.' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$target = Join-Path $backupRoot $stamp
New-Item -ItemType Directory -Path $target -Force | Out-Null
docker compose stop worker api web
if ($LASTEXITCODE -ne 0) { throw 'Could not quiesce application services.' }
try {
    docker compose exec -T postgres pg_dump -U insyvera -Fc -f /tmp/insyvera-backup.dump insyvera
    if ($LASTEXITCODE -ne 0) { throw 'Database backup failed.' }
    docker compose cp postgres:/tmp/insyvera-backup.dump (Join-Path $target 'database.dump')
    if ($LASTEXITCODE -ne 0) { throw 'Could not copy database backup.' }
    docker compose run --rm --no-deps --entrypoint python api infrastructure/scripts/volume_archive.py backup /app/data/checkpoints /app/data/checkpoints.tar
    if ($LASTEXITCODE -ne 0) { throw 'Checkpoint archive failed.' }
    docker compose cp api:/app/data/checkpoints.tar (Join-Path $target 'checkpoints.tar')
    docker compose cp minio:/data (Join-Path $target 'objects')
    if ($LASTEXITCODE -ne 0) { throw 'Object-store backup failed.' }
    Write-Host "Backup written to $target. Keep a separate secure copy of .env."
} finally {
    docker compose start api worker web
}
