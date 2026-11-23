# harness/vpad/build-vpad.ps1 - builds Agent 3's virtual XInput pad (harness-only test tooling, user mode only):
#   powershell -NoProfile -ExecutionPolicy Bypass -File harness\vpad\build-vpad.ps1 [-OutDir build\agent3\vpad] [-Force]
# harness\vpad\xinput1_4.c + .def -> <OutDir>\xinput1_4.dll with toolchain\llvm-23.1.6 clang-cl + lld-link
# (one compile, /threads:1), no CRT, kernel32.lib from the newest Windows 10 SDK. harness\run-game.ps1 -InputScript
# copies the DLL into its run dir only; it never goes into a staged build\agent2\*-bin.
# Skips the build when <OutDir>\xinput1_4.dll is newer than xinput1_4.c and .def. Every link stamps a new PE
# TimeDateStamp (bytes 0x80-0x83), and the B-gate runs record the DLL's sha256 (309DF316... for bgate-dry, -a, -b and
# the -long pair), so a needless rebuild would make later runs differ from them. -Force rebuilds. The self-test builds
# its own copy (-OutDir build\agent3\selftest-bin\vpad -Force) and leaves build\agent3\vpad alone.
param([string]$OutDir = '', [switch]$Force)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$llvm = Join-Path $repo 'toolchain\llvm-23.1.6\bin'
$out = if ($OutDir) { [IO.Path]::GetFullPath([IO.Path]::Combine((Get-Location).Path, $OutDir)) } else { Join-Path $repo 'build\agent3\vpad' }
New-Item -ItemType Directory -Force -Path $out | Out-Null
$obj = Join-Path $out 'xinput1_4.obj'; $dll = Join-Path $out 'xinput1_4.dll'
if (-not $Force -and (Test-Path -LiteralPath $dll)) {
    $newest = @('xinput1_4.c', 'xinput1_4.def') | ForEach-Object { (Get-Item -LiteralPath (Join-Path $PSScriptRoot $_)).LastWriteTimeUtc } |
        Sort-Object -Descending | Select-Object -First 1
    if ((Get-Item -LiteralPath $dll).LastWriteTimeUtc -ge $newest) {
        Write-Host "up to date: $dll ($((Get-Item -LiteralPath $dll).Length) bytes, sha256 $((Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash)); -Force rebuilds"
        exit 0
    }
}
$sdkLib = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\Lib' -Directory | Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName 'um\x64' } | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'kernel32.lib') } | Select-Object -First 1
if (-not $sdkLib) { throw 'no Windows 10 SDK um\x64\kernel32.lib' }
& (Join-Path $llvm 'clang-cl.exe') /nologo /c /O2 /GS- /Zl /W4 /WX "/Fo$obj" (Join-Path $PSScriptRoot 'xinput1_4.c')
if ($LASTEXITCODE) { throw "clang-cl failed ($LASTEXITCODE)" }
& (Join-Path $llvm 'lld-link.exe') /nologo /DLL /NODEFAULTLIB /ENTRY:VpadDllMain /SUBSYSTEM:WINDOWS /MACHINE:X64 /INCREMENTAL:NO /OPT:REF /threads:1 `
    "/DEF:$(Join-Path $PSScriptRoot 'xinput1_4.def')" "/OUT:$dll" $obj (Join-Path $sdkLib 'kernel32.lib')
if ($LASTEXITCODE) { throw "lld-link failed ($LASTEXITCODE)" }
Write-Host "built $dll ($((Get-Item -LiteralPath $dll).Length) bytes, sha256 $((Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash))"
