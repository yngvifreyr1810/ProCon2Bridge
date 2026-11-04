param([string]$Python = 'python.exe', [string]$Destination = '')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
if (-not $Destination) { $Destination = $taskRoot }
$buildRoot = Join-Path $env:TEMP 'ProCon2Bridge-build'
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --version-file (Join-Path $PSScriptRoot 'ProCon2Bridge-Version.txt') --name ProCon2Bridge --distpath $Destination --workpath (Join-Path $buildRoot 'build') --specpath $buildRoot --collect-submodules winrt --hidden-import pystray._win32 --hidden-import bleak.backends.winrt --hidden-import winrt.windows.devices.bluetooth --hidden-import winrt.windows.devices.bluetooth.advertisement --hidden-import winrt.windows.devices.bluetooth.genericattributeprofile --hidden-import winrt.windows.devices.enumeration --hidden-import winrt.windows.foundation --hidden-import winrt.windows.foundation.collections --hidden-import winrt.windows.storage.streams (Join-Path $taskRoot 'src\bridge.py')
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
