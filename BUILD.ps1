param([string]$Python = 'python.exe')
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$buildRoot = Join-Path $env:TEMP 'ProCon2Bridge-build'
& $Python -m PyInstaller --noconfirm --clean --onefile --console --name ProCon2Bridge --distpath $taskRoot --workpath (Join-Path $buildRoot 'build') --specpath $buildRoot --collect-submodules winrt --hidden-import bleak.backends.winrt --hidden-import winrt.windows.devices.bluetooth --hidden-import winrt.windows.devices.bluetooth.advertisement --hidden-import winrt.windows.devices.bluetooth.genericattributeprofile --hidden-import winrt.windows.devices.enumeration --hidden-import winrt.windows.foundation --hidden-import winrt.windows.foundation.collections --hidden-import winrt.windows.storage.streams (Join-Path $taskRoot 'bridge.py')
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
