[CmdletBinding()]
param(
    [Parameter()]
    [string]$DestinationPath,

    [Parameter()]
    [string]$TestStatus = "Not provided",

    [Parameter()]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Arguments)

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git $($Arguments -join ' ')`n$output"
    }
    return @($output)
}

try {
    $repositoryRoot = (Resolve-Path -LiteralPath (Get-Location)).Path
    $gitTopLevel = (Invoke-Git -Arguments @("rev-parse", "--show-toplevel") |
        Select-Object -First 1).Trim()
    $resolvedGitTopLevel = (Resolve-Path -LiteralPath $gitTopLevel).Path

    if ($repositoryRoot -ne $resolvedGitTopLevel) {
        throw "Run this script from the repository root: $resolvedGitTopLevel"
    }

    if ([string]::IsNullOrWhiteSpace($DestinationPath)) {
        $DestinationPath = Join-Path (Split-Path -Parent $repositoryRoot) "LUXIOM_BACKUPS"
    }

    $fullDestination = [System.IO.Path]::GetFullPath($DestinationPath)
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDirectory = Join-Path $fullDestination "LUXIOM_$timestamp"
    $bundlePath = Join-Path $backupDirectory "luxiom-repository.bundle"
    $snapshotPath = Join-Path $backupDirectory "luxiom-source.zip"
    $manifestPath = Join-Path $backupDirectory "MANIFEST.txt"

    $branch = (Invoke-Git -Arguments @("branch", "--show-current") |
        Select-Object -First 1)
    $commit = (Invoke-Git -Arguments @("rev-parse", "HEAD") |
        Select-Object -First 1)
    $tags = @(Invoke-Git -Arguments @("tag", "--points-at", "HEAD"))
    $status = @(Invoke-Git -Arguments @("status", "--short", "--branch"))
    $dirtyStatus = @(Invoke-Git -Arguments @("status", "--porcelain"))
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        $pythonVersion = "Python not available on PATH"
    }

    Write-Host "Repository: $repositoryRoot"
    Write-Host "Backup directory: $backupDirectory"
    Write-Host "Git bundle: $bundlePath"
    Write-Host "Source snapshot: $snapshotPath"
    Write-Host "Manifest: $manifestPath"
    Write-Host "Snapshot exclusions: .git, virtual environments, caches, backups,"
    Write-Host "  .env variants, credentials/keys/certificates, logs, and temp artifacts."

    if (@($dirtyStatus).Count -gt 0) {
        Write-Warning "The working tree has uncommitted changes. The Git bundle only contains committed history; the source snapshot will include non-secret working files."
    }

    if ($DryRun) {
        Write-Host "DryRun: no directories, bundle, snapshot, or manifest were created."
        exit 0
    }

    New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
    Invoke-Git -Arguments @("bundle", "create", $bundlePath, "--all") | Out-Null

    $destinationPrefix = $fullDestination.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar

    $excludedDirectoryNames = @(
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        ".ruff_cache", ".mypy_cache", ".tox", ".nox", "node_modules",
        "dist", "build", "htmlcov", "LUXIOM_BACKUPS"
    )
    $excludedExtensions = @(
        ".pyc", ".pyo", ".log", ".tmp", ".temp", ".swp", ".bak",
        ".key", ".pem", ".pfx", ".p12", ".jks", ".keystore"
    )
    $secretNamePattern = '(?i)(credential|credentials|secret|secrets|token|private[_-]?key)'

    $snapshotFiles = @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force |
        Where-Object {
            $file = $_
            $relativePath = $file.FullName.Substring($repositoryRoot.Length).TrimStart(
                [System.IO.Path]::DirectorySeparatorChar,
                [System.IO.Path]::AltDirectorySeparatorChar
            )
            $segments = $relativePath -split '[\\/]'
            $isInsideDestination = $file.FullName.StartsWith(
                $destinationPrefix,
                [System.StringComparison]::OrdinalIgnoreCase
            )
            $isExcludedDirectory = @($segments | Where-Object {
                $excludedDirectoryNames -contains $_
            }).Count -gt 0
            $isEnvFile = $file.Name -eq ".env" -or $file.Name -like ".env.*"
            $isSecretName = $file.Name -match $secretNamePattern
            $isExcludedExtension = $excludedExtensions -contains $file.Extension.ToLowerInvariant()

            -not (
                $isInsideDestination -or
                $isExcludedDirectory -or
                $isEnvFile -or
                $isSecretName -or
                $isExcludedExtension
            )
        })

    if (@($snapshotFiles).Count -eq 0) {
        throw "No safe files were found for the source snapshot."
    }

    $stagingDirectory = Join-Path $backupDirectory ".snapshot-staging"
    New-Item -ItemType Directory -Path $stagingDirectory | Out-Null
    try {
        foreach ($file in $snapshotFiles) {
            $relativePath = $file.FullName.Substring($repositoryRoot.Length).TrimStart(
                [System.IO.Path]::DirectorySeparatorChar,
                [System.IO.Path]::AltDirectorySeparatorChar
            )
            $targetPath = Join-Path $stagingDirectory $relativePath
            $targetParent = Split-Path -Parent $targetPath
            New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $targetPath
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            $stagingDirectory,
            $snapshotPath,
            [System.IO.Compression.CompressionLevel]::Optimal,
            $false
        )
    }
    finally {
        if (Test-Path -LiteralPath $stagingDirectory) {
            Remove-Item -LiteralPath $stagingDirectory -Recurse -Force
        }
    }

    $tagText = if (@($tags).Count -gt 0) { $tags -join ", " } else { "None at HEAD" }
    $manifestLines = @(
        "LUXIOM PORTABLE BACKUP MANIFEST",
        "Generated: $((Get-Date).ToString('o'))",
        "Repository: $repositoryRoot",
        "Branch: $branch",
        "Commit: $commit",
        "Tags at HEAD: $tagText",
        "Python: $pythonVersion",
        "Tests: $TestStatus",
        "",
        "GIT STATUS",
        "----------"
    ) + $status
    Set-Content -LiteralPath $manifestPath -Value $manifestLines -Encoding UTF8

    Write-Host "Backup completed successfully."
    Write-Host "Verify with: git bundle verify `"$bundlePath`""
}
catch {
    Write-Error "Luxiom backup failed: $($_.Exception.Message)"
    exit 1
}
