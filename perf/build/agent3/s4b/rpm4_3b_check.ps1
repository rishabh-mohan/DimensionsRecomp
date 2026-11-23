# rpm4_3b_check.ps1 - Agent 3, task #23: the REPIN.md section 3b checks of the native4b re-pin matrix (rpm4).
# Read-only on the run dirs. Usage (from the repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\s4b\rpm4_3b_check.ps1 *> build\agent3\s4b\logs\rpm4.3b.txt
# Pass needs: logdiff n0old -> n0 NEW 0 / MORE 0 (beside the Native GPU [fp] line and the P2c suffix); no C1 keep-watch,
# d3d12_submit_split, deferred_counters or GPU wait back-off line on any arm; n0 draws p10/p50/p90 = n0old's; a clean
# WM_CLOSE on all 4 runs; n2 has 'Native draw batches: parallel workers=2' and no hash=0 line; n3 has no
# 'Native draw batches' line and no hash=0 line; check_n_rows.py --baseline n0 --rows n2 n3 exits 0.
param([string]$Out = 'build\agent3\runs\rpm4-20261123-0620', [string]$MatrixLog = 'build\agent3\s4b\logs\rpm4.run-matrix.txt')
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$runs = Join-Path $Out 'runs'
function D([string]$arm) { $d = Get-ChildItem -LiteralPath $runs -Directory | Where-Object { $_.Name -match "^\d{4}-$arm-r1$" } | Select-Object -First 1; if ($d) { $d.FullName.Replace((Get-Location).Path + '\', '') } else { '' } }
$a = [ordered]@{ n0old = (D 'n0old'); n0 = (D 'n0'); n2 = (D 'n2'); n3 = (D 'n3') }
foreach ($k in $a.Keys) { "arm $k : $($a[$k])" }

'=== (1) logdiff n0old -> n0'
& python -B build\agent10\bgate\logdiff.py --base $a.n0old --cand $a.n0
"logdiff exit $LASTEXITCODE"

'=== (2) per arm: forbidden families, Native draw batches, hash=0, Native GPU [fp]'
$forbid = 'C1 keep-watch|d3d12_submit_split|deferred_counters|GPU wait back-off'
foreach ($k in $a.Keys) {
    $logs = @(Get-ChildItem -LiteralPath $a[$k] -Recurse -File -Filter '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.Length -lt 200MB })
    "--- $k : logs scanned: " + (@($logs | ForEach-Object { "$($_.FullName.Replace((Resolve-Path $a[$k]).Path + '\', '')) ($($_.Length) B)" }) -join ', ')
    $f = @($logs | Select-String -Pattern $forbid)
    "  forbidden-family lines: $($f.Count)"; $f | Select-Object -First 3 | ForEach-Object { '    ' + $_.Line.Trim() }
    $nb = @($logs | Select-String -Pattern 'Native draw batches')
    "  'Native draw batches' lines: $($nb.Count)"; $nb | Select-Object -First 3 | ForEach-Object { '    ' + $_.Line.Trim() }
    $h0 = @($logs | Select-String -Pattern 'hash=0\b')
    "  hash=0 lines: $($h0.Count)"; $h0 | Select-Object -First 2 | ForEach-Object { '    ' + $_.Line.Trim() }
    $fp = @($logs | Select-String -Pattern 'Native GPU \[fp\]|fingerprint')
    "  Native GPU [fp]/fingerprint lines: $($fp.Count)"; $fp | Select-Object -First 2 | ForEach-Object { '    ' + $_.Line.Trim() }
}

'=== (3) draws per arm (summary.md lines with draw; else the native-frames.csv header)'
foreach ($k in $a.Keys) {
    $s = @(Get-ChildItem -LiteralPath $a[$k] -Recurse -File -Filter 'summary.md' -ErrorAction SilentlyContinue)
    $dl = @($s | Select-String -Pattern 'draw')
    "--- $k : summary.md files $($s.Count), draw lines $($dl.Count)"
    $dl | Select-Object -First 6 | ForEach-Object { '    ' + $_.Line.Trim() }
    if (-not $dl.Count) {
        $nf = Get-ChildItem -LiteralPath $a[$k] -Recurse -File -Filter 'native-frames.csv' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($nf) { '    native-frames.csv header: ' + (Get-Content -LiteralPath $nf.FullName -TotalCount 1) }
    }
}
$ms = Join-Path $Out 'summary.md'
if (Test-Path -LiteralPath $ms) { '--- matrix summary.md draw lines:'; Select-String -LiteralPath $ms -Pattern 'draw' | Select-Object -First 12 | ForEach-Object { '    ' + $_.Line.Trim() } }

'=== (4) close lines and per-run verdicts from the run-matrix log'
Select-String -LiteralPath $MatrixLog -Pattern '^close |^--> ' | ForEach-Object { '  ' + $_.Line.Trim() }

'=== (5) check_n_rows n0 -> n2, n3'
& python -B bench\agent4\check_n_rows.py --baseline $a.n0 --rows "n2=$($a.n2)" "n3=$($a.n3)"
"check_n_rows exit $LASTEXITCODE"
'=== end'
