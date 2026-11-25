# E5.1 for M6, 2026-11-25: the #33 synthetic tests (make_test_s33.py) through RUN-S33-LOGDIFF.cmd, one process at a
# time at below-normal priority. Writes build\agent6\s33-popin\test-s33\ (EXITCODES.txt, out-*, *.out.txt) and
# build\agent6\wnight\s3-regress\test_s33.*.txt. Exit = make_test_s33.py --check's exit (0 = all as expected).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent6\wnight\s3-regress\run_test_s33.ps1
$ErrorActionPreference = 'Continue'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
Set-Location $root
if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { Write-Host 'perf-notes\WINDOW-HOLD.txt exists; not starting'; exit 3 }
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
$t = 'build\agent6\s33-popin\test-s33'
$w = 'build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd'
$log = 'build\agent6\wnight\s3-regress'
python -B build\agent6\s33-popin\make_test_s33.py *> "$log\test_s33.make.txt"
Write-Host "make_test_s33.py exit $LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { exit 1 }

function RunArgs($dir) {
    (Get-ChildItem $dir -Directory | Sort-Object Name | ForEach-Object {
        $arm = ($_.Name -replace '^\d{8}-\d{6}-s33-', '') -replace '-\d+$', ''
        "--run $arm=$dir\$($_.Name)"
    }) -join ' '
}
$hpos = RunArgs "$t\harness"
$hneg = RunArgs "$t\harness-neg"
$offsf = (Get-ChildItem "$t\harness" -Directory | Where-Object Name -like '*-s33-offsf' | Select-Object -First 1).Name
$cases = [ordered]@{
    'matrix'        = "$t\matrix --out $t\out-matrix"
    'matrix-neg'    = "$t\matrix-neg --out $t\out-matrix-neg"
    'harness'       = "$hpos --out $t\out-harness"
    'harness-neg'   = "$hneg --out $t\out-harness-neg"
    'hyphen-expect' = "$t\matrix --expect $t\hyphen-expect.json --skip-logdiff --out $t\out-hyphen-expect"
    'hyphen-run'    = "--run off-sf=$t\harness\$offsf --skip-logdiff --out $t\out-hyphen-run"
    'mixed'         = "--run offsf=$t\harness\$offsf $t\matrix --skip-logdiff --out $t\out-mixed"
    'none'          = "--ref offsf --skip-logdiff --out $t\out-none"
    'noargs'        = ''
}
$rc = @()
foreach ($k in $cases.Keys) {
    if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { Write-Host 'HOLD appeared; stopping'; exit 3 }
    $cmd = "$w $($cases[$k])".Trim()
    Set-Content -Path "$t\$k.cmdline.txt" -Value $cmd -Encoding ascii
    cmd /c "$cmd > $t\$k.out.txt 2>&1"
    $rc += "$k=$LASTEXITCODE"
    Write-Host "$k exit $LASTEXITCODE  ($cmd)"
}
Set-Content -Path "$t\EXITCODES.txt" -Value $rc -Encoding ascii
python -B build\agent6\s33-popin\make_test_s33.py --check *> "$log\test_s33.check.txt"
$c = $LASTEXITCODE
Get-Content "$log\test_s33.check.txt"
Write-Host "make_test_s33.py --check exit $c"
exit $c
