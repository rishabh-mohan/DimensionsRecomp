# make-run-day.ps1: makes run-day.ps1 (Agent 5's day launcher) from bench\agent5\launch\run-night.ps1, which must have
# sha256 565D30D4... (the reviewed night launcher 16B90FA8 plus the SCRNSAVE.EXE fix, build\agent5\scrnsave-fix). Each change replaces text that must occur in exactly one line, or
# inserts one line after a line that must be unique; every changed line ends in '# DAY:'. Nothing else differs.
# It also parse-checks the result and writes run-day.diff (git diff --no-index). It writes only next to itself.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File make-run-day.ps1
param([string]$Source = '')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
if (-not $Source) { $Source = Join-Path $Repo 'bench\agent5\launch\run-night.ps1' }
$Want = '565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112'
$Out = Join-Path $PSScriptRoot 'run-day.ps1'
$DiffFile = Join-Path $PSScriptRoot 'run-day.diff'
$h = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
if ($h -ne $Want) { throw "source $Source has sha256 $h, not $Want; refusing" }
$text = [IO.File]::ReadAllText($Source)
if ($text.Contains("`r")) { throw 'the source has CR characters (expected LF only)' }
if ($text.Contains('# DAY:')) { throw "the source already contains '# DAY:'" }
$L = New-Object System.Collections.Generic.List[string]
$L.AddRange([string[]]($text -split "`n"))
$n0 = $L.Count
$script:Changes = 0

function Find-One([string]$Sub) {
    $ix = @(); for ($i = 0; $i -lt $L.Count; $i++) { if ($L[$i].Contains($Sub)) { $ix += $i } }
    if ($ix.Count -ne 1) { throw "expected exactly one line containing [$Sub], found $($ix.Count)" }
    return $ix[0]
}
function Set-Sub([string]$Old, [string]$New, [string]$Why) {
    $i = Find-One $Old
    $L[$i] = $L[$i].Replace($Old, $New) + "   # DAY: $Why"
    $script:Changes++; Write-Host "line $($i + 1) changed: $Why"
}
function Add-After([string]$Anchor, [string]$New, [string]$Why) {
    $i = Find-One $Anchor
    $L.Insert($i + 1, $New + "   # DAY: $Why")
    $script:Changes++; Write-Host "line $($i + 2) inserted: $Why"
}

# 1. header
$o = @'
# run-night.ps1: Agent 5's overnight launcher (task #4, old #27). Plain description: README.md next to this file.
'@
$n = @'
# run-day.ps1: Agent 5's day launcher, made from run-night.ps1 (sha 565D30D4) by make-run-day.ps1; changed lines end in '# DAY:'. -StopAt is required; in the comments below, 07:30 means the -StopAt time. Plain description: README-DAY.md.
'@
Set-Sub $o $n 'header'

# 2. -StopAt is no longer a dry-run-only hook
$o = @'
'StrictMinutes', 'StopAt', 'MatrixDir'
'@
$n = @'
'StrictMinutes', 'MatrixDir'
'@
Set-Sub $o $n '-StopAt is the day session end here, not a test hook'

# 3. ... and it is required
$o = @'
only work together with -DryRun" -ForegroundColor Red; exit 2 }
'@
$n = @'
if ($StopAt -notmatch '^(\d{4}-\d\d-\d\d )?\d\d:\d\d$') { Write-Host "refused: run-day.ps1 needs -StopAt 'HH:mm' or 'yyyy-MM-dd HH:mm' (RUN-DAY.cmd sets it from your return time)" -ForegroundColor Red; exit 2 }
'@
Add-After $o $n '-StopAt is required'

# 4. pin RUN-DAY.cmd instead of RUN-NIGHT.cmd
$o = @'
$f.Add((Join-Path $PSScriptRoot 'RUN-NIGHT.cmd'))
'@
$n = @'
$f.Add((Join-Path $PSScriptRoot 'RUN-DAY.cmd'))
'@
Set-Sub $o $n 'pins RUN-DAY.cmd'

# 5. the HOLD text names the day launcher
$o = @'
by Agent 5's overnight launcher (bench\agent5\launch\run-night.ps1), pid
'@
$n = @'
by Agent 5's day launcher ($PSCommandPath), pid
'@
Set-Sub $o $n 'HOLD names the day launcher'

# 6. the 14 h start check message
$o = @'
more than $MaxRunHours h from now (it is past 07:30): start it in the evening
'@
$n = @'
more than $MaxRunHours h from now: -StopAt must be less than $MaxRunHours h away
'@
Set-Sub $o $n 'message'

# 7. the start-refusal message points to README-DAY.md
$o = @'
Nothing was changed. README.md explains the start checks.
'@
$n = @'
Nothing was changed. README-DAY.md explains the start checks.
'@
Set-Sub $o $n 'message'

$outText = $L -join "`n"
foreach ($c in $outText.ToCharArray()) { if ([int]$c -gt 126 -or ([int]$c -lt 32 -and [int]$c -ne 10 -and [int]$c -ne 9)) { throw "non-ASCII or control character $([int]$c) in the output" } }
$marks = @($L | Where-Object { $_.Contains('# DAY:') }).Count
if ($script:Changes -ne 7 -or $marks -ne 7 -or $L.Count -ne $n0 + 1) { throw "check failed: changes $($script:Changes), '# DAY:' lines $marks, lines $($L.Count) (source $n0)" }
[IO.File]::WriteAllText($Out, $outText, (New-Object Text.ASCIIEncoding))
$tk = $null; $pe = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($Out, [ref]$tk, [ref]$pe)
if (@($pe).Count) { throw "run-day.ps1 has parse errors: $((@($pe) | ForEach-Object { "line $($_.Extent.StartLineNumber): $($_.Message)" }) -join '; ')" }
$ErrorActionPreference = 'Continue'
# Paths relative to $Repo, so the diff names no user folder (Agent 10's N1); a path outside $Repo stays as it is.
$rel = @(foreach ($p in $Source, $Out) { $f = (Resolve-Path -LiteralPath $p).Path; if ($f.StartsWith($Repo + '\', [StringComparison]::OrdinalIgnoreCase)) { $f.Substring($Repo.Length + 1).Replace('\', '/') } else { $f } })
Push-Location -LiteralPath $Repo
try { $d = @(& git -c core.autocrlf=false diff --no-index --no-color -- $rel[0] $rel[1] | ForEach-Object { [string]$_ }) } finally { Pop-Location }
$ErrorActionPreference = 'Stop'
[IO.File]::WriteAllText($DiffFile, (($d -join "`n") + "`n"), (New-Object Text.ASCIIEncoding))
Write-Host "run-day.ps1: $($L.Count) lines, $marks '# DAY:' lines, parse OK, sha256 $((Get-FileHash -LiteralPath $Out -Algorithm SHA256).Hash)"
Write-Host "run-day.diff: $($d.Count) lines, sha256 $((Get-FileHash -LiteralPath $DiffFile -Algorithm SHA256).Hash)"
