# syntax_check_s4c.ps1 (Agent 9, run-2 task #22) - #24 S4c package: clang -fsyntax-only of the staged
# rexlego/src/gpu_wait_backoff.cpp (must hash to the rated draft 01D9F8F3) with the S4a devoff4 flags
# (build\agent2\snap1-off\compile_commands.json: the snap1 tree + the snap1-sdk install). A parameterised copy of
# ..\syntax_check.ps1 (task #11: devoffB flags, PASS 13:24); the logic is the same:
#   control   = snap1's rexlego src/native_lock_elide.cpp with its own command (it calls std::getenv too, :42).
#   candidate = a hash-checked copy of the staged file in place of the control's source in the same command:
#               (a) -DLEGO_GPU_WAIT_HOOK_GETDATA=1 (what the S4c CMake block sets: Xenos build, H0-H3) and
#               (b) without it (H0/H1: the native-by-mistake case).
#   positive control: -E of each variant must define exactly the expected hooks in the candidate file (a 4, b 2),
#               so a PASS cannot come from an empty TU or from a define that did not take.
#   lint (-Lint only; informational, never fails): the control and both variants again with -Wall -Wextra.
# One compile at a time, single-threaded, writes no objects, no ninja. Run it at BelowNormal:
#   cmd /c start "" /belownormal /wait /b powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\s4\fence-wait\s4c\syntax_check_s4c.ps1
# Output: syntax-<stamp>.txt beside this script. Exit 0 = the staged file hashes to the record, every compile exits 0,
# the hooks are as expected and no candidate diagnostic text is missing from the control. Extra repeats of a control
# text fail too, except the getenv deprecation warning (EXPECTED: the file calls std::getenv 3 times, the control once).
param(
    [string]$Draft = 'build\agent9\s4\fence-wait\s4c\new\rexlego\src\gpu_wait_backoff.cpp',
    [string]$WantSha = '01D9F8F3464C861401C3BE98F797938619C5DD85B1AEA166B6D9CED053FA19DD',
    [string]$CompileCommands = 'build\agent2\snap1-off\compile_commands.json',
    [string]$Pch = 'build\agent2\snap1\DimensionsRecomp\rexlego\generated\default\legodimensions_pch.h',
    [string]$Label = 'S4a devoff4 flags, snap1-off',
    [switch]$Lint
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
Set-Location $root
$here = $PSScriptRoot
$work = Join-Path $here 'syntax'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$report = Join-Path $here ("syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Run([string]$exe, [string]$argStr, [string]$dir) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe; $psi.Arguments = $argStr; $psi.WorkingDirectory = $dir
    $psi.UseShellExecute = $false; $psi.RedirectStandardError = $true; $psi.RedirectStandardOutput = $true
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = [Diagnostics.Process]::Start($psi)
    $e = $p.StandardError.ReadToEndAsync(); $o = $p.StandardOutput.ReadToEndAsync()
    $p.WaitForExit()
    $r = @{ Code = $p.ExitCode; Secs = $sw.Elapsed.TotalSeconds; Out = $o.Result; Err = $e.Result }
    $p.Dispose()
    return $r
}
# diagnostic lines without the file path and line/column numbers, so control and candidate compare
function Diag-Set([string]$d) {
    @($d -split "`r?`n" | Where-Object { $_ -match '(warning|error):' } | ForEach-Object { ($_ -replace '^.*?:\d+:\d+:\s*', '') })
}
# names of the functions `void sub_XXXXXXXX(...)` defined on lines that -E attributes to the candidate file
function Hook-Defs([string]$pp, [string]$leaf) {
    $cur = ''; $names = New-Object System.Collections.Generic.List[string]
    foreach ($l in ($pp -split "`n")) {
        if ($l.StartsWith('#')) { if ($l -match '^#\s*(?:line\s+)?\d+\s+"([^"]*)"') { $cur = $Matches[1] }; continue }
        if ($cur.EndsWith($leaf, [StringComparison]::OrdinalIgnoreCase) -and $l -match '\bvoid\s+(sub_[0-9A-Fa-f]{8})\s*\(') { $names.Add($Matches[1]) }
    }
    return , $names
}
function Short([string]$s) { $s.Replace($root + '\', '').Replace($root.Replace('\', '/') + '/', '') }

$lines = New-Object System.Collections.Generic.List[string]
$bad = 0
$lines.Add("# syntax_check_s4c (#24 S4c package: staged gpu_wait_backoff.cpp vs $Label)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")

$ccPath = Join-Path $root $CompileCommands
$cc = [IO.File]::ReadAllText($ccPath) | ConvertFrom-Json
$ent = @($cc | Where-Object { $_.file -match 'rexlego[\\/]+src[\\/]+native_lock_elide\.cpp$' })
if ($ent.Count -ne 1) { throw "native_lock_elide.cpp: $($ent.Count) entries in $ccPath" }
$cmd = [string]$ent[0].command
if (-not $cmd) { throw 'the native_lock_elide.cpp entry has no "command" field' }
if ($cmd.StartsWith('"')) { $q = $cmd.IndexOf('"', 1); $exe = $cmd.Substring(1, $q - 1); $rest = $cmd.Substring($q + 1).Trim() }
else { $sp = $cmd.IndexOf(' '); $exe = $cmd.Substring(0, $sp); $rest = $cmd.Substring($sp + 1) }
$m = [regex]::Match($rest, '\s-o\s+(\S+)\s+-c\s+(\S+)\s*$')
if (-not $m.Success) { throw 'the command does not end in "-o <obj> -c <src>"' }
$ctrlSrc = [IO.Path]::GetFullPath($m.Groups[2].Value)
$baseArgs = $rest.Substring(0, $m.Index).Trim()
$lines.Add("compile_commands: $(Short $ccPath) ($($cc.Count) entries, sha $((Sha $ccPath).Substring(0, 16))), entry dir $(Short ([string]$ent[0].directory))")
$lines.Add("command (control; '-o <obj> -c <src>' replaced): $(Short $exe) $(Short $baseArgs) [-D...] -fsyntax-only <src>")
$ver = Run $exe '--version' $work
$lines.Add('clang: ' + (($ver.Out -split "`r?`n")[0]))

# hashes: control source vs live, the pch, the staged file and its copy
$liveCtrl = Join-Path $root 'DimensionsRecomp\rexlego\src\native_lock_elide.cpp'
$cs = Sha $ctrlSrc; $ls = Sha $liveCtrl
$lines.Add(('control  {0}  sha {1}  live {2} ({3})' -f (Short $ctrlSrc), $cs.Substring(0, 16), $ls.Substring(0, 16), $(if ($cs -eq $ls) { 'same' } else { 'DIFFERENT (info)' })))
$pchFull = Join-Path $root $Pch
if (Test-Path -LiteralPath $pchFull) { $lines.Add(('pch      {0}  sha {1}' -f $Pch, (Sha $pchFull).Substring(0, 16))) }
$draftFull = Join-Path $root $Draft
$draftSha = Sha $draftFull
$txt = [IO.File]::ReadAllText($draftFull)
$nCr = $txt.Length - $txt.Replace("`r", '').Length
$nLf = $txt.Length - $txt.Replace("`n", '').Length
$lines.Add(('staged   {0}  sha {1}  {2} B  {3} lines  CR={4}  ({5})' -f $Draft, $draftSha, (Get-Item -LiteralPath $draftFull).Length, $nLf, $nCr, $(if ($draftSha -eq $WantSha) { '= rated draft' } else { 'NOT the rated draft ' + $WantSha.Substring(0, 16) })))
if ($draftSha -ne $WantSha) { $bad++ }
$cand = Join-Path $work 'gpu_wait_backoff.cpp'
Copy-Item -LiteralPath $draftFull -Destination $cand -Force
$candSha = Sha $cand
if ($candSha -ne $draftSha) { $bad++; $lines.Add("copy     $(Short $cand) sha $candSha MISMATCH") } else { $lines.Add("copy     $(Short $cand) = staged file") }

$def = '-DLEGO_GPU_WAIT_HOOK_GETDATA=1'
$jobs = @(
    @{ Name = 'control'; Src = $ctrlSrc; Extra = '' },
    @{ Name = 'candidate(a)'; Src = $cand; Extra = $def },
    @{ Name = 'candidate(b)'; Src = $cand; Extra = '' }
)
$res = @{}
$lines.Add("--- syntax (exact flags: $Label) ---")
foreach ($j in $jobs) {
    $a = ($baseArgs + ' ' + $j.Extra).Trim() + ' -fsyntax-only "' + $j.Src + '"'
    $r = Run $exe $a $work
    $r.Diag = $r.Out + $r.Err
    $res[$j.Name] = $r
    $nd = @(Diag-Set $r.Diag).Count
    $lines.Add(('{0,-13} exit={1} {2,5:N1}s diagnostics={3}  {4}{5}' -f $j.Name, $r.Code, $r.Secs, $nd, $(if ($j.Extra) { $j.Extra + ' ' } else { '' }), (Short $j.Src)))
    if ($r.Code -ne 0) { $bad++ }
    if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add('    | ' + (Short $_)) } }
}
$dc = @(Diag-Set $res['control'].Diag)
foreach ($n in 'candidate(a)', 'candidate(b)') {
    $dn = @(Diag-Set $res[$n].Diag)
    $issues = 0
    foreach ($t in @($dn | Where-Object { $dc -cnotcontains $_ } | Select-Object -Unique)) { $bad++; $issues++; $lines.Add("    NEW in $n : $t") }
    foreach ($g in @($dn | Where-Object { $dc -ccontains $_ } | Group-Object -CaseSensitive)) {
        $nc = @($dc | Where-Object { $_ -ceq $g.Name }).Count
        if ($g.Count -gt $nc) {
            if ($g.Name -match "'getenv' is deprecated") { $lines.Add("    EXPECTED in $n : $($g.Count) x (control $nc x) $($g.Name)") }
            else { $bad++; $issues++; $lines.Add("    MORE in $n : $($g.Count) x (control $nc x) $($g.Name)") }
        }
    }
    if (-not $issues) { $lines.Add("    $n : no new diagnostic text vs the control") }
}

$lines.Add('--- positive control (-E: hooks defined in the candidate file) ---')
$want = @{ 'candidate(a)' = 'sub_83FAF180,sub_83FB09E8,sub_83FBF7D0,sub_83FC0C10'; 'candidate(b)' = 'sub_83FAF180,sub_83FBF7D0' }
foreach ($j in $jobs | Where-Object { $_.Name -ne 'control' }) {
    $a = ($baseArgs + ' ' + $j.Extra).Trim() + ' -E "' + $j.Src + '"'
    $r = Run $exe $a $work
    $names = Hook-Defs $r.Out 'gpu_wait_backoff.cpp'
    $got = (@($names) | Sort-Object) -join ','
    $ok = ($r.Code -eq 0) -and ($got -ceq $want[$j.Name])
    if (-not $ok) { $bad++ }
    $lines.Add(('{0,-13} exit={1} {2,5:N1}s {3:N1} MB  defined: {4}  ({5})' -f $j.Name, $r.Code, $r.Secs, ($r.Out.Length / 1MB), $got, $(if ($ok) { 'as expected' } else { 'WANT ' + $want[$j.Name] })))
    if ($r.Code -ne 0 -and $r.Err.Trim()) { $r.Err -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 20 | ForEach-Object { $lines.Add('    | ' + (Short $_)) } }
}

if ($Lint) {
    $lines.Add('--- lint (informational: -Wall -Wextra on top of the exact flags; never fails) ---')
    foreach ($j in $jobs) {
        $a = ($baseArgs + ' ' + $j.Extra).Trim() + ' -Wall -Wextra -fsyntax-only "' + $j.Src + '"'
        $r = Run $exe $a $work
        $all = $r.Out + $r.Err
        $raw = @($all -split "`r?`n" | Where-Object { $_ -match '(warning|error):' })
        $lines.Add(('lint {0,-13} exit={1} {2,5:N1}s warning/error lines={3}' -f $j.Name, $r.Code, $r.Secs, $raw.Count))
        $raw | Select-Object -First 30 | ForEach-Object { $lines.Add('    | ' + (Short $_)) }
    }
} else { $lines.Add('--- lint skipped (light-tasks-only window; run with -Lint; the 13:24 devoffB report has it) ---') }

$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
