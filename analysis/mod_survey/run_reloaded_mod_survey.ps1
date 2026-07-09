param(
    [string]$ModsRoot = "E:\Reloaded-II\Mods",
    [string]$CompilerPath = "E:\Development\PersonaCompiler\pyFlowCompile\tools\AtlusScriptTools\AtlusScriptCompiler.exe",
    [string]$OutputRoot = "E:\Development\PersonaCompiler\pyFlowCompile\analysis\mod_survey\output"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-EncodingForScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FullPath
    )

    # data.cpk usually points at the Japanese/base archive, while data_e.cpk and
    # most file-emulator overrides are written for the EFIGS PC release.
    if ($FullPath -match "\\data\.cpk\\") {
        return "P4G_JP"
    }

    return "P4G_EFIGS"
}

function Get-ModMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.DirectoryInfo]$Directory
    )

    $configPath = Join-Path $Directory.FullName "ModConfig.json"
    $metadata = [ordered]@{
        folder = $Directory.Name
        modId = $Directory.Name
        modName = $Directory.Name
        modAuthor = $null
        modVersion = $null
        modDescription = $null
        hasDll = $false
    }

    if (-not (Test-Path $configPath)) {
        return [pscustomobject]$metadata
    }

    try {
        $json = Get-Content -Path $configPath -Raw | ConvertFrom-Json
        if ($null -ne $json.ModId -and $json.ModId -ne "") { $metadata.modId = $json.ModId }
        if ($null -ne $json.ModName -and $json.ModName -ne "") { $metadata.modName = $json.ModName }
        if ($null -ne $json.ModAuthor -and $json.ModAuthor -ne "") { $metadata.modAuthor = $json.ModAuthor }
        if ($null -ne $json.ModVersion -and $json.ModVersion -ne "") { $metadata.modVersion = $json.ModVersion }
        if ($null -ne $json.ModDescription -and $json.ModDescription -ne "") { $metadata.modDescription = $json.ModDescription }
        if ($null -ne $json.ModDll -and $json.ModDll -ne "") { $metadata.hasDll = $true }
    }
    catch {
        $metadata.modDescription = "Failed to parse ModConfig.json: $($_.Exception.Message)"
    }

    return [pscustomobject]$metadata
}

