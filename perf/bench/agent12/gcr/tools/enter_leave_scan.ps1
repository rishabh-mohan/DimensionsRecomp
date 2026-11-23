# Agent 12 / J3 (checklist C9, hazards H5 H10): static scan of the generated guest
# code for the interrupt-lock macros (REX_ENTER/LEAVE/CHECK_GLOBAL_LOCK).
# Per function (DEFINE_REX_FUNC) it counts ENTER/LEAVE/CHECK and, for each
# ENTER..LEAVE region in *linear text order* (an approximation of control flow),
# what happens while G is held: calls (bl / bctrl / blrl), returns (blr),
# lwarx/stwcx. pairs and the region length. Prints only statistics and a few
# function names; it writes nothing derived from the game except these counts.
#
# Usage (workspace root): powershell -File bench\agent12\gcr\tools\enter_leave_scan.ps1
param(
    [string]$Root = 'DimensionsRecomp\rexlego\generated',
    [string]$Out = 'build\agent12\gcr\enter_leave_scan.log'
)
$ErrorActionPreference = 'Stop'
$files = @(Get-ChildItem $Root -Recurse -Filter *.cpp |
    Select-String -Pattern 'REX_ENTER_GLOBAL_LOCK|REX_LEAVE_GLOBAL_LOCK' -List |
    Select-Object -ExpandProperty Path)

$funcs = New-Object System.Collections.Generic.List[object]
$sections = New-Object System.Collections.Generic.List[object]
$fnRe = [regex]'^DEFINE_REX_FUNC\((\w+)\)'
$impRe = [regex]'^\s*(__imp__\w+)\(ctx, base\);'
$subRe = [regex]'^\s*(sub_[0-9A-Fa-f]+)\(ctx, base\);'

foreach ($f in $files) {
    $cur = $null
    $sec = $null
    foreach ($line in [IO.File]::ReadLines($f)) {
        $m = $fnRe.Match($line)
        if ($m.Success) {
            if ($sec) { $sec.Unterminated = $true; $sections.Add($sec); $sec = $null }
            if ($cur -and ($cur.Enter + $cur.Leave + $cur.Check) -gt 0) { $funcs.Add($cur) }
            $cur = [pscustomobject]@{ Name = $m.Groups[1].Value; File = (Split-Path $f -Leaf); Enter = 0; Leave = 0; Check = 0 }
            continue
        }
        if (-not $cur) { continue }
        if ($line.Contains('REX_ENTER_GLOBAL_LOCK()')) {
            $cur.Enter++
            if ($sec) { $sec.NestedEnter++ } else {
                $sec = [pscustomobject]@{ Func = $cur.Name; Lines = 0; Bl = 0; Bctrl = 0; Blr = 0; Lwarx = 0; Stwcx = 0; NestedEnter = 0; Unterminated = $false; Imps = @(); Subs = @() }
            }
            continue
        }
        if ($line.Contains('REX_LEAVE_GLOBAL_LOCK()')) {
            $cur.Leave++
            if ($sec) { $sections.Add($sec); $sec = $null }
            continue
        }
        if ($line.Contains('REX_CHECK_GLOBAL_LOCK()')) { $cur.Check++ }
        if ($sec) {
            $sec.Lines++
            $t = $line.TrimStart()
            if ($t.StartsWith('// bl ') -or $t.StartsWith('// bla ')) { $sec.Bl++ }
            elseif ($t.StartsWith('// bctrl') -or $t.StartsWith('// blrl') -or $t.StartsWith('// bcctrl')) { $sec.Bctrl++ }
            elseif ($t -eq '// blr' -or $t.StartsWith('// blr ') -or $t.StartsWith('// beqlr') -or $t.StartsWith('// bnelr')) { $sec.Blr++ }
            elseif ($t.StartsWith('// lwarx') -or $t.StartsWith('// ldarx')) { $sec.Lwarx++ }
            elseif ($t.StartsWith('// stwcx.') -or $t.StartsWith('// stdcx.')) { $sec.Stwcx++ }
            $mi = $impRe.Match($line); if ($mi.Success) { $sec.Imps += $mi.Groups[1].Value }
            $ms = $subRe.Match($line); if ($ms.Success) { $sec.Subs += $ms.Groups[1].Value }
        }
    }
    if ($sec) { $sec.Unterminated = $true; $sections.Add($sec) }
    if ($cur -and ($cur.Enter + $cur.Leave + $cur.Check) -gt 0) { $funcs.Add($cur) }
}

