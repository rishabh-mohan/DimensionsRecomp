$ws = '<workspace>'
$src = Join-Path $ws 'build\agent3\gameplay\RUN-MANUAL.cmd'
$dir = Join-Path $ws 'build\agent10\gpchk2'
$t = [IO.File]::ReadAllText($src)
$launch = 'powershell -NoProfile -ExecutionPolicy Bypass -File "%GP%gameplay-run.ps1" manual %*'
if (-not $t.Contains($launch)) { 'launch line not found'; exit 9 }
$base = $t.Replace($launch, 'echo WOULD-LAUNCH')
$variants = [ordered]@{
    'a-untouched' = $base
    'b-badhex'    = $base.Replace('GPPIN_23=31C33A80', 'GPPIN_23=41C33A80')
    'c-renamed'   = $base.Replace('build\agent3\toypad\fake_listener.py', 'build\agent3\toypad\fake_listenerX.py')
}
foreach ($k in $variants.Keys) {
    if ($k -ne 'a-untouched' -and $variants[$k] -eq $base) { "$k : replacement did not apply"; exit 9 }
    [IO.File]::WriteAllText((Join-Path $dir "$k.cmd"), $variants[$k], [Text.Encoding]::ASCII)
}
function RunCmd([string]$name, [hashtable]$env) {
    $p = Join-Path $dir "$name.cmd"
    $psi = New-Object Diagnostics.ProcessStartInfo 'cmd.exe', "/c `"$p`""
    $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardInput = $true; $psi.CreateNoWindow = $true
    foreach ($e in $env.Keys) { $psi.EnvironmentVariables[$e] = $env[$e] }
    $pr = [Diagnostics.Process]::Start($psi); $pr.StandardInput.Close()
    $out = $pr.StandardOutput.ReadToEnd(); $pr.WaitForExit()
    $lines = ($out -split "`r?`n" | Where-Object { $_ -match 'PIN|pins ok|WOULD-LAUNCH|REFUSED|exit' }) -join ' | '
    "{0,-22} rc={1}  {2}" -f $name, $pr.ExitCode, ($lines -replace [regex]::Escape($ws), '<WS>')
}
RunCmd 'a-untouched' @{}
RunCmd 'b-badhex' @{}
RunCmd 'c-renamed' @{}
RunCmd 'a-untouched' @{ 'GPPIN_99' = 'X|Y' }
foreach ($k in $variants.Keys) { Remove-Item -LiteralPath (Join-Path $dir "$k.cmd") }
"copies left: $(@(Get-ChildItem $dir -Filter *.cmd).Count)"
