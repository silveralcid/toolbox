param(
    [string]$Root
)

# If no path provided, use current directory
if (-not $Root) {
    $Root = (Get-Location).Path
    Write-Host "No path provided. Using current directory: $Root"
} else {
    Write-Host "Using path: $Root"
}

Get-ChildItem -Path $Root -Directory -Recurse | ForEach-Object {
    $folder = $_.FullName

    # Count subfolders
    $subdirs = (Get-ChildItem -Path $folder -Directory).Count

    # Count files
    $files = (Get-ChildItem -Path $folder -File).Count

    # Only add .gitkeep if folder is empty
    if ($subdirs -eq 0 -and $files -eq 0) {
        $gitkeep = Join-Path $folder ".gitkeep"
        if (-not (Test-Path $gitkeep)) {
            New-Item -ItemType File -Path $gitkeep | Out-Null
            Write-Host "Created: $gitkeep"
        }
    }
}
