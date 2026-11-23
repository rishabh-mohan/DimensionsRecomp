# Agent 3: early-exit tests of the patched run-timing.ps1 (build\agent3\rtpatch). Every case must stop before
# New-RunDir: no run dir, no game. Fake bin dirs have no MANIFEST.txt, so even a bug could not mirror or launch.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $root
$runner = Join-Path $root 'build\agent3\rtpatch\run-timing.ps1'
$t = 'build\agent3\test'
New-Item -ItemType Directory -Force -Path "$t\fakebin", "$t\fakebin2", "$t\vpadreset" | Out-Null
[IO.File]::WriteAllText((Join-Path $root "$t\fakebin\xinput1_4.dll"), '')
Set-Content -LiteralPath "$t\vpadreset\bad.txt" -Encoding ascii -Value 'bogus 1'
$route = 'harness\routes\attract-long.txt'
$cases = @(
    @{ name = 'T1 missing script'; want = 1; a = @{ BinDir = "$t\fakebin2"; InputScript = "$t\vpadreset\nope.txt" } },
    @{ name = 'T2 bad script'; want = 1; a = @{ BinDir = "$t\fakebin2"; InputScript = "$t\vpadreset\bad.txt" } },
    @{ name = 'T3 bin dir has xinput1_4.dll'; want = 1; a = @{ BinDir = "$t\fakebin"; InputScript = $route } },
    @{ name = 'T4 missing pad DLL'; want = 1; a = @{ BinDir = "$t\fakebin2"; InputScript = $route; VPadDll = "$t\vpadreset\nope.dll" } },
    @{ name = 'T5 valid route -> RAM check'; want = 3; a = @{ BinDir = "$t\fakebin2"; InputScript = $route } },
    @{ name = 'T6 no -InputScript -> RAM check'; want = 3; a = @{ BinDir = "$t\fakebin2" } }
)
foreach ($c in $cases) {
    $a = $c.a + @{ MinFreeRamGB = 999; RunsRoot = "$t\rtruns"; Tag = 'rtpatch-test' }
    $global:LASTEXITCODE = $null
    $out = & $runner @a 2>&1 | Out-String
    $code = $LASTEXITCODE
    "{0}: exit {1} (want {2}) {3} :: {4}" -f $c.name, $code, $c.want, $(if ($code -eq $c.want) { 'PASS' } else { 'FAIL' }), ($out.Trim() -replace '\s*\r?\n\s*', ' | ')
}
"run dirs created: $(if (Test-Path "$t\rtruns") { @(Get-ChildItem "$t\rtruns").Count } else { 0 })"