function Convert-ToRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BasePath,
        [Parameter(Mandatory = $true)]
        [string]$FullPath
    )

    $baseUri = [System.Uri]((Resolve-Path $BasePath).Path + [System.IO.Path]::DirectorySeparatorChar)
    $fullUri = [System.Uri](Resolve-Path $FullPath).Path
    $relative = $baseUri.MakeRelativeUri($fullUri).ToString()
    return [System.Uri]::UnescapeDataString($relative).Replace("/", "\")
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$targetMods = Get-ChildItem -Path $ModsRoot -Directory |
    Where-Object { $_.Name -match "^(p4g|p4g64|p4gpc|p4r)" } |
    Sort-Object Name

$inventory = [ordered]@{
    generatedAt = (Get-Date).ToString("s")
    modsRoot = $ModsRoot
    compilerPath = $CompilerPath
    outputRoot = $OutputRoot
    mods = @()
}

foreach ($mod in $targetMods) {
    Write-Host "Surveying $($mod.Name)..."

    $metadata = Get-ModMetadata -Directory $mod
    $bfFiles = @(Get-ChildItem -Path $mod.FullName -Recurse -Filter "*.bf" -File -ErrorAction SilentlyContinue)
    $flowFiles = @(Get-ChildItem -Path $mod.FullName -Recurse -Filter "*.flow" -File -ErrorAction SilentlyContinue)
    $msgFiles = @(Get-ChildItem -Path $mod.FullName -Recurse -Include "*.msg","*.msg.h" -File -ErrorAction SilentlyContinue)

    $modOutputRoot = Join-Path $OutputRoot $mod.Name
    New-Item -ItemType Directory -Force -Path $modOutputRoot | Out-Null

    $scriptEntries = @()

    foreach ($bf in $bfFiles) {
        $relativePath = Convert-ToRelativePath -BasePath $mod.FullName -FullPath $bf.FullName
        $encoding = Get-EncodingForScript -FullPath $bf.FullName
        $baseOutputPath = Join-Path $modOutputRoot ($relativePath -replace "\.bf$", "")
        $outputDirectory = Split-Path -Parent $baseOutputPath
        $logPath = "$baseOutputPath.decompile.log.txt"

        New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

        $entry = [ordered]@{
            relativeBfPath = $relativePath
            size = [int64]$bf.Length
            encoding = $encoding
            placeholder = ($bf.Length -eq 0)
            decompileAttempted = $false
            decompileSucceeded = $false
            outputFlow = $null
            outputMsg = $null
            outputMsgHeader = $null
            logPath = $null
            error = $null
        }

        if ($bf.Length -gt 0) {
            $entry.decompileAttempted = $true
            $arguments = @(
                "-Decompile",
                "-In", $bf.FullName,
                "-Out", "$baseOutputPath.flow",
                "-Library", "P4G",
                "-Encoding", $encoding
            )

            try {
                & $CompilerPath @arguments 2>&1 | Out-File -FilePath $logPath -Encoding utf8
                $exitCode = $LASTEXITCODE

                $flowPath = "$baseOutputPath.flow"
                $msgPath = "$baseOutputPath.msg"
                $msgHeaderPath = "$baseOutputPath.msg.h"

                $entry.logPath = Convert-ToRelativePath -BasePath $OutputRoot -FullPath $logPath
                $entry.outputFlow = if (Test-Path $flowPath) { Convert-ToRelativePath -BasePath $OutputRoot -FullPath $flowPath } else { $null }
                $entry.outputMsg = if (Test-Path $msgPath) { Convert-ToRelativePath -BasePath $OutputRoot -FullPath $msgPath } else { $null }
                $entry.outputMsgHeader = if (Test-Path $msgHeaderPath) { Convert-ToRelativePath -BasePath $OutputRoot -FullPath $msgHeaderPath } else { $null }
                $entry.decompileSucceeded = ($exitCode -eq 0 -and (Test-Path $flowPath))

                if (-not $entry.decompileSucceeded) {
                    $entry.error = "Decompiler exited with code $exitCode"
                }
            }
            catch {
                $entry.logPath = if (Test-Path $logPath) { Convert-ToRelativePath -BasePath $OutputRoot -FullPath $logPath } else { $null }
                $entry.error = $_.Exception.Message
            }
        }

        $scriptEntries += [pscustomobject]$entry
    }

    $inventory.mods += [pscustomobject][ordered]@{
        folder = $metadata.folder
        modId = $metadata.modId
        modName = $metadata.modName
        modAuthor = $metadata.modAuthor
        modVersion = $metadata.modVersion
        modDescription = $metadata.modDescription
        hasDll = $metadata.hasDll
        bfCount = $bfFiles.Count
        bfRealCount = @($bfFiles | Where-Object { $_.Length -gt 0 }).Count
        bfPlaceholderCount = @($bfFiles | Where-Object { $_.Length -eq 0 }).Count
        flowSourceCount = $flowFiles.Count
        messageSourceCount = $msgFiles.Count
        flowSources = @($flowFiles | ForEach-Object { Convert-ToRelativePath -BasePath $mod.FullName -FullPath $_.FullName })
        messageSources = @($msgFiles | ForEach-Object { Convert-ToRelativePath -BasePath $mod.FullName -FullPath $_.FullName })
        scripts = $scriptEntries
    }
}

$inventoryPath = Join-Path $OutputRoot "inventory.json"
$inventory | ConvertTo-Json -Depth 8 | Out-File -FilePath $inventoryPath -Encoding utf8
Write-Host "Inventory written to $inventoryPath"

