# ============================================
# Git Remote Conversion Tool
# Modes:
# 1 = Convert all to HTTPS
# 2 = Convert all to SSH
# 3 = Flip each (HTTPS<->SSH)
# ============================================

$root = "A:\dev"
$log  = Join-Path $PWD "repo-remote-tool.log"

"=== Git Remote Tool Log $(Get-Date) ===`n" | Out-File $log -Encoding utf8

Write-Host "Select mode:" -ForegroundColor Cyan
Write-Host "1. Convert ALL to HTTPS"
Write-Host "2. Convert ALL to SSH"
Write-Host "3. Flip each (HTTPS <-> SSH)"
$mode = Read-Host "Enter mode number"

if ($mode -notin "1","2","3") {
    Write-Host "Invalid selection. Exiting." -ForegroundColor Red
    exit
}

Get-ChildItem -Path $root -Directory | ForEach-Object {
    $repo = $_.FullName
    if (-not (Test-Path "$repo\.git")) { return }

    Write-Host "`nChecking repo: $repo" -ForegroundColor Cyan
    Add-Content $log "`nRepo: $repo"

    $remote = git -C $repo remote get-url origin 2>$null

    if (-not $remote) {
        Write-Host "  No origin remote found." -ForegroundColor DarkGray
        Add-Content $log "  No origin remote."
        return
    }

    Add-Content $log "  Current: $remote"

    $isHttps = $remote.StartsWith("https://github.com/")
    $isSsh   = $remote.StartsWith("git@github.com:")

    switch ($mode) {

        # MODE 1: all → HTTPS
        "1" {
            if ($isHttps) {
                Write-Host "  Already HTTPS." -ForegroundColor DarkGray
                Add-Content $log "  Already HTTPS."
                return
            }

            if ($isSsh) {
                $clean = $remote -replace "^git@github.com:", "" -replace "\.git/?$", ""
                $new = "https://github.com/$clean.git"

                Write-Host "  SSH → HTTPS: $new" -ForegroundColor Green
                Add-Content $log "  SSH → HTTPS: $new"

                git -C $repo remote set-url origin $new
                return
            }

            Write-Host "  Unsupported remote format." -ForegroundColor Yellow
            Add-Content $log "  Unsupported format."
        }

        # MODE 2: all → SSH
        "2" {
            if ($isSsh) {
                Write-Host "  Already SSH." -ForegroundColor DarkGray
                Add-Content $log "  Already SSH."
                return
            }

            if ($isHttps) {
                $clean = $remote -replace "^https://github.com/", "" -replace "\.git/?$", ""
                $new = "git@github.com:$clean.git"

                Write-Host "  HTTPS → SSH: $new" -ForegroundColor Green
                Add-Content $log "  HTTPS → SSH: $new"

                git -C $repo remote set-url origin $new
                return
            }

            Write-Host "  Unsupported remote format." -ForegroundColor Yellow
            Add-Content $log "  Unsupported format."
        }

        # MODE 3: Flip each remote
        "3" {
            if ($isHttps) {
                $clean = $remote -replace "^https://github.com/", "" -replace "\.git/?$", ""
                $new = "git@github.com:$clean.git"

                Write-Host "  FLIP: HTTPS → SSH: $new" -ForegroundColor Green
                Add-Content $log "  FLIP: HTTPS → SSH: $new"

                git -C $repo remote set-url origin $new
                return
            }

            if ($isSsh) {
                $clean = $remote -replace "^git@github.com:", "" -replace "\.git/?$", ""
                $new = "https://github.com/$clean.git"

                Write-Host "  FLIP: SSH → HTTPS: $new" -ForegroundColor Green
                Add-Content $log "  FLIP: SSH → HTTPS: $new"

                git -C $repo remote set-url origin $new
                return
            }

            Write-Host "  Unsupported remote format." -ForegroundColor Yellow
            Add-Content $log "  Unsupported format."
        }
    }
}

Write-Host "`nDone. Log saved to: $log" -ForegroundColor Cyan
