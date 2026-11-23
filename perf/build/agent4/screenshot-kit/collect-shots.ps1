# build/agent4/screenshot-kit/collect-shots.ps1 - Agent 4, task #29, 2026-11-23.
# After the two kit runs (README.md section 1): copies each run's Win+PrtScn PNGs into shots/, checks both runs and
# writes shots/compare.html (the pairs side by side, or one large image that flips between them on each click).
# Copies only: it never moves or deletes a PNG, never writes into a run dir and starts no game.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent4\screenshot-kit\collect-shots.ps1
#       [-RunsRoot <kit>\runs] [-ShotDir <folder with the PNGs>] [-OutDir <kit>\shots] [-Force] [-DryRun]
# -ShotDir defaults to the Windows Screenshots folder (the Win+PrtScn target). A PNG belongs to the newest sc-ref or
# sc-native run (-DryRun dirs skipped) whose window (launch to launch + elapsed_s + 15 s, cut at the other run's
# launch) holds its LastWriteTime. Names: S<k>-<arm>-ff<sss>.png when the run has exactly 5 shots, else
# <arm>-<nn>-ff<sss>.png, where sss = whole seconds after that run's first frame (input.csv "mark first-frame").
# A run is OK when run-game.ps1 would exit 0 for it, it ran on your desktop, and the virtual pad connected (no route
# timeout, the game loaded the pad DLL and read a pressed button).
# Exit: 0 both runs OK with 5 shots each; 1 incomplete (a run missing or failed, or not 5 shots); 2 bad arguments, or
# shots/ already holds PNGs (move them away or pass -Force).
# LOCAL ONLY: the shots show game assets. Never commit or export shots/ or runs/.
param(
    [string]$RunsRoot = '',
    [string]$ShotDir = '',
    [string]$OutDir = '',
    [switch]$Force,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$inv = [Globalization.CultureInfo]::InvariantCulture
if (-not $RunsRoot) { $RunsRoot = Join-Path $PSScriptRoot 'runs' }
if (-not $OutDir) { $OutDir = Join-Path $PSScriptRoot 'shots' }
if (-not $ShotDir) {
    $usf = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders' -ErrorAction SilentlyContinue
    $reg = $null
    if ($usf) { $reg = $usf.PSObject.Properties['{B7BEDE81-DF94-4682-A7D8-57A52620B86F}'] }
    if ($reg -and $reg.Value) { $ShotDir = [Environment]::ExpandEnvironmentVariables([string]$reg.Value) }
    else { $ShotDir = Join-Path ([Environment]::GetFolderPath('MyPictures')) 'Screenshots' }
}
if (-not (Test-Path -LiteralPath $ShotDir -PathType Container)) { Write-Host "no screenshot folder '$ShotDir' (pass -ShotDir)"; exit 2 }
if (-not (Test-Path -LiteralPath $RunsRoot -PathType Container)) { Write-Host "no runs folder '$RunsRoot' (pass -RunsRoot)"; exit 2 }
if (-not $DryRun -and -not $Force -and (Test-Path -LiteralPath $OutDir)) {
    $old = @(Get-ChildItem -LiteralPath $OutDir -File -Filter '*.png')
    if ($old.Count) { Write-Host "$OutDir already holds $($old.Count) PNGs: move them away or pass -Force"; exit 2 }
}

function Prop($o, [string]$n) { $p = $o.PSObject.Properties[$n]; if ($p) { $p.Value } else { $null } }

function Get-KitRun([string]$Tag, [string]$Arm) {
    $r = [pscustomobject]@{ Tag = $Tag; Arm = $Arm; Name = ''; Ok = $false; Note = ''; Start = $null; End = $null; FF = $null; Shots = @() }
    # The newest run dir first. -DryRun dirs (run.json mode 'DRY RUN, not launched', no start time) are skipped.
    $dirs = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | Where-Object { $_.Name -like "*-$Tag" } | Sort-Object Name -Descending)
    $d = $null; $rj = $null; $dry = 0
    foreach ($c in $dirs) {
        $p = Join-Path $c.FullName 'run.json'
        if (-not (Test-Path -LiteralPath $p)) { $d = $c; break }
        $j = Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
        if ([string](Prop $j 'mode') -like 'DRY RUN*') { $dry++; continue }
        $d = $c; $rj = $j; break
    }
    if ($null -eq $d) { $r.Note = "no run dir *-$Tag"; if ($dry) { $r.Note += " (only $dry dry runs)" }; return $r }
    $r.Name = $d.Name
    if ($null -eq $rj) { $r.Note = 'no run.json (still running, or stopped by hand?)'; return $r }
    $s = Prop $rj 'started'
    if (-not $s) { $r.Note = 'run.json has no start time'; return $r }
    if ($s -is [datetime]) { $r.Start = $s } else { $r.Start = ([datetimeoffset]::Parse([string]$s, $inv)).LocalDateTime }
    $el = Prop $rj 'elapsed_s'
    if ($null -eq $el) { $el = 420 }
    $r.End = $r.Start.AddSeconds([double]$el + 15)
    $ic = Join-Path $d.FullName 'input.csv'
    if (Test-Path -LiteralPath $ic) {
        $row = @(Import-Csv -LiteralPath $ic | Where-Object { $_.cmd -eq 'mark' -and $_.args -eq 'first-frame' }) | Select-Object -First 1
        if ($row) { $r.FF = [double]::Parse($row.t_s, $inv) }
    }
    $problems = @()
    # Same rule as run-game.ps1's own exit code: a crash report, a dump, or an early exit with a nonzero code fails the
    # run. The game's exit code after the timer's close (wm_close; -1 when killed) doesn't matter.
    $code = Prop $rj 'exit_code'
    $early = [bool](Prop $rj 'exited_early')
    if ($early -and $code -ne 0) { $problems += "the game quit early with exit code $code" }
    if (Prop $rj 'wer_seen') { $problems += 'crash report (WER) seen' }
    $crash = @(Prop $rj 'crash_events' | Where-Object { $_ }).Count + @(Prop $rj 'dumps' | Where-Object { $_ }).Count
    if ($crash) { $problems += "$crash crash events or dumps" }
    # The virtual pad (run.json input_script, from vpadhost.cs Finish): without it there is no menu and no attract, and a
    # timed-out wait_first_frame writes the first-frame mark late, so every ff number would be wrong.
    $pad = Prop $rj 'input_script'
    if ($null -eq $pad) { $problems += 'no virtual pad (run without -InputScript)' }
    else {
        if (Prop $pad 'timeouts') { $problems += "the pad route timed out (route line $(Prop $pad 'timeout_lines')), so the first-frame time is wrong" }
        $er = Prop $pad 'error'
        if ($er) { $problems += "pad route error: $er" }
        if (-not (Prop $pad 'dll_loaded_by_pid')) { $problems += 'the game never loaded the virtual pad' }
        elseif (-not (Prop $pad 'pad_active_reads')) { $problems += 'the game never read a pressed pad button' }
    }
    if ($null -eq $r.FF) { $problems += 'no first-frame mark in input.csv' }
    $mode = [string](Prop $rj 'mode')
    if ($mode -ne 'FUNCTIONAL (interactive desktop)') { $problems += "mode '$mode' (not your desktop)" }
    $r.Ok = ($problems.Count -eq 0)
    if ($problems.Count) { $r.Note = $problems -join '; ' }
    elseif ($early) { $r.Note = 'OK, interactive desktop (the game closed before the timer, exit code 0)' }
    else { $r.Note = 'OK, interactive desktop' }
    return $r
}

