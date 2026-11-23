# Agent 10: read-only comparison of the live DimensionsRecomp tree against the S1 manifest.
# Lists CHANGED (content differs from S1), NEW (not in S1) and DELETED (in S1, missing live)
# under the given roots (relative to DimensionsRecomp). Skips .git, generated/, build-output
# directories and reparse points (junctions). Hashes only files whose size/mtime differ from S1
# and new files up to 2 MB. Writes nothing outside $Out.
param([string]$Out = '', [string[]]$Roots = @('rexlego', 'rexglue-sdk', 'tools', 'thirdparty/plume'))
$ErrorActionPreference = 'Continue'
$root = '<workspace>'
$live = Join-Path $root 'DimensionsRecomp'
$manifest = Join-Path $root 'build\agent2\snap1\MANIFEST-S1-2041.tsv'
$map = @{}
foreach ($line in [IO.File]::ReadLines($manifest)) {
    if ($line.StartsWith('#')) { continue }
    $c = $line.Split("`t")
    if ($c.Count -lt 4) { continue }
    $map[$c[0]] = $c
}
$epoch = 621355968000000000L
$skip = @('.git', 'generated', 'out', 'build', 'bin', 'obj', '.vs', 'node_modules', '__pycache__')
$new = New-Object System.Collections.ArrayList
$changed = New-Object System.Collections.ArrayList
$touched = 0
$scanned = 0
$seen = @{}
$prefixes = @()
$stack = New-Object System.Collections.Stack
foreach ($r in $Roots) {
    $p = Join-Path $live ($r.Replace('/', '\'))
    if (Test-Path $p) { $stack.Push($p); $prefixes += ($r.TrimEnd('/') + '/') }
}
$topFiles = [IO.Directory]::GetFiles($live)
function Compare-One([string]$f) {
    $script:scanned++
    $rel = $f.Substring($live.Length + 1).Replace('\', '/')
    $script:seen[$rel] = 1
    $e = $map[$rel]
    $fi = New-Object IO.FileInfo $f
    if (-not $e) {
        $h = if ($fi.Length -le 2MB) { (Get-FileHash $f -Algorithm SHA256).Hash.Substring(0, 8) } else { 'big' }
        [void]$new.Add((@($rel, $h, $fi.Length, $fi.LastWriteTime.ToString('HH:mm:ss')) -join "`t"))
        return
    }
    $ns = ($fi.LastWriteTimeUtc.Ticks - $epoch) * 100
    if ($fi.Length -eq [long]$e[1] -and $ns -eq [long]$e[2]) { return }
    $h = (Get-FileHash $f -Algorithm SHA256).Hash.ToLower()
    if ($h -eq $e[3]) { $script:touched++; return }
    [void]$changed.Add((@($rel, $h.Substring(0, 8).ToUpper(), $e[3].Substring(0, 8).ToUpper(), $fi.LastWriteTime.ToString('HH:mm:ss')) -join "`t"))
}
foreach ($f in $topFiles) { Compare-One $f }
while ($stack.Count) {
    $d = $stack.Pop()
    try { $subs = [IO.Directory]::GetDirectories($d) } catch { continue }
    foreach ($s in $subs) {
        $n = [IO.Path]::GetFileName($s)
        if ($skip -contains $n) { continue }
        if ([IO.File]::GetAttributes($s) -band [IO.FileAttributes]::ReparsePoint) { continue }
        $stack.Push($s)
    }
    foreach ($f in [IO.Directory]::GetFiles($d)) { Compare-One $f }
}
$deleted = @($map.Keys | Where-Object {
        $k = $_
        (-not $seen.ContainsKey($k)) -and (($k -notmatch '/') -or ($prefixes | Where-Object { $k.StartsWith($_) }))
    } | Where-Object { $_ -notmatch '(^|/)(\.git|generated|out|build|bin|obj|\.vs|node_modules|__pycache__)/' } | Sort-Object)
$lines = New-Object System.Collections.ArrayList
[void]$lines.Add("# scan $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') roots=$($Roots -join ',')+top-level files: scanned=$scanned changed=$($changed.Count) new=$($new.Count) deleted=$($deleted.Count) touched-same=$touched")
[void]$lines.Add('## CHANGED (rel, live sha8, S1 sha8, live mtime)')
$changed | Sort-Object | ForEach-Object { [void]$lines.Add($_) }
[void]$lines.Add('## NEW, grouped by first three path parts (rel, sha8, size, mtime); groups over 25 files are counted only')
$groups = $new | Group-Object { ($_.Split("`t")[0].Split('/') | Select-Object -First 3) -join '/' } | Sort-Object Name
foreach ($g in $groups) {
    if ($g.Count -le 25) { $g.Group | Sort-Object | ForEach-Object { [void]$lines.Add($_) } }
    else { [void]$lines.Add("$($g.Name)/... $($g.Count) files") }
}
[void]$lines.Add('## DELETED')
$deleted | Select-Object -First 60 | ForEach-Object { [void]$lines.Add($_) }
if ($Out) { [IO.File]::WriteAllLines($Out, [string[]]$lines) }
$lines