$o = New-Object System.Collections.Generic.List[string]
$o.Add("enter_leave_scan: $($files.Count) files with ENTER/LEAVE under $Root")
$tE = ($funcs | Measure-Object Enter -Sum).Sum; $tL = ($funcs | Measure-Object Leave -Sum).Sum; $tC = ($funcs | Measure-Object Check -Sum).Sum
$o.Add("macro totals: ENTER=$tE LEAVE=$tL CHECK=$tC in $($funcs.Count) functions")
$withE = @($funcs | Where-Object Enter -gt 0)
$leaveNoEnter = @($funcs | Where-Object { $_.Leave -gt 0 -and $_.Enter -eq 0 })
$enterNoLeave = @($funcs | Where-Object { $_.Enter -gt 0 -and $_.Leave -eq 0 })
$checkOnly = @($funcs | Where-Object { $_.Check -gt 0 -and $_.Enter -eq 0 -and $_.Leave -eq 0 })
$o.Add("functions with ENTER: $($withE.Count); LEAVE but no ENTER: $($leaveNoEnter.Count); ENTER but no LEAVE: $($enterNoLeave.Count); CHECK only: $($checkOnly.Count)")
if ($leaveNoEnter.Count) { $o.Add("  LEAVE-without-ENTER examples: " + (($leaveNoEnter | Select-Object -First 5 | ForEach-Object { "$($_.Name)(L=$($_.Leave),C=$($_.Check))" }) -join ', ')) }
if ($enterNoLeave.Count) { $o.Add("  ENTER-without-LEAVE examples: " + (($enterNoLeave | Select-Object -First 5 | ForEach-Object { "$($_.Name)(E=$($_.Enter))" }) -join ', ')) }
$o.Add("ENTER..LEAVE regions (linear order): $($sections.Count)")
$atomic = @($sections | Where-Object { $_.Lwarx -gt 0 -and $_.Bl -eq 0 -and $_.Bctrl -eq 0 })
$calls = @($sections | Where-Object { $_.Bl -gt 0 -or $_.Bctrl -gt 0 })
$rets = @($sections | Where-Object { $_.Blr -gt 0 })
$unterm = @($sections | Where-Object Unterminated)
$nested = @($sections | Where-Object { $_.NestedEnter -gt 0 })
$plain = @($sections | Where-Object { $_.Lwarx -eq 0 -and $_.Bl -eq 0 -and $_.Bctrl -eq 0 })
$o.Add("  lwarx/stwcx. only (no calls): $($atomic.Count); with calls (bl/bctrl): $($calls.Count); no atomics and no calls: $($plain.Count)")
$o.Add("  containing a return (blr) before LEAVE: $($rets.Count); unterminated at function end: $($unterm.Count); with a nested ENTER: $($nested.Count)")
$len = @($sections | ForEach-Object Lines | Sort-Object)
if ($len.Count) { $o.Add("  region length in generated lines: median=$($len[[int]($len.Count/2)]) max=$($len[-1])") }
if ($calls.Count) {
    $imps = @($calls | ForEach-Object { $_.Imps } | Group-Object | Sort-Object Count -Descending | ForEach-Object { "$($_.Name) x$($_.Count)" })
    $subs = @($calls | ForEach-Object { $_.Subs } | Sort-Object -Unique)
    $o.Add("  kernel imports called while G is held: " + ($(if ($imps.Count) { $imps -join ', ' } else { 'none' })))
    $o.Add("  guest functions called while G is held: $($subs.Count) distinct (first 5: " + (($subs | Select-Object -First 5) -join ', ') + ")")
    $o.Add("  regions with calls, by function (first 8): " + (($calls | Select-Object -First 8 | ForEach-Object { "$($_.Func)[bl=$($_.Bl),bctrl=$($_.Bctrl),lines=$($_.Lines)]" }) -join ' '))
}
if ($rets.Count) { $o.Add("  regions with blr, by function (first 8): " + (($rets | Select-Object -First 8 | ForEach-Object { "$($_.Func)[lines=$($_.Lines)]" }) -join ' ')) }
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$o | Set-Content $Out
$o