$runs = @((Get-KitRun 'sc-ref' 'ref'), (Get-KitRun 'sc-native' 'native'))
$timed = @($runs | Where-Object { $null -ne $_.Start } | Sort-Object Start)
for ($i = 0; $i -lt $timed.Count - 1; $i++) {
    if ($timed[$i].End -gt $timed[$i + 1].Start) { $timed[$i].End = $timed[$i + 1].Start }
}
$pngs = @(Get-ChildItem -LiteralPath $ShotDir -File -Filter '*.png' | Where-Object { $_.Extension -eq '.png' })
$plan = @()
foreach ($r in $runs) {
    if ($null -eq $r.Start) { continue }
    $r.Shots = @($pngs | Where-Object { $_.LastWriteTime -ge $r.Start -and $_.LastWriteTime -lt $r.End } | Sort-Object LastWriteTime)
    $n = $r.Shots.Count
    for ($i = 0; $i -lt $n; $i++) {
        $f = $r.Shots[$i]
        $ff = 'ff-na'
        if ($null -ne $r.FF) { $ff = 'ff' + ([int][math]::Round(($f.LastWriteTime - $r.Start).TotalSeconds - $r.FF)).ToString('000', $inv) }
        if ($n -eq 5) { $name = 'S{0}-{1}-{2}.png' -f ($i + 1), $r.Arm, $ff } else { $name = '{0}-{1}-{2}.png' -f $r.Arm, ($i + 1).ToString('00', $inv), $ff }
        $plan += [pscustomobject]@{ Arm = $r.Arm; Src = $f.FullName; SrcName = $f.Name; Time = $f.LastWriteTime; Name = $name }
    }
}

