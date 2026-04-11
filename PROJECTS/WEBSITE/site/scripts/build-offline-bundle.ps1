param(
  [string]$Tag = "latest",
  [string]$OutputDir = ".\\dist\\offline-bundle"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$bundleDir = Join-Path $root $OutputDir
$imagesDir = Join-Path $bundleDir "images"

New-Item -ItemType Directory -Force -Path $imagesDir | Out-Null

$apiImage = "website-api-offline:$Tag"
$webImage = "website-web-offline:$Tag"
$envExamplePath = Join-Path $bundleDir ".env.example"

Write-Host "[offline] Building API image $apiImage"
docker build -t $apiImage (Join-Path $root "backend")

Write-Host "[offline] Building WEB image $webImage"
docker build -t $webImage (Join-Path $root "frontend")

Write-Host "[offline] Saving images"
docker save -o (Join-Path $imagesDir "website-api-offline_$Tag.tar") $apiImage
docker save -o (Join-Path $imagesDir "website-web-offline_$Tag.tar") $webImage
docker pull postgres:16-alpine | Out-Null
docker save -o (Join-Path $imagesDir "postgres_16-alpine.tar") postgres:16-alpine

Copy-Item (Join-Path $root "docker-compose.offline.yml") (Join-Path $bundleDir "docker-compose.yml") -Force
Copy-Item (Join-Path $PSScriptRoot "server-load-offline-images.sh") (Join-Path $bundleDir "server-load-offline-images.sh") -Force

$envContent = @"
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=prompts_vault
JWT_SECRET_KEY=change-me-in-production

DB_PORT=5432
API_PORT=8000
WEB_PORT=3000

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000

WEBSITE_API_IMAGE=$apiImage
WEBSITE_WEB_IMAGE=$webImage
"@

Set-Content -Path $envExamplePath -Value $envContent -NoNewline

Write-Host "[offline] Bundle ready at $bundleDir"
