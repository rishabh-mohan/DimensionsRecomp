# Agent 2 (task #14, 03:55): self-test of the task #14 tools (make-rb-clones.py output, run-nb.ps1, rb-chain.ps1,
# the patched stop-snap.ps1). Nothing is copied, configured or built; console copies go to build/agent2/rbt-logs, and
# the logs the negative tests create (while snapB3 does not exist) are moved there at the end.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\rb-tools-test.ps1
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$L = "$A\rbt-logs"
New-Item -ItemType Directory -Force $L | Out-Null
$script:np = 0; $script:nf = 0
function Check([bool]$ok, [string]$m) { if ($ok) { $script:np++; Write-Host "PASS $m" } else { $script:nf++; Write-Host "FAIL $m" } }
function Tail([string]$p, [int]$n) { (@(Get-Content -LiteralPath $p -ErrorAction SilentlyContinue) | Select-Object -Last $n) -join ' | ' }
$snapB3 = "$A\snapB3"
$vs = 'rb1', 'rb2', 'nb'
Check (-not (Test-Path -LiteralPath $snapB3)) 'snapB3 does not exist before the tests'
Check (-not (Test-Path -LiteralPath "$A\snapB3-manifest-notes.txt")) 'no snapB3-manifest-notes.txt before the tests'

# 1. parse
foreach ($n in 'run-rb1.ps1', 'run-rb2.ps1', 'run-nb.ps1', 'rb-chain.ps1', 'stop-snap.ps1', 'rb-tools-test.ps1') {
    $tok = $null; $err = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile("$A\$n", [ref]$tok, [ref]$err)
    Check ($err.Count -eq 0) "$n parses ($($err.Count) errors)"
}
$o = "$L\ast-parse.txt"
& cmd /d /c "python -c `"import ast,sys; [ast.parse(open(f,'rb').read(), f) for f in sys.argv[1:]]; print('ok', len(sys.argv)-1)`" $A\prep-rb1.py $A\prep-rb2.py $A\prep-nb.py > $o 2>&1"
Check ($LASTEXITCODE -eq 0 -and (Tail $o 1) -eq 'ok 3') "prep-rb1/rb2/nb.py parse (ast): $(Tail $o 1)"

# 2. every quoted '-Param' passed to build-snap.ps1 / stage-snap-bin.ps1 is declared there
function ParamNames([string]$f) {
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$null, [ref]$null)
    @($ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
}
$bsP = ParamNames "$A\build-snap.ps1"; $stP = ParamNames "$A\stage-snap-bin.ps1"
foreach ($v in $vs) {
    $ast = [System.Management.Automation.Language.Parser]::ParseFile("$A\run-$v.ps1", [ref]$null, [ref]$null)
    $asg = @($ast.FindAll({ param($x) $x -is [System.Management.Automation.Language.AssignmentStatementAst] }, $true))
    foreach ($pair in @(@('bsArgs', $bsP, 'build-snap.ps1'), @('stageArgs', $stP, 'stage-snap-bin.ps1'))) {
        $txt = (@($asg | Where-Object { $_.Left.Extent.Text -eq ('$' + $pair[0]) }) | ForEach-Object { $_.Right.Extent.Text }) -join ' '
        $used = @([regex]::Matches($txt, "'-([A-Za-z]+)'") | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
        $bad = @($used | Where-Object { $_ -notin $pair[1] })
        Check ($used.Count -gt 0 -and $bad.Count -eq 0) ("run-$v.ps1 `$$($pair[0]): $($used.Count) params ($($used -join ' ')), all declared in $($pair[2])" + $(if ($bad.Count) { '; undeclared: ' + ($bad -join ', ') } else { '' }))
    }
}

# 3. pins
$pins = @{ 'rb1' = @('rb1-nolocal', 'A966CF18E3EC736F', 'AE9F8F967FBB2649'); 'rb2' = @('rb2-nomusttail', '8BDE87171405EC96', 'FC034D495DAC395F');
    'nb' = @('batch-nolr', '24CE1493FB8DAE37', 'E60EAF1CEB575572') }
foreach ($v in $vs) {
    foreach ($f in "prep-$v.py", "run-$v.ps1") {
        $t = [IO.File]::ReadAllText("$A\$f")
        $miss = @($pins[$v] | Where-Object { $t.IndexOf($_, [StringComparison]::OrdinalIgnoreCase) -lt 0 })
        Check ($miss.Count -eq 0) ("$f pins $($pins[$v] -join ' ')" + $(if ($miss.Count) { '; missing ' + ($miss -join ', ') } else { '' }))
    }
}

