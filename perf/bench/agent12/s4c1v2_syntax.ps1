# s4c1v2_syntax.ps1 (Agent 12, run-2 task #13 step 5) - S4 C1 v2 = C1 v1 + gate D's kept-protect counter.
# v2 changes only SDK src/system/xmemory.cpp (no header), so this compiles that one unit twice with the exact
# dev-SDK flags (env\compile-one.ps1 -SyntaxOnly -PrintOnly gives the command):
#   - CONTROL   = C1 v1's new xmemory.cpp (build\agent12\s4-c1v2\v1\sdk, a byte copy of build\agent12\s4-c1\new\sdk);
#   - CANDIDATE = C1 v2's xmemory.cpp (build\agent12\s4-c1v2\new\sdk).
# Both get build\agent12\s4-c1v2\new\sdk\include FIRST on the include path (C1's xmemory.h and shared_memory.h, byte
# copies of v1's), because the live headers lack C1's declarations. The candidate must add no diagnostic.
# Adapted from bench\agent12\s4c1_syntax.ps1; same rules: the PCH is dropped (its header stays force-included as
# plain source), the live file's directory is the LAST include path, single-threaded, one compile at a time,
# writes no objects. Run it at BelowNormal:
#   cmd /c start "" /belownormal /wait /b powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent12\s4c1v2_syntax.ps1
# Output: build\agent12\s4-c1v2\syntax-<stamp>.txt. Exit 0 = both compiles exit 0, every hash matches
# build\agent12\s4-c1v2\HASHES.txt and the candidate has no diagnostic the control doesn't have (nor more of them).
param([string]$Config = 'Release')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent12\s4-c1v2'
$report = Join-Path $stage ("syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
$newInc = Join-Path $stage 'new\sdk\include'
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
$h = @{}
foreach ($l in [IO.File]::ReadAllLines((Join-Path $stage 'HASHES.txt'))) {
    if ($l -match '^(v1|orig|new)\s+([0-9A-F]{64})\s+(\S+)') { $h[$Matches[1] + '|' + $Matches[3]] = $Matches[2] }
}
$rel = 'src/system/xmemory.cpp'
foreach ($k in "v1|$rel", "new|$rel", 'new|include/rex/system/xmemory.h', 'new|include/rex/graphics/shared_memory.h') {
    if (-not $h[$k]) { throw "build\agent12\s4-c1v2\HASHES.txt lacks the $k line" }
}

function Compile([string]$exe, [string]$argStr, [string]$dir) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe; $psi.Arguments = $argStr; $psi.WorkingDirectory = $dir
    $psi.UseShellExecute = $false; $psi.RedirectStandardError = $true; $psi.RedirectStandardOutput = $true
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = [Diagnostics.Process]::Start($psi)
    $e = $p.StandardError.ReadToEndAsync(); $o = $p.StandardOutput.ReadToEndAsync()
    $p.WaitForExit()
    $r = @{ Code = $p.ExitCode; Secs = $sw.Elapsed.TotalSeconds; Diag = ($o.Result + $e.Result) }
    $p.Dispose()
    return $r
}
# diagnostic lines without the file path and line/column numbers, so control and candidate compare
function Diag-Set([string]$d) {
    @($d -split "`r?`n" | Where-Object { $_ -match '(warning|error):' } |
        ForEach-Object { ($_ -replace '^.*?\.(cpp|h|hpp|hxx|inl):\d+:\d+:\s*', '') })
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# s4c1v2_syntax (S4 C1 v2: C1 v1 + the kept-protect counter)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  config $Config")
$lines.Add('# control = build\agent12\s4-c1v2\v1\sdk (C1 v1); candidate = build\agent12\s4-c1v2\new\sdk (C1 v2); both with new\sdk\include first')
$bad = 0
# both compiles see the staged C1 headers (v2 changes no header)
foreach ($hr in 'include/rex/system/xmemory.h', 'include/rex/graphics/shared_memory.h') {
    $nw = Sha (Join-Path $stage ('new\sdk\' + $hr.Replace('/', '\')))
    $ok = ($nw -eq $h['new|' + $hr])
    if (-not $ok) { $bad++ }
    $lines.Add(('header {0,-38} staged {1} ({2})' -f $hr, $nw.Substring(0, 16), $(if ($ok) { '= HASHES new (= C1 v1)' } else { 'MISMATCH' })))
}

$relW = $rel.Replace('/', '\')
$liveRel = 'DimensionsRecomp\rexglue-sdk\' + $relW
$old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$po = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'env\compile-one.ps1') $liveRel -OutDir 'build\agent12\obj' -SyntaxOnly -PrintOnly -Config $Config 2>&1
$poCode = $LASTEXITCODE
$ErrorActionPreference = $old
$po = @($po | ForEach-Object { "$_" })
if ($poCode -ne 0) { $po | ForEach-Object { Write-Host $_ }; throw "compile-one -PrintOnly failed for $liveRel" }
$dir = ($po | Where-Object { $_ -like 'cd *' } | Select-Object -First 1).Substring(3)
$cmd = $po | Where-Object { $_ -notlike 'cd *' -and $_ -notlike 'note:*' -and $_ -notlike 'compile-one:*' -and $_ -match '-fsyntax-only' } | Select-Object -First 1
if (-not $cmd) { $po | ForEach-Object { Write-Host $_ }; throw 'no compiler command in the compile-one -PrintOnly output' }
if ($cmd.StartsWith('"')) { $q = $cmd.IndexOf('"', 1); $exe = $cmd.Substring(1, $q - 1); $args0 = $cmd.Substring($q + 1).Trim() }
else { $sp = $cmd.IndexOf(' '); $exe = $cmd.Substring(0, $sp); $args0 = $cmd.Substring($sp + 1) }
# drop the PCH (keep the force-included PCH header as plain source)
$args0 = [regex]::Replace($args0, '-Xclang -include-pch -Xclang \S+\s*', '')
$livePath = [IO.Path]::GetFullPath((Join-Path $root $liveRel))
# quote includes next to the live file: its directory is the LAST include path
$args0 = $args0.TrimEnd() + ' -I"' + [IO.Path]::GetDirectoryName($livePath) + '"'
$esc = [regex]::Escape($livePath)
if (([regex]::Matches($args0, $esc, 'IgnoreCase')).Count -ne 1) { throw "source path not found exactly once in the command for $rel" }
$ctrl = Join-Path $stage ('v1\sdk\' + $relW); $cand = Join-Path $stage ('new\sdk\' + $relW)
$res = @{}
foreach ($which in 'control', 'candidate') {
    $src = $ctrl; $want = $h["v1|$rel"]
    if ($which -eq 'candidate') { $src = $cand; $want = $h["new|$rel"] }
    $sha = Sha $src
    $hashNote = '= HASHES ' + $(if ($which -eq 'control') { 'v1' } else { 'new' })
    if ($sha -ne $want) { $bad++; $hashNote = 'MISMATCH: want ' + $want.Substring(0, 16) }
    $a = '-I"' + $newInc + '" ' + $args0
    $a = [regex]::Replace($a, $esc, $src.Replace('$', '$$'), 'IgnoreCase')
    $r = Compile $exe $a $dir
    $res[$which] = $r
    $nd = (Diag-Set $r.Diag).Count
    $lines.Add(('{0,-24} {1,-9} exit={2} {3,5:N1}s diagnostics={4}  sha {5} ({6})  {7}' -f $rel, $which, $r.Code, $r.Secs, $nd, $sha.Substring(0, 16), $hashNote, $src))
    if ($r.Code -ne 0) { $bad++ }
    if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add("    | $_") } }
}
$dc = @(Diag-Set $res['control'].Diag); $dn = @(Diag-Set $res['candidate'].Diag)
$new = @($dn | Where-Object { $dc -notcontains $_ })
if ($new.Count) { $bad++; $new | ForEach-Object { $lines.Add("    NEW in candidate: $_") } }
elseif ($dn.Count -gt $dc.Count) { $bad++; $lines.Add("    candidate has more diagnostic lines than its control ($($dn.Count) vs $($dc.Count))") }
else { $lines.Add('    no new diagnostics in the candidate') }
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
