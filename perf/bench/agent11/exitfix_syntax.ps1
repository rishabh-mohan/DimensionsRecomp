# exitfix_syntax.ps1 - task #27: clang -fsyntax-only of the exit-path fix with
# the exact dev-SDK flags (env\compile-one.ps1 -SyntaxOnly -PrintOnly gives the
# command), once for the pristine copy and once for the candidate, so the two
# diagnostic outputs can be compared (the fix must add no warning).
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_syntax.ps1         # staged copies
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_syntax.ps1 -Live   # live tree
# The precompiled header is always dropped (the PCH header stays force-included
# as plain source), so headers edited by others since the PCH was built can't
# fail the check. Single-threaded, one compile at a time, writes no objects.
# Output: build\agent11\exitfix\syntax-<stamp>.txt. Exit 0 = every compile exit
# 0 and the candidate has no diagnostic line the pristine copy doesn't have.
param([switch]$Live, [string]$Config = 'Release')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent11\exitfix'
$report = Join-Path $stage ("syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
$files = @(
  @{ Name = 'xboxkrnl_hal.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\kernel\xboxkrnl\xboxkrnl_hal.cpp' },
  @{ Name = 'xam_ui.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\kernel\xam\xam_ui.cpp' }
)
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
# diagnostic lines, with the file path and line/column numbers removed so the
# pristine and candidate outputs compare (the fix shifts line numbers)
function Diag-Set([string]$d) {
  @($d -split "`r?`n" | Where-Object { $_ -match '(warning|error):' } |
    ForEach-Object { ($_ -replace '^.*?\.(cpp|h|hpp|hxx|inl):\d+:\d+:\s*', '') })
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# exitfix_syntax (task #27)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  config $Config  candidate: $(if ($Live) { 'live tree' } else { 'staged copies' })")
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
  $pristine = Join-Path $stage "pristine\$($f.Name)"
  $cand = Join-Path $stage $f.Name; if ($Live) { $cand = $livePath }
  $esc = [regex]::Escape($livePath)
  if (([regex]::Matches($args0, $esc, 'IgnoreCase')).Count -ne 1) { throw "source path not found exactly once in the command for $($f.Name)" }
  $res = @{}
  foreach ($which in 'pristine', 'candidate') {
    $src = $pristine; if ($which -eq 'candidate') { $src = $cand }
    $a = [regex]::Replace($args0, $esc, $src.Replace('$', '$$'), 'IgnoreCase')
    $r = Compile $exe $a $dir
    $res[$which] = $r
    $nd = (Diag-Set $r.Diag).Count
    $lines.Add(('{0,-18} {1,-9} exit={2} {3,5:N1}s diagnostics={4}  {5}' -f $f.Name, $which, $r.Code, $r.Secs, $nd, $src))
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
