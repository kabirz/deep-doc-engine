param(
    [Parameter(Mandatory=$true)][string]$InFile,
    [Parameter(Mandatory=$true)][string]$OutFile
)
# ASCII-only: PowerShell 5.1 reads BOM-less scripts as ANSI.
$ErrorActionPreference = "Stop"
$cands = @(
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
)
$edge = $cands | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Error "Edge not found"; exit 2 }
if (Test-Path $OutFile) { Remove-Item $OutFile -Force }
$uri = ([System.Uri]((Resolve-Path $InFile).Path)).AbsoluteUri
$args = @("--headless", "--disable-gpu", "--no-pdf-header-footer", "--disable-extensions",
          "--print-to-pdf=$OutFile", $uri)
$p = Start-Process -FilePath $edge -ArgumentList $args -PassThru -WindowStyle Hidden
$deadline = (Get-Date).AddSeconds(300)
while (-not (Test-Path $OutFile) -and -not $p.HasExited -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 700 }
if (-not $p.HasExited) { try { $p.WaitForExit(180000) | Out-Null } catch {} }
if (-not (Test-Path $OutFile)) { Write-Error "PDF not generated"; exit 3 }
$size = (Get-Item $OutFile).Length
Write-Output ("OK {0} ({1} bytes)" -f $OutFile, $size)
