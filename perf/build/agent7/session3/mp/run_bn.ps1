# run_bn.ps1 OUTFILE SCRIPT ARGS... : runs `python -B SCRIPT ARGS` at BelowNormal priority,
# writes stdout+stderr and the exit code to OUTFILE (used to produce the offline-*.out.txt files).
param([string]$Out, [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
$tmpE = "$Out.err.tmp"
$argl = @('-B') + ($Rest | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })
$p = Start-Process python -ArgumentList $argl -NoNewWindow -PassThru -RedirectStandardOutput $Out -RedirectStandardError $tmpE
$null = $p.Handle  # keep the handle so ExitCode is available
try { $p.PriorityClass = 'BelowNormal' } catch {}
$p.WaitForExit()
$rc = $p.ExitCode
$cmd = 'python ' + ($argl -join ' ')
$body = Get-Content $Out -Raw
$err = Get-Content $tmpE -Raw
Set-Content -Path $Out -Value ("`$ $cmd`n" + $body + $err + "[exit code $rc]") -Encoding utf8
Remove-Item $tmpE -ErrorAction SilentlyContinue
"exit=$rc"
