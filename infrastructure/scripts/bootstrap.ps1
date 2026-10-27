param([switch]$Start)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.env')) {
    $template = Get-Content -LiteralPath '.env.example' -Raw
    $databasePassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24)).ToLowerInvariant()
    $storagePassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24)).ToLowerInvariant()
    $template = $template.Replace('POSTGRES_PASSWORD=', "POSTGRES_PASSWORD=$databasePassword")
    $template = $template.Replace('MINIO_ROOT_PASSWORD=', "MINIO_ROOT_PASSWORD=$storagePassword")
    [IO.File]::WriteAllText((Join-Path $projectRoot '.env'), $template)
    Write-Host 'Created local configuration with random credentials.'
} else {
    Write-Host 'Existing local configuration preserved.'
}
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Compose configuration is invalid.' }
if ($Start) {
    docker compose up --build -d
    if ($LASTEXITCODE -ne 0) { throw 'Compose startup failed.' }
}
Write-Host 'Open http://localhost:5180 after the web service is healthy.'
