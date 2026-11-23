# Agent 7: syntax-only compile of every TU that includes gpu_native/device.h, against build/dev,
# at most -Throttle (default 2) compiler processes at a time, via env\compile-one.ps1.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\syntax_check_includers.ps1 <tag> [-Throttle 2] [-List build\agent7\device_h_includers.txt] [-Only a.cpp,b.cpp]
# Writes build\agent7\syntax-<tag>\<name>.log and summary.txt (exit code, error:/warning: counts, seconds).
param([string]$Tag = 'b2', [int]$Throttle = 2, [string]$List = 'build\agent7\device_h_includers.txt', [string]$Only = '')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location $root
$out = Join-Path $root "build\agent7\syntax-$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$tus = @(Get-Content $List | Where-Object { $_ -match '^dimensionsrecomp\\.*\.cpp$' })
if ($Only) { $want = $Only -split ','; $tus = @($tus | Where-Object { $want -contains [IO.Path]::GetFileName($_) }) }
$running = @{}
$done = @()
$queue = New-Object System.Collections.Queue
$tus | ForEach-Object { $queue.Enqueue($_) }
function Finish($tu, $p, $sw) {
  $name = [IO.Path]::GetFileNameWithoutExtension($tu)
  $log = Join-Path $out "$name.log"
  $text = (Get-Content "$log.out" -Raw -ErrorAction SilentlyContinue) + (Get-Content "$log.err" -Raw -ErrorAction SilentlyContinue)
  Set-Content -Path $log -Value $text
  Remove-Item "$log.out", "$log.err" -ErrorAction SilentlyContinue
  $err = ([regex]::Matches($text, '\berror:')).Count
  $warn = ([regex]::Matches($text, '\bwarning:')).Count
  '{0,-28} exit={1,-3} errors={2,-3} warnings={3,-4} {4,6:N1}s' -f ($name + '.cpp'), $p.ExitCode, $err, $warn, $sw.Elapsed.TotalSeconds
}
while ($queue.Count -or $running.Count) {
  while ($queue.Count -and $running.Count -lt $Throttle) {
    $tu = $queue.Dequeue()
    $name = [IO.Path]::GetFileNameWithoutExtension($tu)
    $log = Join-Path $out "$name.log"
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $root 'env\compile-one.ps1'), $tu,
                 '-OutDir', 'build\agent7\obj', '-Db', 'build\dev\compile_commands.json', '-SyntaxOnly')
    $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -WorkingDirectory $root -NoNewWindow -PassThru `
         -RedirectStandardOutput "$log.out" -RedirectStandardError "$log.err"
    $null = $p.Handle  # keep the handle so ExitCode is available after exit
    $running[$tu] = @{ p = $p; sw = [Diagnostics.Stopwatch]::StartNew() }
  }
  Start-Sleep -Milliseconds 500
  foreach ($tu in @($running.Keys)) {
    $r = $running[$tu]
    if ($r.p.HasExited) {
      $r.p.WaitForExit()
      $line = Finish $tu $r.p $r.sw
      $done += $line
      Write-Output $line
      $running.Remove($tu)
    }
  }
}
$done | Sort-Object | Set-Content -Path (Join-Path $out 'summary.txt')
'TUs={0} failed={1}' -f $done.Count, @($done | Where-Object { $_ -notmatch 'exit=0 ' }).Count
