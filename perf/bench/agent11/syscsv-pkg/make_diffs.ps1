# make_diffs.ps1 - Agent 11, 2026-11-22. Writes the adoption diffs for the staged package-power
# sampler columns into this folder:
#   LdSys.cs.diff        Agent 8's bench/agent8/run/drivers/LdSys.cs  (the change itself)
#   sys_summary.py.diff  Agent 8's bench/agent8/run/sys_summary.py    (1 line: header_ok allows extra columns)
#   sys-csv.ps1.diff     reference only: the staged copy's path changes, NOT for adoption
# The two adoption diffs get Agent 8's path on both header sides, so `git apply <diff>` from the
# repo root patches Agent 8's file. Each is then checked with `git apply --check` (read-only).
# Nothing outside this folder is written. Exit 0 = all diffs written and both checks pass.
# ASCII only, PowerShell 5.1.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location -LiteralPath $repo
$pairs = @(
  , @('bench/agent8/run/drivers/LdSys.cs', 'bench/agent11/syscsv-pkg/LdSys.cs', 'LdSys.cs.diff', $true)
)
$pairs += , @('bench/agent8/run/sys_summary.py', 'bench/agent11/syscsv-pkg/sys_summary.py', 'sys_summary.py.diff', $true)
$pairs += , @('bench/agent8/run/drivers/sys-csv.ps1', 'bench/agent11/syscsv-pkg/sys-csv.ps1', 'sys-csv.ps1.diff', $false)
$rc = 0
foreach ($p in $pairs) {
  $orig = $p[0]; $staged = $p[1]; $out = Join-Path $PSScriptRoot $p[2]; $adopt = [bool]$p[3]
  $ErrorActionPreference = 'Continue'
  $lines = @(& git -c core.autocrlf=false diff --no-index --no-color -- $orig $staged)
  $ErrorActionPreference = 'Stop'
  if ($lines.Count -eq 0) { "{0}: NO DIFF (files equal?)" -f $p[2]; $rc = 1; continue }
  if ($adopt) {
    $lines = @($lines | ForEach-Object {
        if ($_.StartsWith('diff --git ') -or $_.StartsWith('+++ ')) { $_.Replace('b/' + $staged, 'b/' + $orig) } else { $_ }
      })
  }
  $txt = ($lines -join "`n") + "`n"
  [IO.File]::WriteAllText($out, $txt, (New-Object System.Text.UTF8Encoding($false)))
  $plus = @($lines | Where-Object { $_.StartsWith('+') -and -not $_.StartsWith('+++ ') }).Count
  $minus = @($lines | Where-Object { $_.StartsWith('-') -and -not $_.StartsWith('--- ') }).Count
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $h = ([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($out))) -replace '-', '')
  $check = 'n/a (reference only)'
  if ($adopt) {
    $ErrorActionPreference = 'Continue'
    $chk = @(& git -c core.autocrlf=false apply --check $out 2>&1)
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -eq 0) { $check = 'git apply --check PASS' } else { $check = 'git apply --check FAIL: ' + (($chk | ForEach-Object { "$_" }) -join ' / '); $rc = 1 }
  }
  "{0}: {1} lines, +{2}/-{3}, sha256 {4}; {5}" -f $p[2], $lines.Count, $plus, $minus, $h, $check
}
exit $rc
