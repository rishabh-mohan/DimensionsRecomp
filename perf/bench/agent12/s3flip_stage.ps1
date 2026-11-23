<#
.SYNOPSIS
  s3flip_stage.ps1 (Agent 12) -- S3 flip: audio_shutdown_detach_worker default false -> true
  (DimensionsRecomp/rexglue-sdk/src/audio/audio_system.cpp:48, one token in the REXCVAR_DEFINE_BOOL).

  (no switch)  Stage. Refuses unless live = the file reviewed for #22 (C281FA86...). Copies live to
               build\agent12\s3flip\pristine\audio_system.cpp, writes the flipped copy to
               build\agent12\s3flip\audio_system.cpp (BOM and line endings preserved), the diff (read-only
               "git diff --no-index", headers rewritten to the repo path) to
               build\agent12\s3flip\audio-default-on.diff, and HASHES.txt. Writes nothing in the source tree.
  -Check       Print the hashes. Exit 0 = live is pristine, 3 = live is the staged file, 1 = anything else.
  -Apply       Write the staged bytes over live. Refuses unless live = pristine and both copies match
               HASHES.txt. The write gives live a fresh mtime (Copy-Item would keep the staging time, and
               ninja could then skip the rebuild if an object was built after staging).
  -Revert      Write the pristine bytes back over live. Refuses unless live = staged. Fresh mtime too.
  Written for Windows PowerShell 5.1.
#>
param([switch]$Check, [switch]$Apply, [switch]$Revert)
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$liveRel = 'DimensionsRecomp/rexglue-sdk/src/audio/audio_system.cpp'
$stageRel = 'build/agent12/s3flip'
$prRel = "$stageRel/pristine/audio_system.cpp"
$stRel = "$stageRel/audio_system.cpp"
$live = [IO.Path]::GetFullPath((Join-Path $Root $liveRel))
$stage = [IO.Path]::GetFullPath((Join-Path $Root $stageRel))
$pr = [IO.Path]::GetFullPath((Join-Path $Root $prRel))
$st = [IO.Path]::GetFullPath((Join-Path $Root $stRel))
$diffPath = Join-Path $stage 'audio-default-on.diff'
$hashFile = Join-Path $stage 'HASHES.txt'
$reviewed = 'C281FA8625435EFE352DD4E62043837063BA84D523831ED629A994759A861260'
$old = '    audio_shutdown_detach_worker, false, "Audio",'
$new = '    audio_shutdown_detach_worker, true, "Audio",'
$expectLine = 48

