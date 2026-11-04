$ErrorActionPreference = 'Stop'
Start-Process -FilePath (Join-Path $PSScriptRoot 'ProCon2Bridge.exe') -WorkingDirectory $PSScriptRoot
