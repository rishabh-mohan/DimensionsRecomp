<#
.SYNOPSIS
  Self-test of testg_driver.ps1 (watch-mode verdicts, setup errors) and of TestGWin+LogTail and
  TestGWin::MiniDump, with synthetic spdlog-format logs. No game is needed and nothing is started
  except one ping.exe that stands in for the game process. Exit 0 if every check passes.

.DESCRIPTION
  Each scenario writes a complete log first and runs the driver in-process with -FromStart, so the
  verdicts come from the log timestamps (LATE) or from the driver's own clock after reading (HANG,
  stopped, idle). Output goes to build\agent11\selftest\<time>\ (logs, reports, one small dump).
#>
param([string]$Dir = '')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not $Dir) { $Dir = Join-Path $root ('build\agent11\selftest\{0:yyyyMMdd-HHmmss}' -f (Get-Date)) }
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
if (-not ('TestGWin' -as [type])) {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_win.cs'))) -Language CSharp
}
$driver = Join-Path $PSScriptRoot 'testg_driver.ps1'
$failures = 0
function Check([string]$what, [bool]$ok, [string]$detail = '') {
    if ($ok) { Write-Host "  ok    $what" } else { $script:failures++; Write-Host "  FAIL  $what $detail" }
}

# --- TestGWin+LogTail: partial lines, CRLF, fromStart=false, truncation (rotation) ---
Write-Host 'LogTail:'
$lt = Join-Path $Dir 'logtail.log'
[IO.File]::WriteAllText($lt, "old line`r`n")
$tailNew = New-Object 'TestGWin+LogTail' -ArgumentList $lt, $false
$tailAll = New-Object 'TestGWin+LogTail' -ArgumentList $lt, $true
Check 'fromStart=true sees existing lines' ((@($tailAll.Read()) -join '|') -eq 'old line')
Check 'fromStart=false skips existing lines' (@($tailNew.Read()).Count -eq 0)
[IO.File]::AppendAllText($lt, 'abc')
Check 'a partial line is held back' (@($tailNew.Read()).Count -eq 0)
[IO.File]::AppendAllText($lt, "def`r`nx`ny`n")
Check 'completed and LF-only lines' ((@($tailNew.Read()) -join '|') -eq 'abcdef|x|y')
[IO.File]::WriteAllText($lt, "new`n")
Check 'truncation restarts from the top' ((@($tailNew.Read()) -join '|') -eq 'new')
Check 'nothing new, nothing read' (@($tailNew.Read()).Count -eq 0)

# --- a stand-in "game" process: alive, windowless ---
$stand = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\ping.exe') -ArgumentList '-n', '600', '127.0.0.1' -RedirectStandardOutput (Join-Path $Dir 'ping.txt') -NoNewWindow -PassThru
$dead = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\cmd.exe') -ArgumentList '/c', 'exit 0' -RedirectStandardOutput (Join-Path $Dir 'cmd.txt') -NoNewWindow -PassThru
[void]$dead.WaitForExit(30000)
$deadPid = $dead.Id
$dead.Dispose()

