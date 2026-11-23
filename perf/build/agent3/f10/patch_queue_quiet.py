r"""patch_queue_quiet.py - Agent 3, task #23 (Agent 1, 11-23 05:45: "Before each row, check that no build or other
heavy process is running"). Adds a quiet-host gate to build/agent3/s4b/s4b-queue.ps1, checked right before every
launch (game rows and run-matrix rows):
  busy = any build process (compiler/linker/ninja/cmake/msbuild), any check script (s4b_check, p2c_check, logdiff,
         dumpstacks, native3_boot_check, check_n_rows), or total CPU (Processor(_Total) % Processor Time averaged over
         -QuietSampleSec s, default 5) above -QuietCpuPct (default 20);
  busy -> the queue waits (re-checks every 15 s); quiet -> logs\<id>.quiet.txt + a "quiet host before <id>" line in
         logs\queue.out.txt with the CPU and the top 5 processes.
Backup: s4b-queue.ps1.bak-0550 (made before this runs). Every target must occur exactly once, else nothing is written.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 's4b', 's4b-queue.ps1')

FUNC = r'''# task #23 (Agent 1, 11-23 05:45): quiet-host gate, checked right before every launch. QuietReason returns '' when the
# host is quiet, else the reason; $script:quietTxt keeps the last measurement (logs\<id>.quiet.txt at launch).
# Busy = any build process, any check script, or total CPU (Processor(_Total) % Processor Time, averaged over
# -QuietSampleSec s) above -QuietCpuPct. The per-process list covers my user's processes only (top 5 shown).
$buildNames = '^(clang|clang\+\+|clang-cl|cl|ninja|link|lld-link|cmake|msbuild|devenv|cc1plus|mspdbsrv)$'
$script:quietTxt = ''
function QuietReason {
    $b = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match $buildNames })
    if ($b.Count) { return ('build processes: ' + (@($b | Group-Object ProcessName | ForEach-Object { "$($_.Name) x$($_.Count)" }) -join ', ')) }
    $chk = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 's4b_check|p2c_check|logdiff|dumpstacks|native3_boot_check|check_n_rows' })
    if ($chk.Count) { return ('check scripts running: pid ' + (@($chk | ForEach-Object { [string]$_.ProcessId }) -join ', ')) }
    $before = @{}
    foreach ($p in Get-Process -ErrorAction SilentlyContinue) { if ($null -ne $p.CPU) { $before[$p.Id] = $p.CPU } }
    $t0 = Get-Date; $tot = $null
    try {
        $cs = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples $QuietSampleSec -ErrorAction Stop).CounterSamples
        $tot = ($cs | Measure-Object -Property CookedValue -Average).Average
    } catch { Start-Sleep -Seconds $QuietSampleSec }
    $dt = ((Get-Date) - $t0).TotalSeconds; $nc = [Environment]::ProcessorCount; $procs = @()
    foreach ($p in Get-Process -ErrorAction SilentlyContinue) {
        if ($null -ne $p.CPU -and $before.ContainsKey($p.Id)) {
            $procs += [pscustomobject]@{ n = $p.ProcessName; id = $p.Id; pct = ($p.CPU - $before[$p.Id]) / $dt / $nc * 100 }
        }
    }
    $sum = ($procs | Measure-Object -Property pct -Sum).Sum
    $src = 'Processor(_Total)'
    if ($null -eq $tot) { $tot = $sum; $src = 'my-user processes (counter failed)' }
    $top = @($procs | Sort-Object pct -Descending | Select-Object -First 5 | ForEach-Object { '{0}({1}) {2:0.0}%' -f $_.n, $_.id, $_.pct }) -join ', '
    $script:quietTxt = '{0} quiet check: build processes 0, check scripts 0, total CPU {1:0.0}% ({2}) over {3:0} s, limit {4}%; my-user processes {5:0.0}%; top: {6}' -f `
        (Get-Date -Format 'HH:mm:ss'), $tot, $src, $dt, $QuietCpuPct, $sum, $top
    if ($tot -gt $QuietCpuPct) { return "busy host: $script:quietTxt" }
    return ''
}
'''

REPS = [
    ("param(\n    [string]$LastLaunch = '23:30:00',\n    [string]$GamesClosed = '23:45:00'\n)\n",
     "param(\n    [string]$LastLaunch = '23:30:00',\n    [string]$GamesClosed = '23:45:00',\n"
     "    # task #23 (Agent 1, 11-23 05:45): before each row, no build or other heavy process may run (QuietReason)\n"
     "    [int]$QuietCpuPct = 20,\n    [int]$QuietSampleSec = 5\n)\n"),
    ("$ll = [datetime]::Today.Add([timespan]::Parse($LastLaunch))\n",
     FUNC + "$ll = [datetime]::Today.Add([timespan]::Parse($LastLaunch))\n"),
    ("    if (Held) { continue }   # the last HOLD/PAUSE check, right before the launch\n",
     "    $qr = QuietReason   # task #23: no build or other heavy process (takes -QuietSampleSec s)\n"
     "    if ($qr) {\n"
     "        if ($lastWait -ne 'quiet') { Say \"host not quiet ($qr); waiting (next: $($next.id))\"; $lastWait = 'quiet' }\n"
     "        Start-Sleep -Seconds 15; continue\n"
     "    }\n"
     "    if (Get-Process legodimensions -ErrorAction SilentlyContinue) { continue }   # one appeared during the sample\n"
     "    if (Held) { continue }   # the last HOLD/PAUSE check, right before the launch\n"),
    ("    foreach ($f in @('run-game', 'attach.out', 'attach.err', 'holdwatch.out', 'holdwatch.err', 'hold-abort', "
     "'sidecar.out', 'sidecar.err', 'run-matrix', 'run-matrix.err')) { Keep (Join-Path $logs \"$id.$f.txt\") }\n",
     "    foreach ($f in @('run-game', 'attach.out', 'attach.err', 'holdwatch.out', 'holdwatch.err', 'hold-abort', "
     "'sidecar.out', 'sidecar.err', 'run-matrix', 'run-matrix.err', 'quiet')) { Keep (Join-Path $logs \"$id.$f.txt\") }\n"
     "    try { Set-Content -LiteralPath (Join-Path $logs \"$id.quiet.txt\") -Value $script:quietTxt -Encoding UTF8 } catch { }\n"
     "    Say \"quiet host before $id`: $script:quietTxt\"\n"),
]

raw = open(P, 'rb').read().decode('utf-8')
bom = raw.startswith('\ufeff')
crlf = '\r\n' in raw
s = raw.lstrip('\ufeff').replace('\r\n', '\n')
for old, _new in REPS:
    if s.count(old) != 1:
        sys.exit('target occurs %d times: %r' % (s.count(old), old[:80]))
if not os.path.exists(P + '.bak-0550'):
    sys.exit('no backup s4b-queue.ps1.bak-0550')
for old, new in REPS:
    s = s.replace(old, new)
out = s.replace('\n', '\r\n') if crlf else s
with open(P, 'wb') as f:
    f.write((('\ufeff' if bom else '') + out).encode('utf-8'))
print('patched s4b-queue.ps1: %d replacements (%s%s)' % (len(REPS), 'CRLF' if crlf else 'LF', ', BOM' if bom else ''))
