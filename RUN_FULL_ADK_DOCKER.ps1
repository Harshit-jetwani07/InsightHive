$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is not installed or not available on PATH."
}

if (-not (Test-Path -LiteralPath ".env.docker")) {
    Copy-Item -LiteralPath ".env.docker.example" -Destination ".env.docker"
    Write-Host "Created .env.docker. Add your Gemini key and admin password, then run this script again." -ForegroundColor Yellow
    exit 1
}

$envText = Get-Content -LiteralPath ".env.docker" -Raw
if ($envText -match "replace_with_") {
    throw "Replace placeholder values inside .env.docker before starting Full ADK mode."
}

docker compose up --build