function Sha([string]$p) { return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function MTime([string]$p) { return (Get-Item -LiteralPath $p).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') }
function Read-Hashes {
    if (-not (Test-Path -LiteralPath $hashFile)) { throw "no $hashFile; run without switches to stage first" }
    $h = @{}
    foreach ($l in [IO.File]::ReadAllLines($hashFile)) {
        if ($l -match '^(pristine|staged|diff)\s+([0-9A-F]{64})\b') { $h[$Matches[1]] = $Matches[2] }
    }
    foreach ($k in 'pristine', 'staged', 'diff') { if (-not $h.ContainsKey($k)) { throw "HASHES.txt has no '$k' line" } }
    return $h
}
function Write-Fresh([string]$from, [string]$to) {
    # Rewrites the existing file in place, so it gets a fresh mtime (unlike Copy-Item).
    [IO.File]::WriteAllBytes($to, [IO.File]::ReadAllBytes($from))
    (Get-Item -LiteralPath $to).LastWriteTime = Get-Date
}

$nModes = 0
foreach ($s in @($Check.IsPresent, $Apply.IsPresent, $Revert.IsPresent)) { if ($s) { $nModes++ } }
if ($nModes -gt 1) { throw 'use at most one of -Check, -Apply, -Revert' }

if ($Check) {
    $h = Read-Hashes
    $l = Sha $live
    Write-Host ('live     {0}  {1}  mtime {2}' -f $l, $liveRel, (MTime $live))
    Write-Host ('pristine {0}  {1}' -f (Sha $pr), $prRel)
    Write-Host ('staged   {0}  {1}' -f (Sha $st), $stRel)
    Write-Host ('HASHES   pristine {0}  staged {1}  diff {2}' -f $h['pristine'], $h['staged'], $h['diff'])
    if ($l -eq $h['pristine']) { Write-Host 'live = PRISTINE (flip not applied)'; exit 0 }
    if ($l -eq $h['staged']) { Write-Host 'live = STAGED (flip applied)'; exit 3 }
    Write-Host 'live = OTHER (neither pristine nor staged)'
    exit 1
}

if ($Apply) {
    $h = Read-Hashes
    $l = Sha $live
    if ($l -ne $h['pristine']) { throw "live $liveRel is $l, not pristine $($h['pristine']); refusing (see -Check)" }
    if ((Sha $pr) -ne $h['pristine']) { throw "pristine copy $prRel changed since staging; refusing" }
    if ((Sha $st) -ne $h['staged']) { throw "staged copy $stRel changed since staging; refusing" }
    Write-Fresh $st $live
    $after = Sha $live
    if ($after -ne $h['staged']) { throw "after apply live is $after, expected $($h['staged'])" }
    Write-Host ('APPLIED {0}: {1} -> {2} (mtime {3})' -f $liveRel, $h['pristine'], $after, (MTime $live))
    exit 0
}

if ($Revert) {
    $h = Read-Hashes
    $l = Sha $live
    if ($l -ne $h['staged']) { throw "live $liveRel is $l, not the staged $($h['staged']); refusing (see -Check)" }
    if ((Sha $pr) -ne $h['pristine']) { throw "pristine copy $prRel changed since staging; refusing" }
    Write-Fresh $pr $live
    $after = Sha $live
    if ($after -ne $h['pristine']) { throw "after revert live is $after, expected $($h['pristine'])" }
    Write-Host ('REVERTED {0} to pristine {1} (mtime {2})' -f $liveRel, $after, (MTime $live))
    exit 0
}

# ---- Stage ----
$script:fails = 0
function Report([bool]$ok, [string]$what) {
    if ($ok) { Write-Host "PASS  $what" } else { Write-Host "FAIL  $what"; $script:fails++ }
}
$liveMtime = MTime $live
$l = Sha $live
if ($l -ne $reviewed) { throw "live $liveRel is $l, not the file reviewed for #22 ($reviewed); refusing to stage" }
Report $true ('live {0} = reviewed #22 file {1}' -f $liveRel, $reviewed.Substring(0, 8))
New-Item -ItemType Directory -Force -Path (Split-Path $pr) | Out-Null
if (Test-Path -LiteralPath $pr) {
    if ((Sha $pr) -ne $l) { throw "existing pristine copy $prRel differs from live; delete $stageRel to re-stage deliberately" }
} else {
    Copy-Item -LiteralPath $live -Destination $pr
}
Report ((Sha $pr) -eq $l) "pristine copy $prRel = live"

$a = [IO.File]::ReadAllBytes($pr)
$bomA = ($a.Length -ge 3 -and $a[0] -eq 0xEF -and $a[1] -eq 0xBB -and $a[2] -eq 0xBF)
$text = [IO.File]::ReadAllText($pr)
$n = ([regex]::Matches($text, [regex]::Escape($old))).Count
if ($n -ne 1) { throw "edit target found $n times (need exactly 1): $old" }
[IO.File]::WriteAllText($st, $text.Replace($old, $new), (New-Object Text.UTF8Encoding($bomA)))
$b = [IO.File]::ReadAllBytes($st)
$bomB = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
Report ($bomA -eq $bomB) ('BOM unchanged ({0})' -f $(if ($bomA) { 'BOM' } else { 'no BOM' }))
$crA = 0; foreach ($x in $a) { if ($x -eq 13) { $crA++ } }
$crB = 0; foreach ($x in $b) { if ($x -eq 13) { $crB++ } }
Report ($crA -eq $crB) ('CR count unchanged ({0})' -f $crA)
Report ($b.Length -eq ($a.Length - 1)) ('size {0} -> {1} bytes (expect -1)' -f $a.Length, $b.Length)
$i = 0; while ($i -lt $b.Length -and $a[$i] -eq $b[$i]) { $i++ }
$j = 0; while ($j -lt ($b.Length - $i) -and $a[$a.Length - 1 - $j] -eq $b[$b.Length - 1 - $j]) { $j++ }
$lenA = $a.Length - $j - $i; $lenB = $b.Length - $j - $i
$regA = ''; $regB = ''
if ($lenA -ge 0 -and $lenB -ge 0) {
    $regA = [Text.Encoding]::ASCII.GetString($a, $i, $lenA); $regB = [Text.Encoding]::ASCII.GetString($b, $i, $lenB)
}
$lf = 0; for ($k = 0; $k -lt $i; $k++) { if ($a[$k] -eq 10) { $lf++ } }
Report (($lf + 1) -eq $expectLine -and $regA -eq 'fals' -and $regB -eq 'tru') ('only bytes that differ: "{0}" -> "{1}" on line {2} (false -> true)' -f $regA, $regB, ($lf + 1))
$la = [IO.File]::ReadAllLines($pr); $lb = [IO.File]::ReadAllLines($st)
$diffIdx = @(); for ($k = 0; $k -lt [Math]::Min($la.Count, $lb.Count); $k++) { if ($la[$k] -ne $lb[$k]) { $diffIdx += ($k + 1) } }
Report (($la.Count -eq $lb.Count) -and ($diffIdx.Count -eq 1) -and ($diffIdx[0] -eq $expectLine) -and ($la[$expectLine - 1] -eq $old) -and ($lb[$expectLine - 1] -eq $new)) ('line count {0} = {1}; only line {2} differs' -f $la.Count, $lb.Count, ($diffIdx -join ','))

$tmp = Join-Path $stage 'audio-default-on.diff.tmp'
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp }
Push-Location $Root
try {
    $ErrorActionPreference = 'Continue'
    & git --no-optional-locks diff --no-index --no-color --src-prefix=a/ --dst-prefix=b/ "--output=$tmp" -- $prRel $stRel 2>&1 | Out-Null
    $gitRc = $LASTEXITCODE
} finally { $ErrorActionPreference = 'Stop'; Pop-Location }
if (-not (Test-Path -LiteralPath $tmp)) { throw "git diff produced no output (rc $gitRc)" }
$d = [IO.File]::ReadAllText($tmp)
Remove-Item -LiteralPath $tmp
$d = $d.Replace("a/$prRel", "a/$liveRel").Replace("b/$stRel", "b/$liveRel")
[IO.File]::WriteAllText($diffPath, $d, (New-Object Text.UTF8Encoding($false)))
$dl = $d -split "`n"
$minus = @($dl | Where-Object { $_.StartsWith('-') -and -not $_.StartsWith('---') })
$plus = @($dl | Where-Object { $_.StartsWith('+') -and -not $_.StartsWith('+++') })
$hunks = @($dl | Where-Object { $_.StartsWith('@@') })
Report (($minus.Count -eq 1) -and ($plus.Count -eq 1) -and ($hunks.Count -eq 1)) ('diff has -1/+1 lines in 1 hunk (got -{0}/+{1}, {2} hunks)' -f $minus.Count, $plus.Count, $hunks.Count)
Report (($minus.Count -eq 1) -and ($minus[0] -eq "-$old") -and ($plus.Count -eq 1) -and ($plus[0] -eq "+$new")) 'diff -/+ lines are exactly the old/new cvar line'
Report ($d.Contains("--- a/$liveRel") -and $d.Contains("+++ b/$liveRel") -and -not $d.Contains($stageRel)) "diff headers name $liveRel only"
Report (((Sha $live) -eq $reviewed) -and ((MTime $live) -eq $liveMtime)) 'live file untouched by staging (hash and mtime)'

$hp = Sha $pr; $hs = Sha $st; $hd = Sha $diffPath
[IO.File]::WriteAllLines($hashFile, @(
    ('pristine {0}  {1} as reviewed for #22 (copy: {2})' -f $hp, $liveRel, $prRel),
    ('staged {0}  {1} (line {2}: false -> true)' -f $hs, $stRel, $expectLine),
    ('diff {0}  {1}/audio-default-on.diff' -f $hd, $stageRel),
    ('staged-at {0}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
))
Write-Host ('staged {0}: pristine {1} -> staged {2}; diff {3}' -f $liveRel, $hp, $hs, $hd)
Write-Host ('wrote {0} and {1}; {2} FAIL' -f $hashFile, $diffPath, $script:fails)
if ($script:fails -gt 0) { exit 1 }
exit 0
