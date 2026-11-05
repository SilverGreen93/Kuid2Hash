#Requires -Version 7.0
<#
.SYNOPSIS
  Builds the Kuid2Hash MSI installer.

.DESCRIPTION
  Packages the PyInstaller one-file exes (dist\Kuid2Hash.exe and
  dist\Kuid2HashCli.exe) into a per-user MSI with WiX v5. Build the exes
  first (python build.py --only exe). Requires the WiX command-line tool:

    dotnet tool install --global wix
    wix extension add -g WixToolset.UI.wixext
#>
param(
    # Override the version baked into the MSI (default: pyproject.toml).
    [string]$Version
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $root 'dist'

if (-not $Version) {
    $match = Select-String -Path (Join-Path $root 'pyproject.toml') -Pattern '^version = "([^"]+)"' | Select-Object -First 1
    if (-not $match) { throw 'Could not read the version from pyproject.toml.' }
    $Version = $match.Matches[0].Groups[1].Value
}

# The MSI uses the same two-part Major.Minor version as the app VERSION;
# a leading 'v' (release tags) is accepted and dropped.
$Version = ($Version.TrimStart('v') -split '\.')[0..1] -join '.'

foreach ($exe in 'Kuid2Hash.exe', 'Kuid2HashCli.exe') {
    if (-not (Test-Path (Join-Path $distDir $exe))) {
        throw "$exe not found in dist\ - build the exes first: python build.py --only exe"
    }
}

$msi = Join-Path $distDir "Kuid2Hash-$Version.msi"
Remove-Item $msi -Force -ErrorAction SilentlyContinue

Write-Output "Building $msi ..."
wix build (Join-Path $PSScriptRoot 'Product.wxs') `
    -ext WixToolset.UI.wixext `
    -d "Version=$Version" `
    -d "DistDir=$distDir" `
    -d "AssetsDir=$(Join-Path $root 'assets')" `
    -o $msi
if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Output ("Done: {0} ({1:N1} MB)" -f $msi, ((Get-Item $msi).Length / 1MB))
