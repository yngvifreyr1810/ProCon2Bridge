$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + [IO.Path]::PathSeparator + $env:PSModulePath
$taskRoot = Split-Path -Parent $PSScriptRoot
$installer = Join-Path $taskRoot 'drivers\USBip-0.9.8.1-x64.exe'
$expected = '38CAD6D4432B52D5BB9409D9AD03B72FDFFC4ADA4CD3A48FBECA1A2752A8518A'
if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $expected) {
    throw 'USB/IP installer hash mismatch. Nothing installed.'
}
$signature = Get-AuthenticodeSignature -LiteralPath $installer
if ($signature.Status -ne 'Valid') { throw 'USB/IP installer signature invalid. Nothing installed.' }
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    $process = Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"')) -Wait -PassThru
    exit $process.ExitCode
}
$log = Join-Path $taskRoot 'driver-install.log'
$process = Start-Process -FilePath $installer -WindowStyle Hidden -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="'+$log+'"')) -Wait -PassThru
$result = @{exit_code=$process.ExitCode;installed_at=(Get-Date -Format o);installer_sha256=$expected;signer=$signature.SignerCertificate.Subject;exe_present=(Test-Path 'C:\Program Files\USBip\usbip.exe');driver_present=(Test-Path 'HKLM:\SYSTEM\CurrentControlSet\Services\usbip2_ude')}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'driver-install-result.json') -Encoding UTF8
if ($process.ExitCode -notin @(0,3010)) { throw "USB/IP installation failed: $($process.ExitCode). See driver-install.log." }
if (-not $result.exe_present -or -not $result.driver_present) { throw 'USB/IP installation incomplete. See driver-install.log.' }
Write-Host 'USB/IP installed. Run START.cmd. If Windows requests a reboot, reboot first.'
