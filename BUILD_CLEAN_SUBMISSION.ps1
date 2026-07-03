$ErrorActionPreference = "Stop"

$root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$dist = Join-Path $root "dist"
$stage = Join-Path $dist "InsightHive"
$zip = Join-Path $dist "insight-hive-capstone-clean.zip"

if (-not $stage.StartsWith($root) -or -not $zip.StartsWith($root)) {
    throw "Submission paths resolved outside the project."
}

if (Test-Path -LiteralPath $stage) {
    Remove-Item -LiteralPath $stage -Recurse -Force
}
if (Test-Path -LiteralPath $zip) {
    Remove-Item -LiteralPath $zip -Force
}
New-Item -ItemType Directory -Path $stage -Force | Out-Null

$directories = @(
    "agents", "tools", "services", "utils", "pages", "tests", "rag",
    "mcp_server", "evaluation", "submission", "submission_assets", "docs",
    ".streamlit", ".github", "assets", "data", "uploads", "reports", "exports"
)
$files = @(
    "app.py", "Dockerfile", "compose.yaml", "cloudbuild.yaml",
    "requirements.txt", "requirements-dev.txt", ".python-version", ".env.example",
    ".env.docker.example", ".dockerignore", ".gitignore", ".gitattributes",
    "README.md", "DEPLOYMENT.md", "GITHUB_PUSH_CHECKLIST.md",
    "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "CITATION.cff",
    "RUN_FULL_ADK_DOCKER.ps1",
    "BUILD_CLEAN_SUBMISSION.ps1", "LICENSE"
)

foreach ($name in $directories) {
    $source = Join-Path $root $name
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination $stage -Recurse -Force
    }
}
foreach ($name in $files) {
    $source = Join-Path $root $name
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination $stage -Force
    }
}

Get-ChildItem -LiteralPath $stage -Recurse -Force |
    Where-Object {
        $_.Name -eq "__pycache__" -or
        $_.Extension -in @(".pyc", ".pyo") -or
        $_.Name -in @(".env", ".env.docker", "secrets.toml") -or
        $_.Extension -in @(".db", ".sqlite", ".sqlite3") -or
        (
            $_.FullName -match "[\\/](uploads|reports|exports|data)[\\/]" -and
            $_.Name -ne ".gitkeep"
        )
    } |
    Sort-Object FullName -Descending |
    Remove-Item -Recurse -Force

$forbidden = Get-ChildItem -LiteralPath $stage -Recurse -Force |
    Where-Object {
        (
            $_.FullName -match "[\\/](\.git|\.venv|venv)([\\/]|$)" -or
            (
                $_.FullName -match "[\\/](uploads|reports|exports|data)([\\/]|$)" -and
                -not $_.PSIsContainer -and
                $_.Name -ne ".gitkeep"
            )
        ) -or
        $_.Name -in @(".env", ".env.docker", "secrets.toml") -or
        $_.Extension -in @(".db", ".sqlite", ".sqlite3", ".pyc")
    }
if ($forbidden) {
    throw "Forbidden runtime/private files remain in the staging directory."
}

$manifest = Get-ChildItem -LiteralPath $stage -Recurse -File |
    ForEach-Object {
        $relative = $_.FullName.Substring($stage.Length + 1).Replace("\", "/")
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
        "$hash  $relative"
    }
$manifest | Set-Content -LiteralPath (Join-Path $stage "SHA256SUMS.txt") -Encoding utf8

Compress-Archive -LiteralPath $stage -DestinationPath $zip -CompressionLevel Optimal
$count = (Get-ChildItem -LiteralPath $stage -Recurse -File).Count
$sizeMb = [math]::Round((Get-Item -LiteralPath $zip).Length / 1MB, 2)

Write-Host "Clean submission created: $zip" -ForegroundColor Green
Write-Host "Files: $count | ZIP size: $sizeMb MB"
