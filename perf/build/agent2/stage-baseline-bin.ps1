# Agent 2 - stage the verified NATIVE_GPU=OFF baseline game into build/baseline-bin (task #1 step 4).
# Verifies the ARTIFACTS (README-dev "Things that have cost real time"), not the build log:
#   - strings in the exe and the two DLLs, native_lock_elide.cpp.obj present in the link map,
#   - rexruntime.dll in build/baseline == build/sdk/install/bin (POST_BUILD copy_if_different),
#   - rexgpu-xenos.dll: build/baseline has NO copy rule in find_package mode, so it is taken from
#     build/sdk/install/bin and must equal the SDK output tree (baseline/.../rexglue-sdk/out/win-amd64/Release),
#   - import tables (llvm-readobj): TracyClient.dll is staged on request (Agent 1, 18:50) but nothing imports it,
#   - every staged file hashes equal to its source. Writes build/baseline-bin/MANIFEST.txt.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\stage-baseline-bin.ps1
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
$B = "$R\build\baseline"; $I = "$R\build\sdk\install\bin"; $O = "$R\build\baseline-bin"
$sdkOut = "$R\baseline\DimensionsRecomp\rexglue-sdk\out\win-amd64\Release"
$RO = "$R\toolchain\llvm-23.1.6\bin\llvm-readobj.exe"
$items = [ordered]@{
    'legodimensions.exe'       = "$B\legodimensions.exe"
    'legodimensions.map'       = "$B\legodimensions.map"
    'rexruntime.dll'           = "$B\rexruntime.dll"
    'rexgpu-xenos.dll'         = "$I\rexgpu-xenos.dll"
    'TracyClient.dll'          = "$I\TracyClient.dll"
    'achievement_unlocked.wav' = "$B\achievement_unlocked.wav"
    'FiraSans-Regular.ttf'     = "$R\baseline\DimensionsRecomp\rexlego\res\FiraSans-Regular.ttf"
}
$fails = New-Object System.Collections.Generic.List[string]
$report = New-Object System.Collections.Generic.List[string]
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 $p).Hash }
function Check([bool]$ok, [string]$what) { $report.Add(("{0} {1}" -f ($(if ($ok) { 'PASS' } else { 'FAIL' })), $what)); if (-not $ok) { $fails.Add($what) } }
function HasStrings([string]$file, [string[]]$needles) {
    $text = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($file))
    foreach ($n in $needles) { Check ($text.Contains($n)) ("{0} contains '{1}'" -f (Split-Path -Leaf $file), $n) }
    $text = $null; [GC]::Collect()
}
foreach ($k in $items.Keys) { Check (Test-Path $items[$k]) "source exists: $($items[$k].Substring($R.Length + 1))" }
if ($fails.Count) { $report; exit 1 }
# freshness: exe newer than every object it links (and the shimmed TU)
$exe = Get-Item $items['legodimensions.exe']
$newestObj = Get-ChildItem "$B\CMakeFiles" -Recurse -Filter *.obj | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Check ($exe.LastWriteTime -ge $newestObj.LastWriteTime) ("exe {0:HH:mm:ss} newer than newest obj {1} {2:HH:mm:ss}" -f $exe.LastWriteTime, $newestObj.Name, $newestObj.LastWriteTime)
$map = Get-Item $items['legodimensions.map']
Check ($map.LastWriteTime -ge $exe.LastWriteTime.AddSeconds(-5)) ("map written with the exe ({0:HH:mm:ss})" -f $map.LastWriteTime)
Check ([bool](Select-String -Path $map.FullName -Pattern 'native_lock_elide\.cpp\.obj' -Quiet)) "map lists native_lock_elide.cpp.obj (shimmed TU is linked)"
# DLL identity
Check ((Sha "$B\rexruntime.dll") -eq (Sha "$I\rexruntime.dll")) "build/baseline/rexruntime.dll == build/sdk/install/bin/rexruntime.dll"
Check ((Sha "$I\rexgpu-xenos.dll") -eq (Sha "$sdkOut\rexgpu-xenos.dll")) "install/bin/rexgpu-xenos.dll == SDK out tree rexgpu-xenos.dll"
Check ((Sha "$I\rexruntime.dll") -eq (Sha "$sdkOut\rexruntime.dll")) "install/bin/rexruntime.dll == SDK out tree rexruntime.dll"
# import tables: every non-system DLL a binary imports must be staged; TracyClient.dll must not be needed.
# (build/sdk is Ninja Multi-Config: src/core + src/system link TracyClient and define REXGLUE_ENABLE_PROFILING only
#  for $<NOT:$<CONFIG:Release>>, so the Release binaries carry no Tracy/profiling code.)
$importLines = New-Object System.Collections.Generic.List[string]
foreach ($k in 'legodimensions.exe', 'rexruntime.dll', 'rexgpu-xenos.dll', 'TracyClient.dll') {
    $imp = @(& $RO --coff-imports $items[$k] 2>&1 | Select-String -Pattern '^\s*Name:\s*(\S+\.dll)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
    Check ($imp.Count -gt 0) "$k import table readable ($($imp.Count) DLLs)"
    $local = @($imp | Where-Object { $_ -match '^(rexruntime|rexgpu-xenos|TracyClient|rexglue.*|legodimensions.*)\.dll$' })
    foreach ($l in $local) { Check ($items.Contains($l)) "$k imports $l, which is staged" }
    if ($k -ne 'TracyClient.dll') { Check ($imp -notcontains 'TracyClient.dll') "$k does not import TracyClient.dll" }
    $importLines.Add(("#   {0} imports: {1}" -f $k, ($imp -join ', ')))
}
# strings (README-dev: look in the actual binary). Use literals of 16+ chars: clang -O3 builds short std::string
# literals (<=15 chars, MSVC SSO) from instruction immediates, so e.g. the cvar name 'd3d12_bindless' and 'GPU/D3D12'
# are absent from rexgpu-xenos.dll even though the DLL is newer than its obj and contains that cvar's description.
HasStrings $items['legodimensions.exe'] @('ui_font', 'FiraSans-Regular.ttf', 'depth_of_field', 'rexruntime.dll')
HasStrings $items['rexgpu-xenos.dll'] @('Use bindless resources where available', 'd3d12_readback_memexport')
HasStrings $items['rexruntime.dll'] @('rexcrt_heap_enable', 'rexcrt_heap_size_mb')
if ($fails.Count) { $report; "NOT staged: $($fails.Count) check(s) failed"; exit 1 }
# stage
New-Item -ItemType Directory -Force $O | Out-Null
$man = New-Object System.Collections.Generic.List[string]
$man.Add("# build/baseline-bin - Agent 2, task #1 step 4. NATIVE_GPU=OFF baseline, Release, game x86-64-v3, SDK x86-64-v2.")
$man.Add("# staged $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); snapshot baseline/DimensionsRecomp (127e04b + SDK 2897c31); codegen 0.0.23.3.")
$man.Add("# No PDBs exist for this configuration: the exe links without /DEBUG (LINK_FLAGS = /subsystem:windows /MAP:legodimensions.map)")
$man.Add("# and the SDK install has none. Symbols: legodimensions.map. Runtime also needs legodimensions.toml in the working dir.")
$man.Add("# TracyClient.dll is staged on request only: no staged binary imports it (Release has no Tracy/REXGLUE_ENABLE_PROFILING code).")
$man.Add("# Not staged: the mod manager 'mods' folder (README-dev lists it for the installer package, not for running the game).")
$man.Add("# name`tsize`tmtime`tsha256`tsource")
foreach ($k in $items.Keys) {
    $src = $items[$k]; $dst = Join-Path $O $k
    Copy-Item $src $dst -Force
    $hs = Sha $src; $hd = Sha $dst
    Check ($hs -eq $hd) "staged copy identical: $k"
    $f = Get-Item $src
    $man.Add(("{0}`t{1}`t{2:yyyy-MM-dd HH:mm:ss}`t{3}`t{4}" -f $k, $f.Length, $f.LastWriteTime, $hd, $src.Substring($R.Length + 1)))
}
$man.Add("# imports (llvm-readobj --coff-imports):")
foreach ($l in $importLines) { $man.Add($l) }
$man.Add("# checks:")
foreach ($l in $report) { $man.Add("#   $l") }
$man | Out-File -Encoding utf8 "$O\MANIFEST.txt"
$report
if ($fails.Count) { "STAGED WITH FAILURES: $($fails.Count)"; exit 1 }
"staged $($items.Count) files into $O"
exit 0
