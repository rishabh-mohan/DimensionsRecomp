# pthrottle_syntax.ps1 - S4 task #19 (host_execution_throttling_optout, default OFF): clang
# -fsyntax-only of threading_win.cpp and runtime.cpp with the exact dev-SDK flags
# (env\compile-one.ps1 -SyntaxOnly -PrintOnly gives each command), once for the pristine copies
# and once for the staged candidates in build\agent11\pthrottle\stage (pthrottle_stage.ps1), so
# the diagnostic outputs can be compared (the change must add no warning). Cloned from
# timerq_syntax.ps1; same rules, plus the header: each compile puts its own include tree first
# (-I stage\pristine\include or -I stage\include), so <rex/threading_timing.h> resolves to the
# matching copy of the header, and -iquote <live source dir> so threading_win.cpp's
# "platform_win.h" still resolves from the stage directory. A control compile (the staged
# threading_win.cpp against the PRISTINE header) must fail on the new field: that proves the
# -I override is in effect, so the candidate compiles really used the staged header.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_syntax.ps1         # staged copies
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_syntax.ps1 -Live   # live tree
# The precompiled header is always dropped (the PCH header stays force-included as plain
# source), so headers edited by others since the PCH was built can't fail the check.
# Single-threaded, one compile at a time, writes no objects.
# Output: build\agent11\pthrottle\stage\syntax-<stamp>.txt. Exit 0 = every pristine and
# candidate compile exit 0, the candidates have no diagnostic line the pristine copies don't
# have, and (staged mode) the control compile failed on keep_execution_speed_in_background.
param([switch]$Live, [string]$Config = 'Release')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent11\pthrottle\stage'
$report = Join-Path $stage ("syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
$files = @(
  @{ Name = 'threading_win.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\core\threading_win.cpp'; Control = $true },
  @{ Name = 'runtime.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\system\runtime.cpp'; Control = $false }
)
foreach ($p in 'pristine\threading_win.cpp', 'pristine\runtime.cpp', 'pristine\include\rex\threading_timing.h', 'threading_win.cpp', 'runtime.cpp', 'include\rex\threading_timing.h') {
  if (-not (Test-Path (Join-Path $stage $p))) { throw "no staged copy ($p): run bench\agent11\pthrottle_stage.ps1 first" }
}
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }

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
# diagnostic lines, with the file path and line/column numbers removed so the pristine and
# candidate outputs compare (the change shifts line numbers)
function Diag-Set([string]$d) {
  @($d -split "`r?`n" | Where-Object { $_ -match '(warning|error):' } |
    ForEach-Object { ($_ -replace '^.*?\.(cpp|h|hpp|hxx|inl):\d+:\d+:\s*', '') })
}
function Q([string]$s) { '"' + $s + '"' }

$incPristine = Join-Path $stage 'pristine\include'
$incStaged = Join-Path $stage 'include'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# pthrottle_syntax (S4 task #19)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  config $Config  candidate: $(if ($Live) { 'live tree' } else { 'staged copies' })")
$bad = 0
foreach ($f in $files) {
  $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  $po = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'env\compile-one.ps1') $f.Live -OutDir 'build\agent11\obj' -SyntaxOnly -PrintOnly -Config $Config 2>&1
  $poCode = $LASTEXITCODE
  $ErrorActionPreference = $old
  $po = @($po | ForEach-Object { "$_" })
  if ($poCode -ne 0) { $po | ForEach-Object { Write-Host $_ }; throw "compile-one -PrintOnly failed for $($f.Live)" }
  $dir = ($po | Where-Object { $_ -like 'cd *' } | Select-Object -First 1).Substring(3)
  $cmd = $po | Where-Object { $_ -notlike 'cd *' -and $_ -notlike 'note:*' -and $_.Trim() } | Select-Object -First 1
  if ($cmd.StartsWith('"')) { $q = $cmd.IndexOf('"', 1); $exe = $cmd.Substring(1, $q - 1); $args0 = $cmd.Substring($q + 1).Trim() }
  else { $sp = $cmd.IndexOf(' '); $exe = $cmd.Substring(0, $sp); $args0 = $cmd.Substring($sp + 1) }
  # drop the PCH (keep the force-included PCH header as plain source)
  $args0 = [regex]::Replace($args0, '-Xclang -include-pch -Xclang \S+\s*', '')
  $livePath = [IO.Path]::GetFullPath((Join-Path $root $f.Live))
  $liveDir = Split-Path -Parent $livePath
  $esc = [regex]::Escape($livePath)
  if (([regex]::Matches($args0, $esc, 'IgnoreCase')).Count -ne 1) { throw "source path not found exactly once in the command for $($f.Name)" }
  $pristine = Join-Path $stage "pristine\$($f.Name)"
  $runs = @(
    @{ Which = 'pristine'; Src = $pristine; Pre = ('-I' + (Q $incPristine) + ' -iquote ' + (Q $liveDir) + ' ') }
  )
  if ($Live) {
    $runs += @{ Which = 'candidate'; Src = $livePath; Pre = '' }
  } else {
    $runs += @{ Which = 'candidate'; Src = (Join-Path $stage $f.Name); Pre = ('-I' + (Q $incStaged) + ' -iquote ' + (Q $liveDir) + ' ') }
    if ($f.Control) {
      $runs += @{ Which = 'control'; Src = (Join-Path $stage $f.Name); Pre = ('-I' + (Q $incPristine) + ' -iquote ' + (Q $liveDir) + ' ') }
    }
  }
  $res = @{}
  foreach ($run in $runs) {
    $a = $run.Pre + [regex]::Replace($args0, $esc, $run.Src.Replace('$', '$$'), 'IgnoreCase')
    $r = Compile $exe $a $dir
    $res[$run.Which] = $r
    $nd = (Diag-Set $r.Diag).Count
    $hdr = 'live header'; if ($run.Pre) { $hdr = $(if ($run.Pre.Contains($incPristine)) { 'pristine header' } else { 'staged header' }) }
    $lines.Add(('{0,-18} {1,-9} exit={2} {3,5:N1}s diagnostics={4}  {5} ({6})' -f $f.Name, $run.Which, $r.Code, $r.Secs, $nd, $run.Src, $hdr))
    if ($run.Which -eq 'control') {
      $hit = @($r.Diag -split "`r?`n" | Where-Object { $_ -match 'error:' -and $_ -match 'keep_execution_speed_in_background' })
      if ($r.Code -ne 0 -and $hit.Count -ge 1) {
        $lines.Add("    control failed as expected: $($hit[0].Trim())")
      } else {
        $bad++; $lines.Add('    CONTROL DID NOT FAIL on keep_execution_speed_in_background: the -I override is not in effect')
      }
      continue
    }
    if ($r.Code -ne 0) { $bad++ }
    if ($r.Diag.Trim()) { $r.Diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add("    | $_") } }
  }
  $new = @(Diag-Set $res['candidate'].Diag | Where-Object { (Diag-Set $res['pristine'].Diag) -notcontains $_ })
  if ($new.Count) { $bad++; $new | ForEach-Object { $lines.Add("    NEW in candidate: $_") } }
  else { $lines.Add("    no new diagnostics in the candidate") }
}
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
