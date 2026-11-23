# s4c1_syntax.ps1 (Agent 12) - S4.12 C1 (physical_protect_keep_watch, default OFF; task #31, from Agent 5's #28).
# clang -fsyntax-only of the C1 translation units with the exact dev-SDK flags (env\compile-one.ps1 -SyntaxOnly
# -PrintOnly gives each command), once for the CONTROL (the C1 base copies in build\agent12\s4-c1\orig\sdk, compiled
# against the live headers, which must be the C1 base headers) and once for the CANDIDATE (build\agent12\s4-c1\new\sdk,
# with new\sdk\include put FIRST on the include path so the staged xmemory.h / shared_memory.h win). The candidate
# must add no diagnostic.
# Units: src/system/xmemory.cpp, src/graphics/shared_memory.cpp, src/graphics/primitive_processor.cpp, plus
# src/graphics/d3d12/shared_memory.cpp (the diag staged copy, which C1 does not change) compiled with the live vs the
# staged headers, to show the derived class still compiles against the new shared_memory.h.
# rexlego src/gpu_native/memory_watch.cpp is a native-only TU (LEGODIMENSIONS_NATIVE_GPU): inspected, not compiled.
# Adapted from bench\agent12\s4fixi_syntax.ps1; same rules: the PCH is dropped (its header stays force-included as
# plain source), the live file's directory is the LAST include path (quote includes such as "frame_stats.h"),
# single-threaded, one compile at a time, writes no objects. Run it at BelowNormal:
#   cmd /c start "" /belownormal /wait /b powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent12\s4c1_syntax.ps1
# Output: build\agent12\s4-c1\syntax-<stamp>.txt. Exit 0 = every compile exits 0, every hash matches
# build\agent12\s4-c1\HASHES.txt and no candidate has a diagnostic its control doesn't have (nor more of them).
param([string]$Config = 'Release')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent12\s4-c1'
$report = Join-Path $stage ("syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
$sdk = Join-Path $root 'DimensionsRecomp\rexglue-sdk'
$newInc = Join-Path $stage 'new\sdk\include'
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
$h = @{}
foreach ($l in [IO.File]::ReadAllLines((Join-Path $stage 'HASHES.txt'))) {
    if ($l -match '^(orig|new)\s+([0-9A-F]{64})\s+(\S+)') { $h[$Matches[1] + '|' + $Matches[3]] = $Matches[2] }
}
if (-not $h['orig|src/system/xmemory.cpp'] -or -not $h['new|src/system/xmemory.cpp']) { throw 'build\agent12\s4-c1\HASHES.txt lacks the orig/new lines' }

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
$lines.Add("# s4c1_syntax (S4.12 C1: physical_protect_keep_watch, default OFF)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  config $Config")
$lines.Add('# control = build\agent12\s4-c1\orig\sdk + live headers; candidate = build\agent12\s4-c1\new\sdk + new\sdk\include first')
$bad = 0
# the control compiles see the live headers, which must be the C1 base headers; the candidate sees the staged ones
foreach ($hr in 'include/rex/system/xmemory.h', 'include/rex/graphics/shared_memory.h') {
    $lv = Sha (Join-Path $sdk $hr.Replace('/', '\'))
    $nw = Sha (Join-Path $stage ('new\sdk\' + $hr.Replace('/', '\')))
    $okL = ($lv -eq $h['orig|' + $hr]); $okN = ($nw -eq $h['new|' + $hr])
    if (-not $okL) { $bad++ }
    if (-not $okN) { $bad++ }
    $lines.Add(('header {0,-38} live {1} ({2})  staged {3} ({4})' -f $hr, $lv.Substring(0, 16),
            $(if ($okL) { '= HASHES orig' } else { 'MISMATCH' }), $nw.Substring(0, 16), $(if ($okN) { '= HASHES new' } else { 'MISMATCH' })))
}

$diagCopy = Join-Path $root 'build\agent12\s4-diag\new\shared_memory.cpp'
$diagSha = 'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587'
$units = @(
    @{ Rel = 'src/system/xmemory.cpp' },
    @{ Rel = 'src/graphics/shared_memory.cpp' },
    @{ Rel = 'src/graphics/primitive_processor.cpp' },
    @{ Rel = 'src/graphics/d3d12/shared_memory.cpp'; Fixed = $diagCopy; FixedSha = $diagSha }
)
foreach ($u in $units) {
    $rel = $u.Rel; $relW = $rel.Replace('/', '\')
    $liveRel = 'DimensionsRecomp\rexglue-sdk\' + $relW
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $po = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'env\compile-one.ps1') $liveRel -OutDir 'build\agent12\obj' -SyntaxOnly -PrintOnly -Config $Config 2>&1
    $poCode = $LASTEXITCODE
    $ErrorActionPreference = $old
    $po = @($po | ForEach-Object { "$_" })
    if ($poCode -ne 0) { $po | ForEach-Object { $lines.Add("    | $_") }; $lines.Add("$rel : compile-one -PrintOnly failed"); $bad++; continue }
    $dir = ($po | Where-Object { $_ -like 'cd *' } | Select-Object -First 1).Substring(3)
    $cmd = $po | Where-Object { $_ -notlike 'cd *' -and $_ -notlike 'note:*' -and $_ -notlike 'compile-one:*' -and $_ -match '-fsyntax-only' } | Select-Object -First 1
    if (-not $cmd) { $po | ForEach-Object { $lines.Add("    | $_") }; $lines.Add("$rel : no compiler command in the compile-one -PrintOnly output"); $bad++; continue }
    if ($cmd.StartsWith('"')) { $q = $cmd.IndexOf('"', 1); $exe = $cmd.Substring(1, $q - 1); $args0 = $cmd.Substring($q + 1).Trim() }
    else { $sp = $cmd.IndexOf(' '); $exe = $cmd.Substring(0, $sp); $args0 = $cmd.Substring($sp + 1) }
    # drop the PCH (keep the force-included PCH header as plain source)
    $args0 = [regex]::Replace($args0, '-Xclang -include-pch -Xclang \S+\s*', '')
    $livePath = [IO.Path]::GetFullPath((Join-Path $root $liveRel))
    # quote includes next to the live file: its directory is the LAST include path
    $args0 = $args0.TrimEnd() + ' -I"' + [IO.Path]::GetDirectoryName($livePath) + '"'
    $esc = [regex]::Escape($livePath)
    if (([regex]::Matches($args0, $esc, 'IgnoreCase')).Count -ne 1) { $lines.Add("$rel : source path not found exactly once in the command"); $bad++; continue }
    $ctrl = Join-Path $stage ('orig\sdk\' + $relW); $cand = Join-Path $stage ('new\sdk\' + $relW)
    $ctrlWant = $h['orig|' + $rel]; $candWant = $h['new|' + $rel]
    if ($u.Fixed) { $ctrl = $u.Fixed; $cand = $u.Fixed; $ctrlWant = $u.FixedSha; $candWant = $u.FixedSha }
    $res = @{}
    foreach ($which in 'control', 'candidate') {
        $src = $ctrl; $want = $ctrlWant; $a = $args0
        if ($which -eq 'candidate') { $src = $cand; $want = $candWant; $a = '-I"' + $newInc + '" ' + $args0 }
        $sha = Sha $src
        $hashNote = '= HASHES'
        if ($sha -ne $want) { $bad++; $hashNote = 'MISMATCH: want ' + $(if ($want) { $want.Substring(0, 16) } else { '(none)' }) }
        $a = [regex]::Replace($a, $esc, $src.Replace('$', '$$'), 'IgnoreCase')
        $r = Compile $exe $a $dir
        $res[$which] = $r
        $nd = (Diag-Set $r.Diag).Count
        $lines.Add(('{0,-38} {1,-9} exit={2} {3,5:N1}s diagnostics={4}  sha {5} ({6})  {7}' -f $rel, $which, $r.Code, $r.Secs, $nd, $sha.Substring(0, 16), $hashNote, $src))
        if ($r.Code -ne 0) { $bad++ }
        if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add("    | $_") } }
    }
    $dc = @(Diag-Set $res['control'].Diag); $dn = @(Diag-Set $res['candidate'].Diag)
    $new = @($dn | Where-Object { $dc -notcontains $_ })
    if ($new.Count) { $bad++; $new | ForEach-Object { $lines.Add("    NEW in candidate: $_") } }
    elseif ($dn.Count -gt $dc.Count) { $bad++; $lines.Add("    candidate has more diagnostic lines than its control ($($dn.Count) vs $($dc.Count))") }
    else { $lines.Add('    no new diagnostics in the candidate') }
}
$lines.Add('rexlego src/gpu_native/memory_watch.cpp: native-only TU (LEGODIMENSIONS_NATIVE_GPU), inspected, not compiled here')
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
