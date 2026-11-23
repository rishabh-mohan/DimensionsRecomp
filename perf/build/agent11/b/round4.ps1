# Round 4 (helper B): final SDK shapes (steady_clock deadlines) + A/A controls.
$ErrorActionPreference = 'Continue'
$b = 'build\agent11\b'
function St([string]$tag) {
  $bat = (Get-CimInstance Win32_Battery).BatteryStatus
  $ld = (Get-CimInstance Win32_Processor).LoadPercentage
  '[status {0}] {1} BatteryStatus={2} (2=AC) LoadPercentage={3}' -f $tag, (Get-Date -Format 'HH:mm:ss'), $bat, $ld
}
function Run([string]$out, [string]$exe, [string[]]$a) {
  $f = Join-Path $b $out
  (St 'pre') | Out-File -FilePath $f -Encoding utf8
  ("[cmd] {0} {1}" -f $exe, ($a -join ' ')) | Out-File -FilePath $f -Encoding utf8 -Append
  $t0 = Get-Date
  & (Join-Path $b $exe) @a 2>&1 | Out-File -FilePath $f -Encoding utf8 -Append
  ("[wall] {0:N1} s" -f ((Get-Date) - $t0).TotalSeconds) | Out-File -FilePath $f -Encoding utf8 -Append
  (St 'post') | Out-File -FilePath $f -Encoding utf8 -Append
  "done $out"
}
Run 'cs_paired_3.txt' 'bench_cs.exe' @('paired', '300', '20000', 'old,timecas:5000,time:5000,old#aa')
Run 'sl_paired_3.txt' 'bench_spinlock.exe' @('paired', '300', '20000', 'old,ttast:10000,old#aa')
Run 'cs_contended_4.txt' 'bench_cs.exe' @('contended', '5', '100', '50,500,2000,5000', 'old,timecas:5000', 'none,pp,ee,pe', '200')
Run 'sl_contended_3.txt' 'bench_spinlock.exe' @('contended', '9', '150', '100', 'old,ttast:5000,ttast:10000', 'none,pp,ee,pe', '500', '20000', '200')
