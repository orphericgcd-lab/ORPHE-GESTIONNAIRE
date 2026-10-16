$ErrorActionPreference = 'Stop'

$keys = @(
    'HKCU:\Software\Classes\Directory\shell\ORPHE-GEST',
    'HKCU:\Software\Classes\Directory\Background\shell\ORPHE-GEST',
    'HKCU:\Software\Classes\Drive\shell\ORPHE-GEST'
)

foreach ($key in $keys) {
    if (Test-Path -LiteralPath $key) {
        Remove-Item -LiteralPath $key -Recurse -Force
    }
}

$installDirectory = Join-Path $env:LOCALAPPDATA 'Programs\ORPHE-GEST'
if (Test-Path -LiteralPath $installDirectory -PathType Container) {
    Remove-Item -LiteralPath $installDirectory -Recurse -Force
}

Write-Host 'ORPHE-GEST a été retiré du menu contextuel et désinstallé pour ce compte Windows.'
