$ErrorActionPreference = 'Stop'

$sourceExe = Join-Path $PSScriptRoot 'dist\ORPHE-GEST.exe'
if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
    throw "L'exécutable est introuvable : $sourceExe. Construisez d'abord ORPHE-GEST.exe."
}

$installDirectory = Join-Path $env:LOCALAPPDATA 'Programs\ORPHE-GEST'
$installedExe = Join-Path $installDirectory 'ORPHE-GEST.exe'
New-Item -ItemType Directory -Path $installDirectory -Force | Out-Null
Copy-Item -LiteralPath $sourceExe -Destination $installedExe -Force

$verbs = @(
    @{
        Key = 'HKCU:\Software\Classes\Directory\shell\ORPHE-GEST'
        Argument = '%1'
    },
    @{
        Key = 'HKCU:\Software\Classes\Directory\Background\shell\ORPHE-GEST'
        Argument = '%V'
    },
    @{
        Key = 'HKCU:\Software\Classes\Drive\shell\ORPHE-GEST'
        Argument = '%1'
    }
)

foreach ($verb in $verbs) {
    New-Item -Path $verb.Key -Force | Out-Null
    Set-Item -Path $verb.Key -Value 'Ouvrir dans ORPHE-GEST'
    New-ItemProperty -Path $verb.Key -Name 'Icon' -Value "`"$installedExe`"" -PropertyType String -Force | Out-Null

    $commandKey = Join-Path $verb.Key 'command'
    New-Item -Path $commandKey -Force | Out-Null
    Set-Item -Path $commandKey -Value "`"$installedExe`" `"$($verb.Argument)`""
}

Write-Host 'ORPHE-GEST est installé pour ce compte Windows.'
Write-Host "Fichier : $installedExe"
Write-Host 'Le menu contextuel des dossiers et lecteurs permet maintenant de l’ouvrir avec ORPHE-GEST.'
Write-Host 'L’Explorateur et les applications par défaut ne sont pas remplacés.'
