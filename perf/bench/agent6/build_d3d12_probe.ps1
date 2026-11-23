# Builds build/agent6/d3d12_library_probe.exe from bench/agent6/d3d12_library_probe.cpp.
# Usage (any directory): powershell -File bench/agent6/build_d3d12_probe.ps1
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $root
try {
    . (Join-Path $root 'env/devshell.ps1') -Quiet
    New-Item -ItemType Directory -Force build/agent6 | Out-Null
    & clang++ -std=c++20 -O2 -DNOMINMAX -DWIN32_LEAN_AND_MEAN -Wall -Wno-missing-braces `
        bench/agent6/d3d12_library_probe.cpp -o build/agent6/d3d12_library_probe.exe `
        -ld3d12 -ldxgi -ld3dcompiler -ladvapi32
    if ($LASTEXITCODE -ne 0) { throw "clang++ failed with exit code $LASTEXITCODE" }
    Write-Host "built build/agent6/d3d12_library_probe.exe"
} finally { Pop-Location }
