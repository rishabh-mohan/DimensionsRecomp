# manual-capture.ps1 - M2's matched manual capture for one arm of `RUN-RT-SMOKE.cmd noshots arms=F3A,F3B`
# (M10 rt-noshots-rating 7AFF48CC, N2-N5). Uses computer-cli screenshot / zoom / windows ONLY (N3): no focus, click,
# key, type, scroll or mouse. Timing from build\agent2\s5\rt-mark.ps1 (read-only). Output: rt-smoke\manual\<stamp>-<arm>\
#   powershell -File manual-capture.ps1 -Arm F3A      (start it once the arm's game is up, or just before)
param([Parameter(Mandatory)][ValidateSet('F3A', 'F3B')][string]$Arm,
      [double[]]$Times = @(60, 62, 122.25, 146.75, 201.5), [double]$ZoomLead = 0.35, [double]$CheckLead = 1.3)
$ErrorActionPreference = 'Stop'
$s5 = '<workspace>\build\agent2\s5'
$cli = 'C:\Users\<user>\.vscode\projects\agy-grid\src\computer-cli.js'
$mark = Join-Path $s5 'rt-mark.ps1'
$region = @(266, 172, 1099, 660); $wantW = 1366; $wantH = 800
$out = Join-Path $s5 ("rt-smoke\manual\{0}-{1}" -f (Get-Date -Format yyyyMMdd-HHmmss), $Arm.ToLower())
New-Item -ItemType Directory -Force -Path $out | Out-Null
$log = Join-Path $out 'capture-log.txt'
function Say([string]$s) { $l = "[cap $Arm $(Get-Date -Format HH:mm:ss.f)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l -Encoding utf8 }
function CompCli([string[]]$a) { $o = & node $cli @a 2>&1 | Out-String; if ($LASTEXITCODE -ne 0) { throw "computer-cli $($a -join ' '): $o" }; $o | ConvertFrom-Json }
function Mark([double]$t, [double]$lead) { $o = & powershell -NoProfile -ExecutionPolicy Bypass -File $mark -Until $t -Lead $lead 2>&1 | Out-String; @{ rc = $LASTEXITCODE; o = $o.Trim() } }
Add-Type -AssemblyName System.Drawing
function NonBlack([string]$p) {   # share of pixels with R+G+B > 24 (as the kit's pixel gate), sampled every 4th pixel
    $b = [Drawing.Bitmap]::FromFile($p); try { $n = 0; $k = 0
        for ($y = 0; $y -lt $b.Height; $y += 4) { for ($x = 0; $x -lt $b.Width; $x += 4) { $c = $b.GetPixel($x, $y); $k++; if ($c.R + $c.G + $c.B -gt 24) { $n++ } } }
        @{ w = $b.Width; h = $b.Height; nb = $n / [Math]::Max(1, $k) } } finally { $b.Dispose() } }

# N2: the real-run log must say the kit takes no shots before any capture
$rl = Get-ChildItem (Join-Path $s5 'rt-smoke\logs') -Filter 'rt-smoke-run-2*.txt' | Sort-Object LastWriteTime | Select-Object -Last 1
if (-not $rl -or -not (Select-String -LiteralPath $rl.FullName -SimpleMatch -Quiet -Pattern 'shots NONE (noshots: manual capture)')) { Say "N2 FAIL: newest real-run log $($rl.Name) lacks 'shots NONE (noshots: manual capture)': no captures"; exit 4 }
Say "N2 OK: $($rl.Name) has 'shots NONE (noshots: manual capture)'"
$sched = & powershell -NoProfile -ExecutionPolicy Bypass -File $mark 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { Say "rt-mark: $($sched.Trim())"; exit 2 }
Say ("schedule:`n" + $sched.TrimEnd())
$gpid = [int]([regex]::Match($sched, 'pid (\d+)').Groups[1].Value)

# one full screenshot at ~50 s (title screen; local only, N4) so the helper knows the screen size before the zooms
$m = Mark 50 0.3
if ($m.rc -ne 0) { Say "50 s mark: $($m.o); taking the screenshot now" }
$r = CompCli @('screenshot'); Copy-Item -LiteralPath $r.path -Destination (Join-Path $out 'desktop-LOCAL-ONLY.png'); Say "screenshot $($r.width)x$($r.height) scale $($r.scale) -> desktop-LOCAL-ONLY.png ($($m.o))"

$first = $true
foreach ($t in $Times) {
    $m = Mark $t $CheckLead
    if ($m.rc -ne 0) { Say "T=$t s skipped: $($m.o)"; continue }
    $w = CompCli @('windows')
    $ws = @($w.windows)
    $gi = -1; for ($i = 0; $i -lt $ws.Count; $i++) { if ($ws[$i].pid -eq $gpid) { $gi = $i; break } }
    $g = if ($gi -ge 0) { $ws[$gi] } else { $null }
    $above = if ($gi -gt 0) { ($ws[0..($gi - 1)] | ForEach-Object { "'$($_.title)' ($($_.process))" }) -join ', ' } else { '' }
    if (-not $g -or -not $g.focused -or $g.minimized) { Say "T=$t s SKIPPED (N3): game window $(if ($g) { "focused=$($g.focused) minimized=$($g.minimized)" } else { 'not listed' }); front: '$($ws[0].title)' ($($ws[0].process))"; continue }
    $m = Mark $t $ZoomLead
    if ($m.rc -ne 0) { Say "T=$t s skipped (late): $($m.o)"; continue }
    $r = CompCli (@('zoom') + ($region | ForEach-Object { "$_" }))
    $f = Join-Path $out ("zoom-{0}s.png" -f ("$t".Replace('.', '_')))
    Copy-Item -LiteralPath $r.path -Destination $f
    $px = NonBlack $f
    Say ("T=$t s zoom -> $(Split-Path -Leaf $f) {0}x{1} non-black {2:P1} ({3}); windows above the game: [{4}]" -f $px.w, $px.h, $px.nb, $m.o, $above)
    if ($first -and $Arm -eq 'F3A') {   # N5: the first F3A capture must be 1:1 and not black
        $first = $false
        if ($px.w -ne $wantW -or $px.h -ne $wantH -or $px.nb -lt 0.02) { Say "N5 STOP: first F3A capture is $($px.w)x$($px.h) (want ${wantW}x${wantH}), non-black $('{0:P1}' -f $px.nb): no further captures"; exit 5 }
        Say 'N5 OK: first F3A capture is 1:1 and not black'
    }
    $first = $false
}
Say "done; files in $out"
exit 0