foreach ($r in $runs) { Write-Host ('{0,-7} {1,-36} {2} shots; {3}' -f $r.Arm, $(if ($r.Name) { $r.Name } else { '-' }), $r.Shots.Count, $r.Note) }
foreach ($p in $plan) { Write-Host ('        {0,-26} <- {1} ({2})' -f $p.Name, $p.SrcName, $p.Time.ToString('HH:mm:ss', $inv)) }
$complete = (@($runs | Where-Object { -not $_.Ok -or $_.Shots.Count -ne 5 }).Count -eq 0)

if ($DryRun) {
    Write-Host 'DRY RUN: nothing copied, nothing written.'
} else {
    if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
    foreach ($p in $plan) { Copy-Item -LiteralPath $p.Src -Destination (Join-Path $OutDir $p.Name) -Force }
    function Esc([string]$s) { [System.Net.WebUtility]::HtmlEncode($s) }
    function Cell($p, [string]$cls, [string]$label) {
        if ($null -eq $p) { return "<figure class=`"$cls`"><div class=`"none`">no $label shot</div><figcaption>${label}: none</figcaption></figure>" }
        $n = Esc $p.Name
        return "<figure class=`"$cls`"><img src=`"$n`" alt=`"$label $n`"><figcaption>${label}: $n</figcaption></figure>"
    }
    $refs = @($plan | Where-Object { $_.Arm -eq 'ref' })
    $nats = @($plan | Where-Object { $_.Arm -eq 'native' })
    $rows = [math]::Max($refs.Count, $nats.Count)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append(@'
<!doctype html>
<html><head><meta charset="utf-8"><title>Screenshot kit: reference vs native</title>
<style>
body{font:14px sans-serif;margin:12px;background:#1e1e1e;color:#ddd}
h3{margin:18px 0 6px 0}
button{margin-left:12px}
.row{display:flex;gap:6px}
figure{flex:1;margin:0}
img{width:100%;display:block}
figcaption{color:#aaa;padding:2px 0}
.none{padding:40px;border:1px dashed #666;color:#888;text-align:center}
.flip figure.nat{display:none}
.flip.shownat figure.ref{display:none}
.flip.shownat figure.nat{display:block}
.flip img{cursor:pointer}
</style></head><body>
<p><b>Local only:</b> these images show game assets. Never commit or export them.</p>
<p>Left: reference, the standard GPU path (devoff4-bin). Right: native (native4-bin). "flip view" shows one large image; click it to switch between reference and native. Mark each pair SAME, MISSING or OTHER (README.md section 3).</p>

'@)
    for ($i = 0; $i -lt $rows; $i++) {
        if ($refs.Count -eq 5 -and $nats.Count -eq 5) { $label = "S$($i + 1)" } else { $label = "pair $($i + 1)" }
        $a = $null; if ($i -lt $refs.Count) { $a = $refs[$i] }
        $b = $null; if ($i -lt $nats.Count) { $b = $nats[$i] }
        [void]$sb.Append("<div class=`"pair`"><h3>$label<button type=`"button`" onclick=`"mode(this)`">flip view</button></h3>`n")
        [void]$sb.Append("<div class=`"row`">$(Cell $a 'ref' 'reference')$(Cell $b 'nat' 'native')</div></div>`n")
    }
    if ($rows -eq 0) { [void]$sb.Append("<p>No shots were found in the run windows.</p>`n") }
    [void]$sb.Append(@'
<script>
function mode(b){var p=b.parentNode.parentNode;var on=p.classList.toggle('flip');p.classList.remove('shownat');b.textContent=on?'side by side':'flip view';}
document.addEventListener('click',function(e){var t=e.target;if(t.tagName!=='IMG')return;var p=t.parentNode.parentNode.parentNode;if(p.classList.contains('flip'))p.classList.toggle('shownat');});
</script>
</body></html>

'@)
    $html = $sb.ToString().Replace("`r`n", "`n")
    [IO.File]::WriteAllText((Join-Path $OutDir 'compare.html'), $html, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "copied $($plan.Count) PNGs to $OutDir; open $(Join-Path $OutDir 'compare.html')"
}
if ($complete) { Write-Host 'COMPLETE: both runs OK, 5 shots each.'; exit 0 }
Write-Host 'INCOMPLETE: see the lines above (a run missing or failed, or not 5 shots in a run). Pair the shots by hand.'
exit 1
