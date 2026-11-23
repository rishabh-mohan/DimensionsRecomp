# s4r1r2_syntax.ps1 (Agent 7, task #9) - S4 #18 (R1 stage 1, d3d12_submit_split_kb, default 0 = off) and
# #20 step 1 (R2 per-command-type counters, REX_D3D12_DEFERRED_COUNTERS, default 0 = compiled out).
# clang -fsyntax-only with the exact dev-SDK flags (env\compile-one.ps1 -SyntaxOnly -PrintOnly gives each command),
# once for the CONTROL (build\agent7\s4-r1r2\orig\sdk copies against the live headers, which must be the base
# headers) and once for the CANDIDATE (build\agent7\s4-r1r2\new\sdk copies, with new\sdk\include FIRST on the include
# path so the staged command_processor.h / deferred_command_list.h win). The candidate must add no diagnostic.
# Units:
#   src/graphics/d3d12/command_processor.cpp      orig vs new
#   src/graphics/d3d12/deferred_command_list.cpp  orig vs new
#   src/graphics/d3d12/deferred_command_list.cpp  orig vs new, both with -DREX_D3D12_DEFERRED_COUNTERS=1 (the
#                                                 compiled-in counters path; the base file ignores the macro)
#   the six other SDK TUs that include the d3d12 command_processor.h / deferred_command_list.h, from the live
#   sources: control = live headers, candidate = staged headers (the class layout change compiles everywhere).
#   rexlego includes neither header (checked), so no game TU is involved.
# Adapted from bench\agent12\s4c1_syntax.ps1; same rules: the PCH is dropped (its header stays force-included as plain
# source), the live file's directory is the LAST include path (quote includes such as "../frame_stats.h"),
# one compile at a time (single-threaded), writes no objects. Run it at BelowNormal:
#   cmd /c start "" /belownormal /wait /b powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\s4r1r2_syntax.ps1
# Output: build\agent7\s4-r1r2\syntax-<stamp>.txt. Exit 0 = every compile exits 0, every hash matches
# build\agent7\s4-r1r2\HASHES.txt and no candidate has a diagnostic its control doesn't have (nor more of them).
# -Only <regex>: compile only the units whose label matches it (e.g. -Only deferred_command_list after a re-stage
# that changed deferred_command_list.cpp alone); the header and source hash checks still run, and the report name
# gets an "-only" suffix.
param([string]$Config = 'Release', [string]$Only = '')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent7\s4-r1r2'
$report = Join-Path $stage ("syntax-{0:yyyyMMdd-HHmmss}{1}.txt" -f (Get-Date), $(if ($Only) { '-only' } else { '' }))
$sdk = Join-Path $root 'DimensionsRecomp\rexglue-sdk'
$newInc = Join-Path $stage 'new\sdk\include'
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
$h = @{}
foreach ($l in [IO.File]::ReadAllLines((Join-Path $stage 'HASHES.txt'))) {
    if ($l -match '^(orig|new)\s+([0-9A-F]{64})\s+(\S+)') { $h[$Matches[1] + '|' + $Matches[3]] = $Matches[2] }
}
if (-not $h['orig|src/graphics/d3d12/command_processor.cpp'] -or -not $h['new|src/graphics/d3d12/command_processor.cpp']) { throw 'build\agent7\s4-r1r2\HASHES.txt lacks the orig/new lines' }

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
$lines.Add("# s4r1r2_syntax (S4 #18 R1 stage 1 + #20 step 1 R2 counters, both default off)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  config $Config")
$lines.Add('# control = build\agent7\s4-r1r2\orig\sdk (or the live source) + live headers; candidate = new\sdk (or the live source) + new\sdk\include first')
if ($Only) { $lines.Add("# -Only '$Only': only the units whose label matches are compiled") }
$bad = 0
# the control compiles see the live headers, which must be the base headers; the candidate sees the staged ones
foreach ($hr in 'include/rex/graphics/d3d12/command_processor.h', 'include/rex/graphics/d3d12/deferred_command_list.h') {
    $lv = Sha (Join-Path $sdk $hr.Replace('/', '\'))
    $nw = Sha (Join-Path $stage ('new\sdk\' + $hr.Replace('/', '\')))
    $okL = ($lv -eq $h['orig|' + $hr]); $okN = ($nw -eq $h['new|' + $hr])
    if (-not $okL) { $bad++ }
    if (-not $okN) { $bad++ }
    $lines.Add(('header {0,-52} live {1} ({2})  staged {3} ({4})' -f $hr, $lv.Substring(0, 16),
            $(if ($okL) { '= HASHES orig' } else { 'MISMATCH' }), $nw.Substring(0, 16), $(if ($okN) { '= HASHES new' } else { 'MISMATCH' })))
}
# the live sources of the staged TUs must be the base copies too
foreach ($sr in 'src/graphics/d3d12/command_processor.cpp', 'src/graphics/d3d12/deferred_command_list.cpp') {
    $lv = Sha (Join-Path $sdk $sr.Replace('/', '\'))
    $ok = ($lv -eq $h['orig|' + $sr]); if (-not $ok) { $bad++ }
    $lines.Add(('source {0,-52} live {1} ({2})' -f $sr, $lv.Substring(0, 16), $(if ($ok) { '= HASHES orig' } else { 'MISMATCH' })))
}

$units = @(
    @{ Rel = 'src/graphics/d3d12/command_processor.cpp'; Staged = $true },
    @{ Rel = 'src/graphics/d3d12/deferred_command_list.cpp'; Staged = $true },
    @{ Rel = 'src/graphics/d3d12/deferred_command_list.cpp'; Staged = $true; Extra = '-DREX_D3D12_DEFERRED_COUNTERS=1' },
    @{ Rel = 'src/graphics/d3d12/graphics_system.cpp' },
    @{ Rel = 'src/graphics/d3d12/pipeline_cache.cpp' },
    @{ Rel = 'src/graphics/d3d12/primitive_processor.cpp' },
    @{ Rel = 'src/graphics/d3d12/render_target_cache.cpp' },
    @{ Rel = 'src/graphics/d3d12/shared_memory.cpp' },
    @{ Rel = 'src/graphics/d3d12/texture_cache.cpp' }
)
foreach ($u in $units) {
    $rel = $u.Rel; $relW = $rel.Replace('/', '\')
    $label = $rel; if ($u.Extra) { $label = $rel + ' ' + $u.Extra }
    if ($Only -and $label -notmatch $Only) { continue }
    $liveRel = 'DimensionsRecomp\rexglue-sdk\' + $relW
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $po = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'env\compile-one.ps1') $liveRel -OutDir 'build\agent7\obj' -SyntaxOnly -PrintOnly -Config $Config 2>&1
    $poCode = $LASTEXITCODE
    $ErrorActionPreference = $old
    $po = @($po | ForEach-Object { "$_" })
    if ($poCode -ne 0) { $po | ForEach-Object { $lines.Add("    | $_") }; $lines.Add("$label : compile-one -PrintOnly failed"); $bad++; continue }
    $dir = ($po | Where-Object { $_ -like 'cd *' } | Select-Object -First 1).Substring(3)
    $cmd = $po | Where-Object { $_ -notlike 'cd *' -and $_ -notlike 'note:*' -and $_ -notlike 'compile-one:*' -and $_ -match '-fsyntax-only' } | Select-Object -First 1
    if (-not $cmd) { $po | ForEach-Object { $lines.Add("    | $_") }; $lines.Add("$label : no compiler command in the compile-one -PrintOnly output"); $bad++; continue }
    if ($cmd.StartsWith('"')) { $q = $cmd.IndexOf('"', 1); $exe = $cmd.Substring(1, $q - 1); $args0 = $cmd.Substring($q + 1).Trim() }
    else { $sp = $cmd.IndexOf(' '); $exe = $cmd.Substring(0, $sp); $args0 = $cmd.Substring($sp + 1) }
    # drop the PCH (keep the force-included PCH header as plain source)
    $args0 = [regex]::Replace($args0, '-Xclang -include-pch -Xclang \S+\s*', '')
    $livePath = [IO.Path]::GetFullPath((Join-Path $root $liveRel))
    # quote includes next to the live file: its directory is the LAST include path
    $args0 = $args0.TrimEnd() + ' -I"' + [IO.Path]::GetDirectoryName($livePath) + '"'
    if ($u.Extra) { $args0 = $args0 + ' ' + $u.Extra }
    $esc = [regex]::Escape($livePath)
    if (([regex]::Matches($args0, $esc, 'IgnoreCase')).Count -ne 1) { $lines.Add("$label : source path not found exactly once in the command"); $bad++; continue }
    if ($u.Staged) {
        $ctrl = Join-Path $stage ('orig\sdk\' + $relW); $cand = Join-Path $stage ('new\sdk\' + $relW)
        $ctrlWant = $h['orig|' + $rel]; $candWant = $h['new|' + $rel]
    } else {
        $ctrl = $livePath; $cand = $livePath; $ctrlWant = Sha $livePath; $candWant = $ctrlWant
    }
    $res = @{}
    foreach ($which in 'control', 'candidate') {
        $src = $ctrl; $want = $ctrlWant; $a = $args0
        if ($which -eq 'candidate') { $src = $cand; $want = $candWant; $a = '-I"' + $newInc + '" ' + $args0 }
        $sha = Sha $src
        $hashNote = $(if ($u.Staged) { '= HASHES' } else { 'live, unchanged' })
        if ($sha -ne $want) { $bad++; $hashNote = 'MISMATCH: want ' + $(if ($want) { $want.Substring(0, 16) } else { '(none)' }) }
        $a = [regex]::Replace($a, $esc, $src.Replace('$', '$$'), 'IgnoreCase')
        $r = Compile $exe $a $dir
        $res[$which] = $r
        $nd = (Diag-Set $r.Diag).Count
        $lines.Add(('{0,-48} {1,-9} exit={2} {3,5:N1}s diagnostics={4}  sha {5} ({6})  {7}' -f $label, $which, $r.Code, $r.Secs, $nd, $sha.Substring(0, 16), $hashNote, $src))
        if ($r.Code -ne 0) { $bad++ }
        if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add("    | $_") } }
    }
    $dc = @(Diag-Set $res['control'].Diag); $dn = @(Diag-Set $res['candidate'].Diag)
    $new = @($dn | Where-Object { $dc -notcontains $_ })
    if ($new.Count) { $bad++; $new | ForEach-Object { $lines.Add("    NEW in candidate: $_") } }
    elseif ($dn.Count -gt $dc.Count) { $bad++; $lines.Add("    candidate has more diagnostic lines than its control ($($dn.Count) vs $($dc.Count))") }
    else { $lines.Add('    no new diagnostics in the candidate') }
}
$lines.Add('rexlego: includes neither d3d12 command_processor.h nor deferred_command_list.h (grep), so no game TU is compiled here')
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
