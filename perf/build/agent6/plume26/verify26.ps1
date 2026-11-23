# Task #26 verification. Run ONLY after Agent 1 ends the quiet window. Pinned to CPU 5, normal priority
# (the test has 15 s per-command timeouts, so do not starve it). Never touches the live thirdparty/plume.
$p = [Diagnostics.Process]::GetCurrentProcess(); $p.ProcessorAffinity = [IntPtr]0x20
$root = '<workspace>'
Set-Location $root
$dr = Join-Path $root 'DimensionsRecomp'
$live = Join-Path $dr 'thirdparty\plume'
$pin = 'e0c8871b930dc1a6544bf457f2348c456b9d7e13'
$want = '564568D4D5853F22B6823884A79556C773C7679692B3C9022F4DD45B55F6E09E'
$base = Join-Path $root 'build\agent6\plume26'
$scratch = Join-Path $base 'scratch'
$out = Join-Path $base 'test-out'
$prep = Join-Path $dr 'tools\gpu-aot\prepare_plume.py'
$test = Join-Path $dr 'tools\gpu-aot\test_prepare_plume.py'
$patch = Join-Path $dr 'tools\gpu-aot\patches\plume-winsdk-compat.patch'
$t0 = Get-Date
"start $($t0.ToString('HH:mm:ss'))"
foreach ($d in $scratch, $out) { if (Test-Path $d) { cmd /c "rmdir /s /q `"$d`"" } }
cmd /c "git clone -c core.autocrlf=true --shared --no-checkout `"$live`" `"$scratch`" 2>&1"
cmd /c "git -C `"$scratch`" checkout --detach $pin 2>&1"
$head = git -C $scratch rev-parse HEAD; "HEAD = $head"
'--- scratch: prepare_plume.py (apply) ---'
python $prep $scratch; "exit=$LASTEXITCODE"
'--- scratch: prepare_plume.py --check ---'
python $prep $scratch --check; "exit=$LASTEXITCODE"
'--- scratch: prepare_plume.py again (must be a no-op PASS) ---'
python $prep $scratch; "exit=$LASTEXITCODE"
$h = (Get-FileHash (Join-Path $scratch 'plume_d3d12.cpp') -Algorithm SHA256).Hash
"scratch plume_d3d12.cpp sha256 = $h ; equals 564568D4: $($h -eq $want)"
foreach ($f in 'plume_d3d12.cpp', 'plume_d3d12.h', 'plume_vulkan.cpp') {
    $a = (Get-FileHash (Join-Path $scratch $f) -Algorithm SHA256).Hash
    $b = (Get-FileHash (Join-Path $live $f) -Algorithm SHA256).Hash
    "${f}: scratch == live: $($a -eq $b)  ($($a.Substring(0,8)) / $($b.Substring(0,8)))"
}
'--- scratch: git status ---'
cmd /c "git -C `"$scratch`" status --porcelain=v1 2>&1"
'--- test_prepare_plume.py ---'
python $test $out; "exit=$LASTEXITCODE"
if (Test-Path (Join-Path $out 'verification.json')) { Get-Content (Join-Path $out 'verification.json') }
"elapsed $([int]((Get-Date) - $t0).TotalSeconds) s"
