# pthrottle_w4b_hash.ps1 - S4 task #24: sha256 of bench\agent8\RUN-WINDOW4B.cmd and everything it
# calls (Agent 8's window-4b closure), so the opt-out pairs can show they changed none of it.
# Read-only: it reads files and writes one TSV (default build\agent11\pthrottle\w4b-hash-<stamp>.tsv).
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_w4b_hash.ps1 [-Out <tsv>] [-Compare <earlier tsv>]
# Closure: RUN-WINDOW4B.cmd; the scripts, matrix, C# and Python files it runs (a fixed list, plus
# script names found in the listed bench\agent8 scripts that exist in bench\agent8\run or drivers);
# harness\legodimensions.toml; every file in build\agent8\cache (compiled helpers); every file in
# the bin dirs matrix-window4.json names. Not hashed: game data (game\disc, game\tu23: read-only).
# -Compare: exit 0 when every file in the earlier TSV is present with the same sha256 (files added
# since are listed, not failed), else exit 1.
[CmdletBinding(PositionalBinding = $false)]
param([string]$Out = '', [string]$Compare = '')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $Out) { $Out = Join-Path $root ('build\agent11\pthrottle\w4b-hash-{0:yyyyMMdd-HHmmss}.tsv' -f (Get-Date)) }
$set = New-Object 'System.Collections.Generic.SortedDictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
function Add-Rel([string]$rel, [string]$why) {
    $full = Join-Path $root $rel
    if ((Test-Path -LiteralPath $full -PathType Leaf) -and -not $set.ContainsKey($rel)) { $set[$rel] = $why; return $true }
    return $false
}
$fixed = 'bench\agent8\RUN-WINDOW4B.cmd',
  'bench\agent8\run\run-matrix.ps1', 'bench\agent8\run\matrix-window4.json', 'bench\agent8\run\common.ps1',
  'bench\agent8\run\timing-env.ps1', 'bench\agent8\run\run-timing.ps1', 'bench\agent8\run\winhelper.cs',
  'bench\agent8\run\frame_summary.py', 'bench\agent8\run\sys_summary.py', 'bench\agent8\run\matrix_recheck.py',
  'bench\agent8\run\first-boot.ps1', 'bench\agent8\run\drivers\sys-csv.ps1', 'bench\agent8\run\drivers\LdSys.cs',
  'bench\agent8\run\drivers\thread-cpu.ps1', 'harness\nvml.cs', 'harness\winhelper.cs', 'harness\legodimensions.toml',
  'DimensionsRecomp\tools\native-cpu\analyze_profile.py'
foreach ($f in $fixed) { $null = Add-Rel $f 'list' }
# scan (one level, not transitive): script names in the listed bench\agent8 files that exist in
# bench\agent8\run or its drivers dir. Files outside the closure are left out on purpose, so an
# owner's unrelated edit (other matrices, harness tools) cannot fail the check.
$dirs = 'bench\agent8\run', 'bench\agent8\run\drivers'
foreach ($k in @($set.Keys)) {
    if ($k -notmatch '^bench\\agent8\\.*\.(ps1|cmd)$') { continue }
    $text = [IO.File]::ReadAllText((Join-Path $root $k))
    foreach ($m in [regex]::Matches($text, '[A-Za-z0-9_][A-Za-z0-9_.-]*\.(ps1|py|cs)\b')) {
        foreach ($d in $dirs) { $null = Add-Rel (Join-Path $d $m.Value) ('scan:' + (Split-Path -Leaf $k)) }
    }
}
$sha = New-Object Security.Cryptography.SHA256CryptoServiceProvider
function Get-Sha([string]$p) {
    $fs = New-Object IO.FileStream($p, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite, 1048576)
    try { return (-join ($sha.ComputeHash($fs) | ForEach-Object { $_.ToString('X2') })) } finally { $fs.Dispose() }
}
foreach ($f in Get-ChildItem -LiteralPath (Join-Path $root 'build\agent8\cache') -File) { $null = Add-Rel ('build\agent8\cache\' + $f.Name) 'cache' }
$mx = Get-Content -Raw -LiteralPath (Join-Path $root 'bench\agent8\run\matrix-window4.json') | ConvertFrom-Json
foreach ($b in @($mx.arms | ForEach-Object { $_.bin } | Sort-Object -Unique)) {
    $bd = $b -replace '/', '\'
    foreach ($f in Get-ChildItem -LiteralPath (Join-Path $root $bd) -File) { $null = Add-Rel ($bd + '\' + $f.Name) 'bin' }
}
$rows = New-Object System.Collections.Generic.List[string]
$now = @{}; $bytes = 0
foreach ($k in $set.Keys) {
    $fi = Get-Item -LiteralPath (Join-Path $root $k)
    $h = Get-Sha $fi.FullName
    $now[$k] = $h; $bytes += $fi.Length
    $rows.Add((@($k, $fi.Length, $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), $h, $set[$k]) -join "`t"))
}
$head = '# pthrottle_w4b_hash {0:yyyy-MM-dd HH:mm:ss}: {1} files, {2} bytes; not hashed: game\disc, game\tu23 (read-only game data)' -f (Get-Date), $set.Count, $bytes
$dir = Split-Path -Parent $Out; if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
Set-Content -LiteralPath $Out -Value (@($head, "# path`tsize`tmtime`tsha256`twhy") + $rows) -Encoding ascii
Write-Host $head
Write-Host "tsv: $Out"
if (-not $Compare) { exit 0 }
$old = @{}
foreach ($l in Get-Content -LiteralPath $Compare) { if ($l -and -not $l.StartsWith('#')) { $c = $l -split "`t"; $old[$c[0]] = $c[3] } }
$bad = 0
foreach ($k in ($old.Keys | Sort-Object)) {
    if (-not $now.ContainsKey($k)) { Write-Host "MISSING  $k"; $bad++ }
    elseif ($now[$k] -ne $old[$k]) { Write-Host "CHANGED  $k (mtime $((Get-Item -LiteralPath (Join-Path $root $k)).LastWriteTime))"; $bad++ }
}
foreach ($k in ($now.Keys | Sort-Object)) { if (-not $old.ContainsKey($k)) { Write-Host "added    $k (info)" } }
Write-Host ("compare with {0}: {1} files before, {2} changed or missing" -f $Compare, $old.Count, $bad)
if ($bad) { exit 1 }
exit 0