# --- a stand-in whose window stops answering: a WinForms form, then Thread.Sleep (no message
# pump). Ghosting is off, so the hung window stays visible and MainWindow still finds it.
$hungPs1 = Join-Path $Dir 'hung_standin.ps1'
[IO.File]::WriteAllText($hungPs1, @'
Add-Type -Name G -Namespace W -MemberDefinition '[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern void DisableProcessWindowsGhosting();'
[W.G]::DisableProcessWindowsGhosting()
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.Form
$f.Text = 'testg-standin-hung'
$f.Show()
[System.Windows.Forms.Application]::DoEvents()
[System.Threading.Thread]::Sleep(600000)
'@)
$hung = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $hungPs1 -RedirectStandardOutput (Join-Path $Dir 'hung.txt') -NoNewWindow -PassThru
$hungWin = [IntPtr]::Zero
for ($w = 0; $w -lt 100 -and $hungWin -eq [IntPtr]::Zero; $w++) { Start-Sleep -Milliseconds 200; $hungWin = [TestGWin]::MainWindow($hung.Id) }
Start-Sleep -Milliseconds 500
Write-Host ("hung-window stand-in: pid {0}, {1}; ping {2} (-1 = no answer)" -f $hung.Id, [TestGWin]::Describe($hungWin), [TestGWin]::Ping($hungWin, 1000))

$tid = 4242
function L([datetime]$t, [string]$msg, [string]$lvl = 'info') { return ('[{0:yyyy-MM-dd HH:mm:ss.fff}] [{1}] [rex] [t{2}] {3}' -f $t, $lvl, $tid, $msg) }
# Builds a log from steps: 'S' suspend, 'R' resume, 'N' noise; each step advances the clock by $ms.
function Build([string]$steps, [int]$ms, [hashtable]$extraMs = @{}) {
    $t = (Get-Date).AddSeconds(-30)
    $out = @((L $t 'Booting'), (L $t 'some error' 'error'))
    for ($k = 0; $k -lt $steps.Length; $k++) {
        $t = $t.AddMilliseconds($ms)
        if ($extraMs.ContainsKey($k)) { $t = $t.AddMilliseconds($extraMs[$k]) }
        switch ($steps[$k]) {
            'S' { $out += (L $t 'Guest suspended (17 threads)') }
            'R' { $out += (L $t 'Guest resumed (17 threads)') }
            default { $out += (L $t 'noise') }
        }
    }
    return $out
}

$scenarios = @(
    @{ Name = 'pass'; Steps = 'NSRSRSRSRSRN'; Args = @{ Cycles = 5 }; Exit = 0; Verdict = 'PASS' },
    @{ Name = 'late'; Steps = 'SRSR'; Extra = @{ 3 = 1700 }; Args = @{ Cycles = 5 }; Exit = 1; Verdict = 'LATE' },
    @{ Name = 'hang'; Steps = 'SRS'; Args = @{ Cycles = 5 }; Dump = $true; Exit = 1; Verdict = "no 'Guest resumed'" },
    @{ Name = 'second-suspend'; Steps = 'SSR'; Args = @{ Cycles = 5 }; Exit = 1; Verdict = 'NO-RESUME' },
    @{ Name = 'stopped'; Steps = 'SRSR'; Args = @{ Cycles = 5 }; Exit = 3; Verdict = 'pause cycles stopped after 2' },
    @{ Name = 'stopped-ui-silent'; Steps = 'SRSR'; Args = @{ Cycles = 5; UiHangMs = 8000 }; Hung = $true; Dump = $true; Exit = 1; Verdict = 'UI thread did not answer WM_NULL for 8000 ms after 2 cycles (guest running' },
    @{ Name = 'idle'; Steps = 'NNN'; Args = @{ Cycles = 5; FirstEventTimeoutSec = 3 }; Exit = 3; Verdict = "no 'Guest suspended'" },
    @{ Name = 'setup-dead-pid'; Steps = 'SR'; Args = @{ Cycles = 1 }; Pid = $deadPid; Exit = 2; Verdict = '' },
    @{ Name = 'post-no-window'; Steps = 'N'; Args = @{ Cycles = 1 }; Mode = 'post'; Exit = 2; Verdict = 'no visible game window' }
)

foreach ($sc in $scenarios) {
    Write-Host "scenario $($sc.Name):"
    $log = Join-Path $Dir "$($sc.Name).log"
    $extra = @{}; if ($sc.Extra) { $extra = $sc.Extra }
    [IO.File]::WriteAllLines($log, [string[]](Build $sc.Steps 300 $extra))
    $report = Join-Path $Dir "$($sc.Name)_report.txt"
    $a = @{ GamePid = $stand.Id; Log = $log; Mode = 'watch'; PeriodMs = 300; ResumeTimeoutMs = 1000; FirstEventTimeoutSec = 20; FromStart = $true; Out = $report }
    if ($sc.Pid) { $a.GamePid = $sc.Pid }
    if ($sc.Hung) { $a.GamePid = $hung.Id }
    if ($sc.Mode) { $a.Mode = $sc.Mode }
    if (-not $sc.Dump) { $a.NoDump = $true }
    foreach ($k in $sc.Args.Keys) { $a[$k] = $sc.Args[$k] }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $code = -1
    try { & $driver @a 6>$null; $code = $LASTEXITCODE }
    catch { Check 'driver ran without a script error' $false ("{0}`n{1}" -f $_.Exception.Message, $_.ScriptStackTrace); continue }
    $text = ''; if (Test-Path -LiteralPath $report) { $text = [IO.File]::ReadAllText($report) }
    $verdict = ([regex]::Match($text, '(?m)^VERDICT: .*$')).Value
    Check ("exit code {0} (got {1}, {2:N1} s)" -f $sc.Exit, $code, $sw.Elapsed.TotalSeconds) ($code -eq $sc.Exit)
    if ($sc.Verdict) { Check "report says '$($sc.Verdict)'" ($text.Contains($sc.Verdict)) "[$verdict]" }
    if ($sc.Exit -ne 2) { Check 'report and csv written' ((Test-Path -LiteralPath $report) -and (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($report, '.csv')))) }
    if ($sc.Dump) {
        $m = [regex]::Match($text, '(?m)^minidump: .*$').Value
        Check 'minidump of the stand-in written' ($m -match 'written, \d+ bytes') "[$m]"
        $tl = [regex]::Match($text, '(?m)^threads: .*$').Value
        Check 'thread list written' ($tl -match '-threads\.txt : \d+ threads, \d+ suspended') "[$tl]"
    }
    if ($verdict) { Write-Host "        $verdict" }
}

try { $stand.Kill() } catch { }
try { $hung.Kill() } catch { }
Write-Host ''
if ($failures) { Write-Host "SELFTEST: $failures check(s) FAILED ($Dir)"; exit 1 }
Write-Host "SELFTEST: all checks passed ($Dir)"
exit 0
