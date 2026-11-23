# syntax_check_codegen.ps1 (Agent 9, run-2 task #17 step 4): clang -fsyntax-only of the staged #26 change
# (db16cyc_pause) with the snap1 SDK build's own compile_commands entries (Release), as in R2.11.2 / #11.
#   SDK side (build\agent2\snap1-sdk\compile_commands.json, Release entries, PCH flags kept):
#     sys-control    snap1 src/codegen/builders/system.cpp, exact command
#     sys-candidate  new\src\codegen\builders\system.cpp, same command plus -I new\include first (new config.h)
#     sys-negative   new system.cpp WITHOUT the overlay: must FAIL on db16cycPause (proves the overlay is live)
#     cfg-control    snap1 src/codegen/config.cpp, exact command
#     cfg-candidate  new\src\codegen\config.cpp plus -I new\include
#   Generated side (build\agent2\snapB-off\compile_commands.json, devoffB's entry for TU383, no PCH flag):
#     gen-control    B legodimensions_recomp.383.cpp (sub_83FAF180: 8 db16cyc), exact command
#     gen-candidate  a copy with "\tsimde_mm_pause();" after each "\t// db16cyc " line = the predicted ON output
# One compile at a time, single-threaded, no objects. Run at BelowNormal:
#   cmd /c start "" /belownormal /wait /b powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\s4\spin\db16cyc-pause\syntax_check_codegen.ps1
# Exit 0 = controls and candidates exit 0 with no new diagnostic text, the negative fails as expected,
# and the TU383 copy got exactly 8 inserted lines.
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
function Diag-Set([string]$d) {
    @($d -split "`r?`n" | Where-Object { $_ -match '(warning|error):' } | ForEach-Object { ($_ -replace '^.*?:\d+:\d+:\s*', '') })
}
function Short([string]$s) { $s.Replace($root + '\', '').Replace($root.Replace('\', '/') + '/', '') }
function Entry([string]$ccPath, [string]$fileRe, [string]$outRe) {
    $cc = [IO.File]::ReadAllText($ccPath) | ConvertFrom-Json
    $ent = @($cc | Where-Object { $_.file -match $fileRe -and ([string]$_.output -match $outRe -or [string]$_.command -match $outRe) })
    if ($ent.Count -ne 1) { throw "$fileRe : $($ent.Count) entries in $ccPath" }
    $cmd = [string]$ent[0].command
    if ($cmd.StartsWith('"')) { $q = $cmd.IndexOf('"', 1); $exe = $cmd.Substring(1, $q - 1); $rest = $cmd.Substring($q + 1).Trim() }
    else { $sp = $cmd.IndexOf(' '); $exe = $cmd.Substring(0, $sp); $rest = $cmd.Substring($sp + 1) }
    $m = [regex]::Match($rest, '\s-o\s+(\S+)\s+-c\s+(\S+)\s*$')
    if (-not $m.Success) { throw "$fileRe : command does not end in '-o <obj> -c <src>'" }
    return @{ Exe = $exe; Args = $rest.Substring(0, $m.Index).Trim(); Src = [IO.Path]::GetFullPath($m.Groups[2].Value); Dir = [string]$ent[0].directory; Count = $cc.Count }
}

$lines = New-Object System.Collections.Generic.List[string]
$bad = 0
$lines.Add("# syntax_check_codegen (#17 step 4: #26 db16cyc_pause)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$sdkCC = Join-Path $root 'build\agent2\snap1-sdk\compile_commands.json'
$genCC = Join-Path $root 'build\agent2\snapB-off\compile_commands.json'
$sys = Entry $sdkCC 'codegen[\\/]+builders[\\/]+system\.cpp$' '[\\/]Release[\\/]'
$cfg = Entry $sdkCC 'codegen[\\/]+config\.cpp$' '[\\/]Release[\\/]'
$gen = Entry $genCC 'legodimensions_recomp\.383\.cpp$' '.'
$ver = Run $sys.Exe '--version' $work
$lines.Add('clang: ' + (($ver.Out -split "`r?`n")[0]))
$lines.Add("SDK entries: $(Short $sdkCC) ($($sys.Count) entries, Release), dir $(Short $sys.Dir); '-o <obj> -c <src>' -> '-fsyntax-only <src>'")
$lines.Add("gen entry:   $(Short $genCC) ($($gen.Count) entries), dir $(Short $gen.Dir)")
$pch = [regex]::Match($sys.Args, '-include-pch\s+-Xclang\s+(\S+)').Groups[1].Value
if ($pch) { $lines.Add(('SDK pch: {0}  {1:N1} MB  {2:yyyy-MM-dd HH:mm}' -f (Short $pch), ((Get-Item -LiteralPath $pch).Length / 1MB), (Get-Item -LiteralPath $pch).LastWriteTime)) }

$overlay = Join-Path $here 'new\include'
$newSys = Join-Path $here 'new\src\codegen\builders\system.cpp'
$newCfg = Join-Path $here 'new\src\codegen\config.cpp'
foreach ($pair in @(@($sys.Src, 'base\src\codegen\builders\system.cpp'), @($cfg.Src, 'base\src\codegen\config.cpp'))) {
    $a = Sha $pair[0]; $b = Sha (Join-Path $here $pair[1])
    $lines.Add(('source  {0}  sha {1}  = staged {2}: {3}' -f (Short $pair[0]), $a.Substring(0, 16), $pair[1], $(if ($a -eq $b) { 'yes' } else { $bad++; 'NO' })))
}
$lines.Add(('overlay {0}  sha {1}' -f (Short (Join-Path $overlay 'rex\codegen\config.h')), (Sha (Join-Path $overlay 'rex\codegen\config.h')).Substring(0, 16)))

# predicted ON output of TU383: one "\tsimde_mm_pause();" line after every "\t// db16cyc " line
$genCopy = Join-Path $work 'legodimensions_recomp.383.cpp'
$txt = [IO.File]::ReadAllText($gen.Src)
$ins = ([regex]::Matches($txt, "(?m)^\t// db16cyc \n")).Count
$txt2 = [regex]::Replace($txt, "(?m)^(\t// db16cyc \n)", "`$1`tsimde_mm_pause();`n")
[IO.File]::WriteAllText($genCopy, $txt2, (New-Object System.Text.UTF8Encoding($false)))
$okIns = ($ins -eq 8) -and (([regex]::Matches($txt2, "(?m)^\tsimde_mm_pause\(\);\n")).Count -eq 8)
if (-not $okIns) { $bad++ }
$lines.Add(('gen     {0}  sha {1}; copy +{2} lines -> {3} ({4})' -f (Short $gen.Src), (Sha $gen.Src).Substring(0, 16), $ins, (Short $genCopy), $(if ($okIns) { 'as expected: 8' } else { 'WANT 8' })))

$jobs = @(
    @{ Name = 'sys-control'; E = $sys; Src = $sys.Src; Pre = ''; Want = 0; Ctrl = '' },
    @{ Name = 'sys-candidate'; E = $sys; Src = $newSys; Pre = "-I`"$overlay`""; Want = 0; Ctrl = 'sys-control' },
    @{ Name = 'sys-negative'; E = $sys; Src = $newSys; Pre = ''; Want = 1; Ctrl = '' },
    @{ Name = 'cfg-control'; E = $cfg; Src = $cfg.Src; Pre = ''; Want = 0; Ctrl = '' },
    @{ Name = 'cfg-candidate'; E = $cfg; Src = $newCfg; Pre = "-I`"$overlay`""; Want = 0; Ctrl = 'cfg-control' },
    @{ Name = 'gen-control'; E = $gen; Src = $gen.Src; Pre = ''; Want = 0; Ctrl = '' },
    @{ Name = 'gen-candidate'; E = $gen; Src = $genCopy; Pre = ''; Want = 0; Ctrl = 'gen-control' }
)
$res = @{}
$lines.Add('--- syntax ---')
foreach ($j in $jobs) {
    $a = ($j.Pre + ' ' + $j.E.Args).Trim() + ' -fsyntax-only "' + $j.Src + '"'
    $r = Run $j.E.Exe $a $j.E.Dir
    $r.Diag = $r.Out + $r.Err
    $res[$j.Name] = $r
    $nd = @(Diag-Set $r.Diag).Count
    if ($j.Want -eq 0) { $ok = ($r.Code -eq 0) } else { $ok = ($r.Code -ne 0) -and ($r.Diag -match "no member named 'db16cycPause'") }
    if (-not $ok) { $bad++ }
    $lines.Add(('{0,-14} exit={1} {2,6:N1}s diagnostics={3}  {4}{5}  ({6})' -f $j.Name, $r.Code, $r.Secs, $nd, $(if ($j.Pre) { '-I new\include ' } else { '' }), (Short $j.Src), $(if ($ok) { if ($j.Want) { 'fails as expected' } else { 'ok' } } else { 'UNEXPECTED' })))
    if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 12 | ForEach-Object { $lines.Add('    | ' + (Short $_)) } }
    if ($j.Ctrl) {
        $dc = @(Diag-Set $res[$j.Ctrl].Diag); $dn = @(Diag-Set $r.Diag); $issues = 0
        foreach ($t in @($dn | Where-Object { $dc -cnotcontains $_ } | Select-Object -Unique)) { $bad++; $issues++; $lines.Add("    NEW vs $($j.Ctrl): $t") }
        foreach ($g in @($dn | Where-Object { $dc -ccontains $_ } | Group-Object -CaseSensitive)) {
            $nc = @($dc | Where-Object { $_ -ceq $g.Name }).Count
            if ($g.Count -gt $nc) { $bad++; $issues++; $lines.Add("    MORE vs $($j.Ctrl): $($g.Count) x (control $nc x) $($g.Name)") }
        }
        if (-not $issues) { $lines.Add("    no new diagnostic text vs $($j.Ctrl)") }
    }
}
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
