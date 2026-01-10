param(
    [switch]$Verify,
    [string]$Source = "AGENTS.md"
)

$targets = @("AGENTS.md", "CLAUDE.md", "GEMINI.md")
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$sourcePath = if ([IO.Path]::IsPathRooted($Source)) { $Source } else { Join-Path $repoRoot $Source }

if (-not (Test-Path -LiteralPath $sourcePath)) {
    Write-Error "Source file not found: $sourcePath"
    exit 1
}

$sourcePath = (Resolve-Path -LiteralPath $sourcePath).Path
$sourceName = [IO.Path]::GetFileName($sourcePath)

if ($targets -notcontains $sourceName) {
    Write-Error "Source must be one of: $($targets -join ', ')"
    exit 1
}

$targetPaths = $targets | ForEach-Object { Join-Path $repoRoot $_ }

if ($Verify) {
    $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash
    $missing = @()
    $mismatch = @()

    foreach ($path in $targetPaths) {
        if (-not (Test-Path -LiteralPath $path)) {
            $missing += $path
            continue
        }
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
        if ($hash -ne $sourceHash) {
            $mismatch += $path
        }
    }

    if ($missing.Count -gt 0 -or $mismatch.Count -gt 0) {
        if ($missing.Count -gt 0) {
            Write-Error ("Missing agent files: " + ($missing -join ", "))
        }
        if ($mismatch.Count -gt 0) {
            Write-Error ("Out of sync: " + ($mismatch -join ", "))
        }
        Write-Error "Run scripts/sync_agents.ps1 to sync from the source file."
        exit 1
    }

    Write-Host "Agent files are in sync."
    exit 0
}

foreach ($path in $targetPaths) {
    if ($path -ne $sourcePath) {
        Copy-Item -LiteralPath $sourcePath -Destination $path -Force
    }
}

Write-Host "Synced agent files from $sourceName."
