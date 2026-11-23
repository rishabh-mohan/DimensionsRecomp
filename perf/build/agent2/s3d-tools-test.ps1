# Agent 2 - read-only checks of the S3d tool edits (patch-s3d-tools.py on stage-snap-bin.ps1), run-s3d.ps1 and the
# stop-snap.ps1 driver list.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\s3d-tools-test.ps1
$R = '<workspace>'
$A = "$R\build\agent2"
$bad = 0
function T([bool]$ok, [string]$what) { if (-not $ok) { $script:bad++ }; '{0} {1}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $what }
$asts = @{}
foreach ($n in 'stage-snap-bin.ps1', 'run-s3d.ps1', 'stop-snap.ps1', 'build-snap.ps1') {
    $tok = $null; $err = $null
    $asts[$n] = [System.Management.Automation.Language.Parser]::ParseFile("$A\$n", [ref]$tok, [ref]$err)
    T ($err.Count -eq 0) "parse ${n}: $($err.Count) error(s)$(if ($err.Count) { ': ' + $err[0].Message })"
}
# patchTags for each kind of tag
$lines = Get-Content "$A\stage-snap-bin.ps1"
$code = @($lines | Where-Object { $_ -match '^\$(SnapN|SnapBaseN|patchTags) = ' })
T ($code.Count -eq 3) "the SnapN / SnapBaseN / patchTags lines: $($code.Count) of 3"
$want = [ordered]@{ 'S1' = 'S1'; 'S2' = 'S1,S2'; 'S3' = 'S1,S2,S3'; 'S3d' = 'S1,S2,S3,S3d'; 'S4e' = 'S1,S2,S3,S4,S4e'
    'S1x' = 'S1,S1x'; 'S0b' = 'S1,S0b'; 'CHK' = 'S1,CHK' }
foreach ($t in $want.Keys) {
    $SnapTag = $t; $SnapN = $null; $SnapBaseN = $null; $patchTags = $null
    foreach ($c in $code) { Invoke-Expression $c }
    $got = @($patchTags | Select-Object -Unique) -join ','
    T ($got -eq $want[$t]) ("patchTags {0,-4} -> {1}" -f $t, $got)
}
# -CompareWhy: a param with the B default, used by the exe check
$p = @($asts['stage-snap-bin.ps1'].ParamBlock.Parameters | Where-Object { $_.Name.VariablePath.UserPath -eq 'CompareWhy' })
T ($p.Count -eq 1 -and $p[0].DefaultValue.Extent.Text -eq "'the generated code changed'") "param -CompareWhy, default $(if ($p.Count) { $p[0].DefaultValue.Extent.Text } else { 'MISSING' })"
$n = @($lines | Where-Object { $_.Contains('legodimensions.exe differs from the one in $cl ($CompareWhy)') }).Count
T ($n -eq 1) "the -CompareBin exe check uses `$CompareWhy ($n line)"
T (@($lines | Where-Object { $_.Contains('(the generated code changed)"') }).Count -eq 0) 'no hard-coded B wording left in the exe check'
# every '-Name' run-s3d.ps1 passes is a parameter of stage-snap-bin.ps1 or build-snap.ps1
$known = @(foreach ($s in 'stage-snap-bin.ps1', 'build-snap.ps1') { $asts[$s].ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath } })
$used = @([regex]::Matches((Get-Content -Raw "$A\run-s3d.ps1"), "'-([A-Z][A-Za-z]+)'") | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
$unk = @($used | Where-Object { $known -notcontains $_ })
T ($unk.Count -eq 0) "run-s3d.ps1 passes $($used.Count) known parameter names ($($used -join ' '))$(if ($unk.Count) { '; UNKNOWN: ' + ($unk -join ' ') })"
# stop-snap.ps1 matches the run-s3d.ps1 driver, and not the stop script itself
$dl = @(Get-Content "$A\stop-snap.ps1" | Where-Object { $_ -match '^\$drivers = ' })
T ($dl.Count -eq 1) "stop-snap.ps1 has one `$drivers line"
if ($dl.Count -eq 1) {
    Invoke-Expression $dl[0]
    T ('powershell -File build\agent2\run-s3d.ps1' -match $drivers) 'stop-snap.ps1 $drivers matches run-s3d.ps1'
    T ('powershell -File build\agent2\run-s3.ps1 -Stage native' -match $drivers) 'stop-snap.ps1 $drivers still matches run-s3.ps1'
    T (-not ('python build\agent2\prep-s3d.py' -match $drivers)) 'stop-snap.ps1 $drivers does not match prep-s3d.py'
}
if ($bad) { "RESULT: FAIL ($bad)"; exit 1 }
'RESULT: PASS'
exit 0
