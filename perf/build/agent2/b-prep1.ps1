# Agent 2 (session 3, 02:05): B tool prep, step 1 checks. Builds nothing: compiles the 74-line codegen-frozen2.exe stand-in,
# tests it (it only fopen()s files, 'rb'), then runs gen-check.py and snap-gate.py in DEFAULT mode against snap1 (both
# read-only there: snap1's codegen.d already has snapshot paths). Writes only build/agent2/codegen-frozen/codegen-frozen2.exe,
# build/agent2/cf2-test/ (scratch) and the b-prep1*.txt/.log files.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\b-prep1.ps1
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$log = "$A\b-prep1.txt"
function Log([string]$m) { $line = "$(Get-Date -Format HH:mm:ss) $m"; $line | Out-File -Append -Encoding utf8 $log; Write-Host $line }
Set-Location $R
. "$R\env\devshell.ps1" -Quiet
$fails = 0
$cf = "$A\codegen-frozen"
Log ("START b-prep1; codegen-frozen.exe (snap1 trees) sha256 {0}" -f (Get-FileHash "$cf\codegen-frozen.exe").Hash.Substring(0, 16))
Push-Location $cf
$out = & clang -O2 -o codegen-frozen2.exe codegen_frozen2.c 2>&1
$c = $LASTEXITCODE
Pop-Location
Log "compile: clang -O2 -o codegen-frozen2.exe codegen_frozen2.c -> exit $c $($out -join ' | ')"
if ($c -ne 0) { Log 'RESULT: FAIL (compile)'; exit 1 }
$exe = "$cf\codegen-frozen2.exe"
Log ("codegen-frozen2.exe {0} B sha256 {1}; source sha256 {2}" -f (Get-Item $exe).Length, (Get-FileHash $exe).Hash, (Get-FileHash "$cf\codegen_frozen2.c").Hash.Substring(0, 16))
function T([string]$dir, [string[]]$argv, [int]$want, [string]$expect, [string]$what) {
    Push-Location $dir
    $o = (& $exe @argv 2>&1) -join ' | '
    $code = $LASTEXITCODE
    Pop-Location
    $ok = ($code -eq $want) -and ((-not $expect) -or $o.Contains($expect))
    Log ("test {0} ({1}): exit {2} (want {3}{4}): {5}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $what, $code, $want, $(if ($expect) { ", text '$expect'" } else { '' }), $o)
    if (-not $ok) { $script:fails++ }
}
T "$A\snap1\DimensionsRecomp\rexlego" @('codegen', 'legodimensions_manifest.toml') 0 '(440 sources listed' 'snap1 rexlego: 438 TUs + init + register'
T "$R\build\agent9\install\batch-nolr" @('codegen', '--pointer_table_scan', 'legodimensions_manifest.toml') 0 '(432 sources listed' 'batch-nolr install tree: 430 TUs + init + register'
T "$A\snap1\DimensionsRecomp\rexlego" @('recompile', 'x.toml') 2 '' 'wrong verb'
T "$cf" @('codegen', 'x.toml') 3 'missing generated/rexglue.cmake' 'no generated/ in the working dir'
# scratch tree: sources.cmake in the real format (the snap1 file's non-source lines + 3 source lines)
$t = "$A\cf2-test"
if (Test-Path $t) { Remove-Item -Recurse -Force $t }
$null = New-Item -ItemType Directory -Force "$t\generated\default"
$src = Get-Content "$A\snap1\DimensionsRecomp\rexlego\generated\default\sources.cmake"
$keep = @($src | Where-Object { ($_ -notmatch '\$\{CMAKE_CURRENT_LIST_DIR\}/') -or ($_ -match '/(legodimensions_init|legodimensions_register|legodimensions_recomp\.0)\.cpp') })
Set-Content -Encoding ascii "$t\generated\default\sources.cmake" $keep
foreach ($f in 'generated\rexglue.cmake', 'generated\default\codegen.d', 'generated\default\codegen.build.stamp', 'generated\default\legodimensions_init.cpp', 'generated\default\legodimensions_register.cpp') { Set-Content -Encoding ascii "$t\$f" '' }
T $t @('codegen', 'x.toml') 4 'missing generated/default/legodimensions_recomp.0.cpp' 'a listed TU is missing'
Set-Content -Encoding ascii "$t\generated\default\legodimensions_recomp.0.cpp" ''
T $t @('codegen', 'x.toml') 0 '(3 sources listed' 'scratch tree complete (3 sources)'
Remove-Item "$t\generated\default\legodimensions_register.cpp"
T $t @('codegen', 'x.toml') 4 'missing generated/default/legodimensions_register.cpp' 'register missing'
Set-Content -Encoding ascii "$t\generated\default\sources.cmake" @($keep | Where-Object { $_ -notmatch 'legodimensions_register' })
T $t @('codegen', 'x.toml') 5 'lists 2 sources' 'sources.cmake without register'
# gen-check and the gate in default mode (snap1 / snap1-off), plus the gate on snap1-on
$sw = [Diagnostics.Stopwatch]::StartNew()
& python "$A\gen-check.py" > "$A\b-prep1-gen-check.log" 2>&1
$c = $LASTEXITCODE
$g = @(Get-Content "$A\b-prep1-gen-check.log")
Log ("gen-check (default: baseline vs snap1): exit {0}, {1:N1}s: {2}" -f $c, $sw.Elapsed.TotalSeconds, (($g | Where-Object { $_ -match '^# gen-check|^RESULT|^FAIL' }) -join ' | '))
if ($c -ne 0 -or $g[-1] -ne 'RESULT: PASS') { $fails++ }
foreach ($tree in 'snap1-off', 'snap1-on') {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $gl = "$A\b-prep1-gate-$tree.log"
    & python "$A\snap-gate.py" "$A\$tree" > $gl 2>&1
    $c = $LASTEXITCODE
    $g = @(Get-Content $gl)
    Log ("snap-gate {0} (default snapshot snap1): exit {1}, {2:N1}s: {3}" -f $tree, $c, $sw.Elapsed.TotalSeconds, (($g | Where-Object { $_ -match '^# snap-gate|^headers|^rexglue_DIR|^RESULT|^  - ' }) -join ' | '))
    if ($c -ne 0 -or -not ($g -contains 'RESULT: PASS')) { $fails++ }
}
Log ("RESULT: {0}" -f $(if ($fails -eq 0) { 'PASS' } else { "FAIL ($fails)" }))
exit $(if ($fails -eq 0) { 0 } else { 1 })
