$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + [IO.Path]::PathSeparator + $env:PSModulePath
function Add-ProCon2BridgeStartupEntry {
    $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    if (-not (Test-Path -LiteralPath $runKey)) { New-Item -Path $runKey -Force | Out-Null }
    $command = '"' + (Join-Path $PSScriptRoot 'ProCon2Bridge.exe') + '"'
    New-ItemProperty -LiteralPath $runKey -Name 'ProCon2Bridge' -Value $command -PropertyType String -Force | Out-Null
}

try {
    Set-Location -LiteralPath $PSScriptRoot
    $taskProbe = [Net.Sockets.TcpClient]::new()
    try {
        $taskConnect = $taskProbe.ConnectAsync('127.0.0.1',26759)
        if ($taskConnect.Wait(300) -and $taskProbe.Connected) {
            try { Add-ProCon2BridgeStartupEntry } catch { Write-Warning ('Could not register ProCon2Bridge in the Windows Startup apps: ' + $_.Exception.Message) }
            Write-Host 'ProCon2Bridge is already running. Press a controller button to reconnect.'
            Start-Sleep -Seconds 2
            exit 0
        }
    } catch {} finally { $taskProbe.Dispose() }
    if (-not (Test-Path "$env:ProgramFiles\USBip\usbip.exe") -or -not (Test-Path 'HKLM:\SYSTEM\CurrentControlSet\Services\usbip2_ude')) {
        Write-Host 'First launch: installing the signed USB/IP driver. Accept the Windows administrator prompt.'
        & (Join-Path $PSScriptRoot 'scripts\ProCon2Bridge-Install-Driver.ps1')
        if ($LASTEXITCODE -and $LASTEXITCODE -notin @(0,3010)) { throw 'Driver setup did not complete.' }
    }
    try { Add-ProCon2BridgeStartupEntry } catch { Write-Warning ('Could not register ProCon2Bridge in the Windows Startup apps: ' + $_.Exception.Message) }
    Write-Host 'Keep this window open. Press a button on the controller; hold SYNC for first pairing.'
    Write-Host 'Motion + rumble are automatic. Close with ProCon2Bridge-Stop.cmd. ProCon2Bridge-Calibrate.cmd fixes stationary gyro drift.'
    Write-Host 'Use ProCon2Bridge-Settings.cmd to map GL / GR back buttons while connected.'
    & (Join-Path $PSScriptRoot 'ProCon2Bridge.exe')
    if ($LASTEXITCODE) { throw 'Bridge stopped. Check bridge.log. Restart Windows if driver setup requested it.' }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}
