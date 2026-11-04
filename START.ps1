$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + [IO.Path]::PathSeparator + $env:PSModulePath
try {
    Set-Location -LiteralPath $PSScriptRoot
    $taskProbe = [Net.Sockets.TcpClient]::new()
    try {
        $taskConnect = $taskProbe.ConnectAsync('127.0.0.1',26759)
        if ($taskConnect.Wait(300) -and $taskProbe.Connected) {
            Write-Host 'ProCon2Bridge is already running. Press a controller button to reconnect.'
            Start-Sleep -Seconds 2
            exit 0
        }
    } catch {} finally { $taskProbe.Dispose() }
    if (-not (Test-Path "$env:ProgramFiles\USBip\usbip.exe") -or -not (Test-Path 'HKLM:\SYSTEM\CurrentControlSet\Services\usbip2_ude')) {
        Write-Host 'First launch: installing the signed USB/IP driver. Accept the Windows administrator prompt.'
        & (Join-Path $PSScriptRoot 'scripts\INSTALL-DRIVER.ps1')
        if ($LASTEXITCODE -and $LASTEXITCODE -notin @(0,3010)) { throw 'Driver setup did not complete.' }
    }
    Write-Host 'Keep this window open. Press a button on the controller; hold SYNC for first pairing.'
    Write-Host 'Motion + rumble are automatic. Close with STOP.cmd. CALIBRATE.cmd fixes stationary gyro drift.'
    Write-Host 'Use SETTINGS.cmd to map GL / GR back buttons while connected.'
    & (Join-Path $PSScriptRoot 'ProCon2Bridge.exe')
    if ($LASTEXITCODE) { throw 'Bridge stopped. Check bridge.log. Restart Windows if driver setup requested it.' }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}
