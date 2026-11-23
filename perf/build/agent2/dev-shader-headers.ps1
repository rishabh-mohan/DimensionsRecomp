# Agent 2 - produce build/dev/generated/gpu_native/shaders/*.h for compile-one WITHOUT building through ninja.
# "ninja -t commands" shows these 9 dxc custom commands carry order-only deps on the SDK targets (closure
# of 1140 commands, 1131 non-dxc), and no SDK targets may be built in the dev tree. So this runs each
# edge's OWN command only ("ninja -t commands -s"), after checking it is a dxc command. No .ninja_log is
# touched: ninja will simply regenerate these (identically) the first time build/dev is really built.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\dev-shader-headers.ps1
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$D = "$R\build\dev"
Set-Location $D
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2\dev-shader-headers.log"
"$(Get-Date -Format HH:mm:ss) start" | Out-File -Encoding utf8 $log
$hdrs = @(Select-String -Path "$D\build.ninja" -Pattern '^build (generated/gpu_native/shaders/[^ :|$]+\.h)' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
$fail = 0
foreach ($h in $hdrs) {
    $cmd = @(& ninja -C $D -t commands -s $h)
    if ($cmd.Count -ne 1 -or $cmd[0] -notmatch 'dxc\.exe') {
        "SKIP $h : not a single dxc command ($($cmd.Count) lines)" | Out-File -Append -Encoding utf8 $log; $fail++; continue
    }
    $dir = Split-Path -Parent (Join-Path $D $h)
    New-Item -ItemType Directory -Force $dir | Out-Null
    cmd /d /c $cmd[0] >> $log 2>&1
    $c = $LASTEXITCODE
    $ok = Test-Path (Join-Path $D $h)
    "$(Get-Date -Format HH:mm:ss) $h exit=$c exists=$ok" | Out-File -Append -Encoding utf8 $log
    if ($c -ne 0 -or -not $ok) { $fail++ }
}
"$(Get-Date -Format HH:mm:ss) done: $($hdrs.Count) headers, $fail failed" | Out-File -Append -Encoding utf8 $log
exit $fail
