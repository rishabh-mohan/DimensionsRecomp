# pthrottle_dryrunner.ps1 - dot-sourced by pthrottle_pairs.ps1 -DryRun only. A stand-in for Agent 8's
# run-matrix that starts no game: per run it makes the same run dir name (<HHmm>-<arm>-r<k>, the
# same round-robin order), starts pthrottle_standin.exe (a tiny sleeper compiled here) from it, calls
# SetProcessInformation(C=0x4 S=0x0) on it 3 s in, like the game's own startup call, reads the state
# 2 s later (opt-out arm: the sidecar must have re-applied, C=0x5; off arm: C=0x4), and writes a
# synthetic sys.csv and a run.json (UTF-8 with BOM, like run-timing.ps1). Synthetic slow state:
# d0-r1 from 40 s, d0-r2 from 80 s, d0-r3 none; d0e none (d0e-r2: a 2-row dip, under MinRows).
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PtDry {
  [StructLayout(LayoutKind.Sequential)] struct St { public uint V, C, S; }
  [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetProcessInformation(IntPtr p, int c, ref St s, int n);
  [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetProcessInformation(IntPtr p, int c, ref St s, int n);
  public static string Read(IntPtr p) {
    St s = new St(); s.V = 1;
    if (!GetProcessInformation(p, 4, ref s, 12)) return "error " + Marshal.GetLastWin32Error();
    return string.Format("C=0x{0:X} S=0x{1:X}", s.C, s.S);
  }
  public static int Write(IntPtr p, uint c, uint st) {
    St s = new St(); s.V = 1; s.C = c; s.S = st;
    return SetProcessInformation(p, 4, ref s, 12) ? 0 : Marshal.GetLastWin32Error();
  }
}
'@
function Get-Standin {
    $d = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\build\agent11\pthrottle\standin'))
    $exe = Join-Path $d 'pthrottle_standin.exe'
    if (-not (Test-Path -LiteralPath $exe)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
        Add-Type -OutputType ConsoleApplication -OutputAssembly $exe -TypeDefinition 'public static class PtStandin { public static void Main(string[] a) { System.Threading.Thread.Sleep(1000 * int.Parse(a[0])); } }'
    }
    return $exe
}
function Start-Outside([string]$Meta) {
    $d = Join-Path $Meta 'outside'; New-Item -ItemType Directory -Force -Path $d | Out-Null
    $exe = Join-Path $d 'pthrottle_standin.exe'; Copy-Item -LiteralPath (Get-Standin) -Destination $exe
    $p = Start-Process -FilePath $exe -ArgumentList '300' -WindowStyle Hidden -PassThru; $null = $p.Handle
    Start-Sleep -Milliseconds 1500
    return $p
}
function Test-Outside($p, [string]$slog) {
    $st = [PtDry]::Read($p.Handle)
    if (-not $p.HasExited) { $p.Kill(); $null = $p.WaitForExit(5000) }
    $ign = Select-String -LiteralPath $slog -Pattern ('ignore pid {0}:' -f $p.Id) -Quiet
    $ok = ($st -eq 'C=0x0 S=0x0') -and $ign
    Say ('dry check: stand-in outside the runs dir (pid {0}): state {1}, ignored by the sidecar {2}: {3}' -f $p.Id, $st, $ign, $(if ($ok) { 'PASS' } else { 'FAIL' }))
    if ($ok) { return 0 }; return 1
}
function Invoke-DryRunner([string]$Out, [int]$Pairs, [int]$MeasureS) {
    $inv = [Globalization.CultureInfo]::InvariantCulture
    $runs = Join-Path $Out 'runs'; New-Item -ItemType Directory -Force -Path $runs | Out-Null
    $exe = Get-Standin; $fail = 0
    $order = @(); for ($k = 1; $k -le $Pairs; $k++) { $ids = @('d0', 'd0e'); if ($k % 2 -eq 0) { $ids = @('d0e', 'd0') }; foreach ($id in $ids) { $order += , @($id, $k) } }
    Say ('dry runner order: ' + (($order | ForEach-Object { '{0}-r{1}' -f $_[0], $_[1] }) -join ', '))
    foreach ($o in $order) {
        $id = $o[0]; $k = $o[1]
        $base = Join-Path $runs ((Get-Date -Format 'HHmm') + "-$id-r$k"); $rd = $base; $i = 2
        while (Test-Path -LiteralPath $rd) { $rd = "$base-r$i"; $i++ }
        New-Item -ItemType Directory -Path $rd | Out-Null
        $se = Join-Path $rd 'pthrottle_standin.exe'; Copy-Item -LiteralPath $exe -Destination $se
        $p = Start-Process -FilePath $se -ArgumentList '8' -WindowStyle Hidden -PassThru; $null = $p.Handle
        $t0 = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
        Start-Sleep -Seconds 3
        $w = [PtDry]::Write($p.Handle, 4, 0)
        Start-Sleep -Seconds 2
        $late = [PtDry]::Read($p.Handle)
        $p.WaitForExit()
        $want = if ($id -eq 'd0e') { 'C=0x5 S=0x0' } else { 'C=0x4 S=0x0' }
        if ($w -ne 0 -or $late -ne $want) { $fail++ }
        Say ('dry run {0}: game-like Set C=0x4 (error {1}), 2 s later {2} (want {3}): {4}' -f (Split-Path -Leaf $rd), $w, $late, $want, $(if ($w -eq 0 -and $late -eq $want) { 'PASS' } else { 'FAIL' }))
        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add('t_s,epoch_s,fg_game,cpu_util_pct,p_eff_mhz,e_eff_mhz,p_util_pct,e_util_pct,tz_passive_min_pct')
        for ($t = 0; $t -le 5 + 55 + $MeasureS + 2; $t++) {
            $rel = $t - 2
            $slow = ($id -eq 'd0' -and (($k -eq 1 -and $rel -ge 40) -or ($k -eq 2 -and $rel -ge 80))) -or ($id -eq 'd0e' -and $k -eq 2 -and ($rel -eq 50 -or $rel -eq 51))
            $lines.Add([string]::Format($inv, '{0},{1:F3},0,90,1690,{2},99,{3},', $t, ($t0 + $t), $(if ($slow) { 550 } else { 1500 }), $(if ($slow) { 95 } else { 90 })))
        }
        Set-Content -LiteralPath (Join-Path $rd 'sys.csv') -Value $lines -Encoding ascii
        $j = [ordered]@{ status = 'ok'; tag = "$id-r$k"; run = $rd; dry_run = $true; first_frame_signal_s = 2.0; ff_signal_epoch_s = ($t0 + 2.0)
            env_set = @{}; exit_code = $p.ExitCode; dry_game_call_error = $w; dry_state_2s_after_game_call = $late }
        $j | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $rd 'run.json') -Encoding utf8
    }
    if ($fail) { return 1 }; return 0
}
