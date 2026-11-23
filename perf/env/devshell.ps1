# Dimensions Recompiled dev shell: VS 2022 x64 environment + portable LLVM clang + CMake + Ninja.
#
# Usage (Windows PowerShell 5.1 or PowerShell 7), from the workspace root:
#   . games/lego-dimensions-recomp/env/devshell.ps1 [-Quiet] [-Jobs N] [-Refresh]
#
#   -Quiet    no summary line
#   -Jobs N   default for CMAKE_BUILD_PARALLEL_LEVEL (default 4; the CPU is shared)
#   -Refresh  regenerate the cached VS environment (env/.cache/vsenv-x64.json)
#
# Every agent command runs in a fresh session, so the vcvars64.bat environment is
# captured once and cached; later loads only apply the cached delta (fast).
# Only environment variables are changed; no variables or functions leak into
# the caller's scope. Re-sourcing in the same session is a no-op.
#
# Sets: PATH (LLVM bin, CMake, Ninja, MSVC), INCLUDE/LIB/LIBPATH etc. from vcvars,
#   CC=clang  CXX=clang++  CMAKE_GENERATOR=Ninja  CMAKE_BUILD_PARALLEL_LEVEL=<Jobs>
#   LEGO_ROOT       games/lego-dimensions-recomp
#   LEGO_GAME       games/lego-dimensions-recomp/DimensionsRecomp
#   LEGO_SDK        games/lego-dimensions-recomp/DimensionsRecomp/rexglue-sdk
#   LEGO_SDK_BUILD  games/lego-dimensions-recomp/build/sdk
#   LEGO_LLVM       the LLVM install used (toolchain/llvm-<version>)
& {
    param([string]$envDir, [object[]]$argv)
    $ErrorActionPreference = 'Stop'

    $quiet = $false; $refresh = $false; $jobs = 4
    for ($i = 0; $i -lt $argv.Count; $i++) {
        switch -Regex ([string]$argv[$i]) {
            '^-Quiet$'   { $quiet = $true }
            '^-Refresh$' { $refresh = $true }
            '^-Jobs$'    { $i++; $jobs = [int]$argv[$i] }
            default      { throw "devshell.ps1: unknown argument '$($argv[$i])'" }
        }
    }

    $root = Split-Path -Parent $envDir
    $toolchain = Join-Path $root 'toolchain'

    function Add-PathFront([string[]]$dirs) {
        $cur = @($env:PATH -split ';' | Where-Object { $_ })
        $front = @()
        foreach ($d in $dirs) {
            if (-not $d) { continue }
            $cur = @($cur | Where-Object { $_.TrimEnd('\') -ne $d.TrimEnd('\') })
            $front += $d
        }
        $env:PATH = (@($front) + @($cur)) -join ';'
    }

    # ---- Visual Studio x64 environment (cached) ------------------------------------
    $cacheDir = Join-Path $envDir '.cache'
    $cacheFile = Join-Path $cacheDir 'vsenv-x64.json'
    $cache = $null
    $vs = $null
    # Fast path: reuse the cached VS install while its default MSVC version is unchanged (skips vswhere).
    if (-not $refresh -and (Test-Path $cacheFile)) {
        try {
            $c = Get-Content $cacheFile -Raw | ConvertFrom-Json
            $cDefault = Join-Path $c.vs 'VC\Auxiliary\Build\Microsoft.VCToolsVersion.default.txt'
            if ($c.format -eq 1 -and (Test-Path $cDefault) -and (Get-Content $cDefault -Raw).Trim() -eq $c.vcToolsVersion) {
                $cache = $c; $vs = $c.vs
            }
        } catch { $cache = $null }
    }
    if (-not $vs) {
        $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
        if (Test-Path $vswhere) {
            $vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1
        }
        if (-not $vs) { $vs = 'C:\Program Files\Microsoft Visual Studio\2022\Community' }
    }
    $vcvars = Join-Path $vs 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path $vcvars)) { throw "devshell.ps1: vcvars64.bat not found under '$vs'" }
    $vcDefault = Join-Path $vs 'VC\Auxiliary\Build\Microsoft.VCToolsVersion.default.txt'
    $vcVer = if (Test-Path $vcDefault) { (Get-Content $vcDefault -Raw).Trim() } else { '?' }
    $alreadyVs = [bool]($env:VCToolsInstallDir -and $env:INCLUDE -and $env:LIB)
    if (-not $cache -and -not $alreadyVs) {
        # Capture "set" before and after vcvars64.bat in one cmd process; keep the delta.
        $tmp = Join-Path ([IO.Path]::GetTempPath()) ("devshell-vsenv-{0}.cmd" -f $PID)
        $marker = '__DEVSHELL_VSENV_MARKER__'
        Set-Content -Path $tmp -Encoding ASCII -Value @(
            '@echo off', 'set', "echo $marker", "call `"$vcvars`" >nul 2>&1", 'set')
        try { $lines = & cmd.exe /d /c $tmp } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
        $before = @{}; $after = @{}; $target = $before
        foreach ($l in $lines) {
            if ($l -eq $marker) { $target = $after; continue }
            $eq = $l.IndexOf('=')
            if ($eq -gt 0) { $target[$l.Substring(0, $eq)] = $l.Substring($eq + 1) }
        }
        if (-not $after['VCToolsInstallDir'] -or -not $after['INCLUDE']) {
            throw "devshell.ps1: vcvars64.bat did not produce a usable environment"
        }
        $vars = [ordered]@{}
        foreach ($k in ($after.Keys | Sort-Object)) {
            if ($k -ieq 'PATH' -or $k -ieq 'PROMPT') { continue }
            if (-not $before.ContainsKey($k) -or $before[$k] -ne $after[$k]) { $vars[$k] = $after[$k] }
        }
        $oldPath = @($before['Path'] -split ';' | Where-Object { $_ } | ForEach-Object { $_.TrimEnd('\') })
        $pathAdd = @($after['Path'] -split ';' | Where-Object { $_ -and ($oldPath -notcontains $_.TrimEnd('\')) })
        $cache = [pscustomobject]@{
            format = 1; vs = $vs; vcToolsVersion = $vcVer; created = (Get-Date).ToString('s')
            vars = [pscustomobject]$vars; pathPrepend = $pathAdd
        }
        New-Item -ItemType Directory -Force $cacheDir | Out-Null
        $part = "$cacheFile.$PID.tmp"
        $cache | ConvertTo-Json -Depth 4 | Set-Content -Path $part -Encoding UTF8
        Move-Item -Force $part $cacheFile
    }
    if ($cache -and -not $alreadyVs) {
        foreach ($p in $cache.vars.PSObject.Properties) {
            [Environment]::SetEnvironmentVariable($p.Name, [string]$p.Value, 'Process')
        }
        Add-PathFront @($cache.pathPrepend)
    }

    # ---- LLVM (newest toolchain/llvm-*/bin/clang.exe) -------------------------------
    $llvm = Get-ChildItem $toolchain -Directory -Filter 'llvm-*' -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName 'bin\clang.exe') } |
        Sort-Object { try { [version]($_.Name -replace '^llvm-', '') } catch { [version]'0.0' } } -Descending |
        Select-Object -First 1
    if (-not $llvm) {
        Write-Warning "devshell.ps1: no LLVM found under $toolchain (expected llvm-<version>\bin\clang.exe); clang is NOT on PATH"
    }

    # ---- CMake + Ninja: toolchain/cmake-*/bin if present, else the VS bundled ones ----
    $cmakeBin = Get-ChildItem $toolchain -Directory -Filter 'cmake-*' -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName 'bin\cmake.exe') } |
        Sort-Object Name -Descending | Select-Object -First 1 | ForEach-Object { Join-Path $_.FullName 'bin' }
    if (-not $cmakeBin) { $cmakeBin = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin' }
    $ninjaDir = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja'
    if (Test-Path (Join-Path $toolchain 'ninja\ninja.exe')) { $ninjaDir = Join-Path $toolchain 'ninja' }

    $front = @()
    if ($llvm) { $front += (Join-Path $llvm.FullName 'bin') }
    $front += $cmakeBin, $ninjaDir
    Add-PathFront $front

    if ($llvm) {
        $env:CC = 'clang'; $env:CXX = 'clang++'
        $env:LEGO_LLVM = $llvm.FullName
    }
    $env:CMAKE_GENERATOR = 'Ninja'
    if (-not $env:CMAKE_BUILD_PARALLEL_LEVEL -or ($argv -contains '-Jobs')) { $env:CMAKE_BUILD_PARALLEL_LEVEL = "$jobs" }
    $env:LEGO_ROOT = $root
    $env:LEGO_GAME = Join-Path $root 'DimensionsRecomp'
    $env:LEGO_SDK = Join-Path $root 'DimensionsRecomp\rexglue-sdk'
    $env:LEGO_SDK_BUILD = Join-Path $root 'build\sdk'
    $env:LEGO_DEVSHELL = '1'

    if (-not $quiet) {
        $clangVer = if ($llvm) { $llvm.Name -replace '^llvm-', '' } else { 'MISSING' }
        $cmakeVer = ((& (Join-Path $cmakeBin 'cmake.exe') --version | Select-Object -First 1) -replace '^cmake version ', '')
        Write-Host ("devshell: clang {0} | MSVC {1} | WinSDK {2} | cmake {3} | jobs {4} | LEGO_ROOT={5}" -f `
            $clangVer, $env:VCToolsVersion, ($env:WindowsSDKVersion -replace '\\$', ''), $cmakeVer, $env:CMAKE_BUILD_PARALLEL_LEVEL, $root)
    }
} $PSScriptRoot $args
