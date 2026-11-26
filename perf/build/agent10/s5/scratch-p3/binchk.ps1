$ErrorActionPreference = 'Stop'
$b = '<workspace>\build'
function ManMap($dir) {
    $m = @{}
    foreach ($l in Get-Content (Join-Path $dir 'MANIFEST.txt')) {
        if ($l -match '^#' -or -not $l.Trim()) { continue }
        $p = $l -split "`t"
        if ($p.Count -ge 4) { $m[$p[0]] = @{ size = [int64]$p[1]; sha = $p[3] } }
    }
    $m
}
$pairs = @(
    @{ new = "$b\agent2\s5\devs5toml-bin"; base = "$b\agent2\devfinal2-bin"; dll = "$b\agent2\s5\rt-bin\b-toml\rt\link-on\rexruntime.dll" },
    @{ new = "$b\agent2\s5\natives5fsr1-bin"; base = "$b\agent2\nativefinal2-bin"; dll = "$b\agent2\s5\rt-bin\b-fsr1\rt\link-on\rexruntime.dll" }
)
foreach ($p in $pairs) {
    "== $(Split-Path $p.new -Leaf) MANIFEST $((Get-FileHash "$($p.new)\MANIFEST.txt").Hash.Substring(0,8)) vs base $(Split-Path $p.base -Leaf) $((Get-FileHash "$($p.base)\MANIFEST.txt").Hash.Substring(0,8))"
    $own = ManMap $p.new; $bm = ManMap $p.base
    $nf = @(Get-ChildItem $p.new -File | ? Name -ne 'MANIFEST.txt' | % Name | Sort-Object)
    $bf = @(Get-ChildItem $p.base -File | ? Name -ne 'MANIFEST.txt' | % Name | Sort-Object)
    "fileset new=$($nf.Count) base=$($bf.Count) same=$((Compare-Object $nf $bf).Count -eq 0) manifest-entries=$($own.Count) base-entries=$($bm.Count)"
    foreach ($f in $nf) {
        $h = (Get-FileHash (Join-Path $p.new $f)).Hash
        $okOwn = $own.ContainsKey($f) -and $own[$f].sha -eq $h
        $eqBase = $bm.ContainsKey($f) -and $bm[$f].sha -eq $h
        '{0,-26} {1} own={2} ==base={3}' -f $f, $h.Substring(0,8), $okOwn, $eqBase
    }
    "link-on dll $((Get-FileHash $p.dll).Hash.Substring(0,8)) base rexruntime manifest $($bm['rexruntime.dll'].sha.Substring(0,8))"
}
"== pinned bins (MANIFEST sha, newest file mtime, size/rexruntime vs MANIFEST)"
foreach ($d in 'agent2\devfinal2-bin','agent2\nativefinal2-bin','agent16\pack\native4bp-bin','agent2\s5\devs5nops-bin','agent2\native4b-bin','agent2\devoff4b-bin','agent2\devoff4b-cg26-bin','agent2\s5\devs5sync-bin') {
    $dir = "$b\$d"; $m = ManMap $dir
    $files = @(Get-ChildItem $dir -File)
    $newest = ($files | Sort-Object LastWriteTime | Select-Object -Last 1)
    $sizeBad = @($files | ? { $_.Name -ne 'MANIFEST.txt' -and (-not $m.ContainsKey($_.Name) -or $m[$_.Name].size -ne $_.Length) }).Count
    $rr = Join-Path $dir 'rexruntime.dll'; $rrOk = (Get-FileHash $rr).Hash -eq $m['rexruntime.dll'].sha
    $gx = Join-Path $dir 'rexgpu-xenos.dll'; $gxOk = (Get-FileHash $gx).Hash -eq $m['rexgpu-xenos.dll'].sha
    '{0,-28} MAN {1} newest {2:MM-dd HH:mm} ({3}) sizeBad={4} rexruntime={5} rexgpu={6} files={7}' -f $d, (Get-FileHash "$dir\MANIFEST.txt").Hash.Substring(0,8), $newest.LastWriteTime, $newest.Name, $sizeBad, $rrOk, $gxOk, ($files.Count-1)
}
