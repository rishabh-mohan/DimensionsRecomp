# s4m1_syntax.ps1 (Agent 5) - S4 M1 (shared_memory_upload_nontemporal_copy, default OFF). clang -fsyntax-only of
# d3d12/shared_memory.cpp with the exact dev-SDK flags (env\compile-one.ps1 -SyntaxOnly -PrintOnly gives the command),
# once for the control copy (build\agent5\s4-m1\base = live + #7, the file the M1 diff applies to) and once for the
# candidate (the staged copy build\agent5\s4-m1\new = base + M1, or the live tree with -Live), so the two diagnostic
# outputs can be compared: M1 must add no diagnostic. Adapted from bench\agent12\s4diag_syntax.ps1; same rules.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent5\s4m1_syntax.ps1         # staged copy
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent5\s4m1_syntax.ps1 -Live   # live tree (after #7 + M1)
# The precompiled header is always dropped (its header stays force-included as plain source). All includes of
# shared_memory.cpp are <...> through include paths, so a copy elsewhere compiles the same. Each compiled file must
# match build\agent5\s4-m1\HASHES.txt (control = base, candidate = staged), so -Live fails unless the live file is
# exactly base + M1. Single-threaded, one compile at a time, writes no objects.
# Output: build\agent5\s4-m1\syntax-<stamp>.txt. Exit 0 = both compiles exit 0, both hashes match and the candidate
# has no diagnostic line the control copy doesn't have.
param([switch]$Live, [string]$Config = 'Release')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent5\s4-m1'
$report = Join-Path $stage ("syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
$name = 'shared_memory.cpp'
$liveRel = 'DimensionsRecomp\rexglue-sdk\src\graphics\d3d12\shared_memory.cpp'
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
$h = @{}
foreach ($l in [IO.File]::ReadAllLines((Join-Path $stage 'HASHES.txt'))) {
    if ($l -match '^(orig|diff7|base|diff|staged)\s+([0-9A-F]{64})\b') { $h[$Matches[1]] = $Matches[2] }
}
if (-not $h['base'] -or -not $h['staged']) { throw 'build\agent5\s4-m1\HASHES.txt lacks the base/staged lines' }

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
$lines.Add("# s4m1_syntax (S4 M1: shared_memory_upload_nontemporal_copy, default OFF)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  config $Config  candidate: $(if ($Live) { 'live tree' } else { 'staged copy' })")
$bad = 0
$old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$po = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'env\compile-one.ps1') $liveRel -OutDir 'build\agent5\obj' -SyntaxOnly -PrintOnly -Config $Config 2>&1
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
$control = Join-Path $stage "base\$name"
$cand = Join-Path $stage "new\$name"; if ($Live) { $cand = $livePath }
$esc = [regex]::Escape($livePath)
if (([regex]::Matches($args0, $esc, 'IgnoreCase')).Count -ne 1) { throw "source path not found exactly once in the command for $name" }
$res = @{}
foreach ($which in 'control', 'candidate') {
    $src = $control; $key = 'base'
    if ($which -eq 'candidate') { $src = $cand; $key = 'staged' }
    $sha = Sha $src
    $hashNote = "= HASHES $key"
    if ($sha -ne $h[$key]) { $bad++; $hashNote = "MISMATCH: HASHES $key is $($h[$key].Substring(0, 16))" }
    $a = [regex]::Replace($args0, $esc, $src.Replace('$', '$$'), 'IgnoreCase')
    $r = Compile $exe $a $dir
    $res[$which] = $r
    $nd = (Diag-Set $r.Diag).Count
    $lines.Add(('{0,-18} {1,-9} exit={2} {3,5:N1}s diagnostics={4}  sha {5} ({6})  {7}' -f $name, $which, $r.Code, $r.Secs, $nd, $sha.Substring(0, 16), $hashNote, $src))
    if ($r.Code -ne 0) { $bad++ }
    if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add("    | $_") } }
}
$new = @(Diag-Set $res['candidate'].Diag | Where-Object { (Diag-Set $res['control'].Diag) -notcontains $_ })
if ($new.Count) { $bad++; $new | ForEach-Object { $lines.Add("    NEW in candidate: $_") } }
else { $lines.Add('    no new diagnostics in the candidate') }
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
