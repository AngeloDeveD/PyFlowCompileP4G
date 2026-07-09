param(
    [string]$CompilerPath = "E:\Development\PersonaCompiler\pyFlowCompile\tools\AtlusScriptTools\AtlusScriptCompiler.exe",
    [string]$OriginalF007 = "E:\Development\PersonaCompiler\Atlus-Script-Tools\Samples\P4G_Steam_Test\data_e.cpk\field\script\f007.bf"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = Join-Path $root "Source"
$buildDir = Join-Path $root "build"
$runtimeA = Join-Path $root "FEmulator\PAK\field\pack\fd007_001.arc"
$runtimeB = Join-Path $root "FEmulator\PAK\field\pack\fd007_002.arc"

# Keep the original script beside the hook source so the compiler can resolve
# import("original_f007.bf") during hook compilation.
Copy-Item -Path $OriginalF007 -Destination (Join-Path $sourceDir "original_f007.bf") -Force

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeA | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeB | Out-Null

$outputBf = Join-Path $buildDir "f007.bf"

& $CompilerPath `
    -Compile `
    -Hook `
    -In (Join-Path $sourceDir "f007_night_bonus.flow") `
    -Out $outputBf `
    -Library P4G `
    -Encoding P4G_EFIGS `
    -OutFormat V1

if ($LASTEXITCODE -ne 0) {
    throw "AtlusScriptCompiler failed with exit code $LASTEXITCODE"
}

Copy-Item -Path $outputBf -Destination (Join-Path $runtimeA "f007.bf") -Force
Copy-Item -Path $outputBf -Destination (Join-Path $runtimeB "f007.bf") -Force