# 4. stop-snap.ps1 $drivers names every driver, old and new
$m = [regex]::Match([IO.File]::ReadAllText("$A\stop-snap.ps1"), '(?m)^\$drivers = ''([^'']+)''')
$drvRx = $m.Groups[1].Value
$names = 'build-snap.ps1', 'run-s2.ps1', 'run-s3.ps1', 'run-s3d.ps1', 'run-b.ps1', 'prep-b.py', 'b-chain.ps1', 'rb-chain.ps1', 'run-rb1.ps1',
'run-rb2.ps1', 'prep-rb1.py', 'prep-rb2.py', 'run-nb.ps1', 'prep-nb.py'
$miss = @($names | Where-Object { -not $m.Success -or "powershell -File $A\$_ -Jobs 10" -notmatch $drvRx })
Check ($m.Success -and $miss.Count -eq 0) ("stop-snap.ps1 `$drivers matches all $($names.Count) driver names" + $(if ($miss.Count) { '; misses ' + ($miss -join ', ') } else { '' }))

# 5. each run script's driver guard: the other drivers yes; its own rb-chain parent, cmd wrapper and itself no
$common = 'run-b.ps1', 'b-chain.ps1', 'run-s2.ps1', 'run-s3.ps1', 'run-s3d.ps1', 'build-snap.ps1', 'stage-snap-bin.ps1'
$others = @{ 'rb1' = $common + 'run-rb2.ps1', 'run-nb.ps1'; 'rb2' = $common + 'run-rb1.ps1', 'run-nb.ps1'; 'nb' = $common + 'run-rb1.ps1', 'run-rb2.ps1' }
foreach ($v in $vs) {
    $g = [regex]::Match([IO.File]::ReadAllText("$A\run-$v.ps1"), '\$_\.CommandLine -match ''([^'']+)''')
    $rx = $g.Groups[1].Value
    $miss = @($others[$v] | Where-Object { -not $g.Success -or "powershell -NoProfile -ExecutionPolicy Bypass -File $A\$_ -Jobs 10" -notmatch $rx })
    $selfLines = @("powershell -NoProfile -ExecutionPolicy Bypass -File $A\rb-chain.ps1 -Variant $v -Jobs 10",
        "cmd /d /c `"powershell -NoProfile -ExecutionPolicy Bypass -File $A\run-$v.ps1 -Jobs 10 > $A\rb-chain-$v-run.log 2>&1`"",
        "powershell -NoProfile -ExecutionPolicy Bypass -File $A\run-$v.ps1 -Jobs 10")
    $hit = @($selfLines | Where-Object { $g.Success -and $_ -match $rx })
    Check ($g.Success -and $miss.Count -eq 0 -and $hit.Count -eq 0) ("run-$v.ps1 guard matches the $($others[$v].Count) other drivers and not its own rb-chain / cmd / self lines" +
        $(if ($miss.Count) { '; misses ' + ($miss -join ', ') } else { '' }) + $(if ($hit.Count) { '; hits ' + ($hit -join ' || ') } else { '' }))
}

# 6. rb-chain.ps1 parameter refusals (exit 2, nothing written) and its driver guard (-GuardOnly)
$i = 0
foreach ($cs in @(@('bogus', '-Variant bogus'), @('novariant', ''), @('resync-skipcopy', '-Variant nb -Resync -SkipCopy'), @('jobs11', '-Variant nb -Jobs 11'))) {
    $o = "$L\chain-$($cs[0]).txt"
    & cmd /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File $A\rb-chain.ps1 $($cs[1]) > $o 2>&1"
    $c = $LASTEXITCODE
    $logs = @(Get-ChildItem -LiteralPath $A -Filter 'rb-chain-*' -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^rb-chain-(rb1|rb2|nb)(-verify|-prep|-run)?\.(txt|log)$' })
    Check ($c -eq 2 -and $logs.Count -eq 0) "rb-chain.ps1 $($cs[1]) refused: exit $c (want 2), rb-chain logs $($logs.Count): $(Tail $o 1)"
}
$o = "$L\chain-guard-clean.txt"
& cmd /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File $A\rb-chain.ps1 -Variant nb -GuardOnly > $o 2>&1"
$c = $LASTEXITCODE
Check ($c -eq 0 -and (Tail $o 1) -match '^GUARD OK') "rb-chain.ps1 -GuardOnly with no other driver (its cmd parent names rb-chain.ps1): exit $c (want 0): $(Tail $o 1)"
$fake = Start-Process -FilePath powershell -ArgumentList '-NoProfile -Command Start-Sleep -Seconds 40 # rb-tools-test fake run-rb2.ps1' -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 2
$o = "$L\chain-guard-fake.txt"
& cmd /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File $A\rb-chain.ps1 -Variant nb -GuardOnly > $o 2>&1"
$c = $LASTEXITCODE
Stop-Process -Id $fake.Id -Force -ErrorAction SilentlyContinue
Check ($c -eq 4) "rb-chain.ps1 -GuardOnly with a fake run-rb2.ps1 process (pid $($fake.Id)) refused: exit $c (want 4): $(Tail $o 1)"

# 7. prep clones refuse foreign install trees (exit 1, snapB3 not created)
$inst = "$R\build\agent9\install"
foreach ($cs in @(@('rb1', 'batch'), @('rb2', 'batch'), @('nb', 'batch'), @('rb1', 'batch-nolr'), @('rb2', 'rb1-nolocal'), @('nb', 'rb1-nolocal'))) {
    $o = "$L\prep-$($cs[0])-refuse-$($cs[1]).txt"
    & cmd /d /c "python $A\prep-$($cs[0]).py --install $inst\$($cs[1]) > $o 2>&1"
    $c = $LASTEXITCODE
    Check ($c -eq 1 -and (Tail $o 1) -match 'refusing install tree' -and -not (Test-Path -LiteralPath $snapB3)) "prep-$($cs[0]).py --install install\$($cs[1]) refused: exit $c (want 1), snapB3 not created"
}

# 8. run clones refuse install\batch (exit 3) and a missing prep (exit 2)
foreach ($v in $vs) {
    $o = "$L\run-$v-refuse-batch.txt"
    & cmd /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File $A\run-$v.ps1 -Install build\agent9\install\batch > $o 2>&1"
    $c = $LASTEXITCODE
    Check ($c -eq 3 -and (Tail $o 1) -match 'refusing install tree') "run-$v.ps1 -Install build\agent9\install\batch refused: exit $c (want 3)"
    $o = "$L\run-$v-no-notes.txt"
    & cmd /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File $A\run-$v.ps1 > $o 2>&1"
    $c = $LASTEXITCODE
    Check ($c -eq 2 -and (Tail $o 1) -match 'first') "run-$v.ps1 without prep notes refused: exit $c (want 2): $(Tail $o 1)"
}

# 9. --check-only: step 1 and the snapshot tag pass for all three install trees; nothing copied
foreach ($v in $vs) {
    $o = "$L\prep-$v-check-only.txt"
    & cmd /d /c "python $A\prep-$v.py --check-only > $o 2>&1"
    $c = $LASTEXITCODE
    $last = Tail $o 1
    Check ($c -eq 0 -and $last -match 'DONE --check-only: step 1 passed, snapshot tag S3d;' -and -not (Test-Path -LiteralPath $snapB3)) "prep-$v.py --check-only: exit $c; $($last -replace '^.*?DONE', 'DONE')"
}

# 10. what prep-nb.py copies besides snapB's content: snap1 rexlego/out has no links
$ro = "$A\snap1\DimensionsRecomp\rexlego\out"
$rp = @(Get-ChildItem -LiteralPath $ro -Recurse -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue)
$sz = (Get-ChildItem -LiteralPath $ro -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
Check ((Test-Path -LiteralPath $ro) -and $rp.Count -eq 0) ("snap1 rexlego/out (copied by prep-nb.py): {0} links, {1:N2} GB" -f $rp.Count, ($sz / 1GB))

# the negative tests' own logs (no snapB3 yet, so they are all test output)
if (-not (Test-Path -LiteralPath $snapB3)) {
    foreach ($f in 'snapB3-prep.txt', 'snapB3-run.txt', 'snapB3n-run.txt') {
        if (Test-Path -LiteralPath "$A\$f") { Move-Item -Force -LiteralPath "$A\$f" "$L\test-$f" }
    }
}
Check (-not (Test-Path -LiteralPath $snapB3)) 'snapB3 still does not exist after the tests'
Write-Host "RESULT: $($script:np) PASS / $($script:nf) FAIL"
exit $(if ($script:nf) { 1 } else { 0 })
