# Agent 2 - produce the top-level generated headers of build/dev (generated/*.h, generated/**/shaders/*.h)
# for compile-one, WITHOUT building through ninja (their edges carry order-only deps on SDK targets, and no
# SDK targets may be built in the dev tree). Runs each edge's OWN command ("ninja -t commands -s") only if it
# is a dxc.exe or "cmake -P" command (no clang, no rexglue, no linker). Writes only under build/dev.
# No .ninja_log is touched: ninja regenerates these (identically) the first time build/dev is really built.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\dev-gen-headers.ps1
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$D = "$R\build\dev"
Set-Location $D
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2\dev-gen-headers.log"
"$(Get-Date -Format HH:mm:ss) start" | Out-File -Encoding utf8 $log
$hdrs = @(Select-String -Path "$D\build.ninja" -Pattern '^build (generated/[^ :|$]+\.(h|hpp|inc))[ :|]' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
$fail = 0; $done = @{}
foreach ($h in $hdrs) {
    $cmd = @(& ninja -C $D -t commands -s $h)
    $ok = $cmd.Count -eq 1 -and ($cmd[0] -match 'dxc\.exe' -or $cmd[0] -match 'cmake\.exe"? -P ') -and
          $cmd[0] -notmatch 'clang|rexglue|lld-link|ninja\.exe'
    if (-not $ok) { "SKIP $h : not a single dxc / cmake -P command ($($cmd.Count) lines)" | Out-File -Append -Encoding utf8 $log; $fail++; continue }
    if (-not $done.ContainsKey($cmd[0])) {
        $dir = Split-Path -Parent (Join-Path $D $h)
        New-Item -ItemType Directory -Force $dir | Out-Null
        cmd /d /c $cmd[0] >> $log 2>&1
        $done[$cmd[0]] = $LASTEXITCODE
    }
    $c = $done[$cmd[0]]; $exists = Test-Path (Join-Path $D $h)
    "$(Get-Date -Format HH:mm:ss) $h exit=$c exists=$exists" | Out-File -Append -Encoding utf8 $log
    if ($c -ne 0 -or -not $exists) { $fail++ }
}
"$(Get-Date -Format HH:mm:ss) done: $($hdrs.Count) headers, $fail failed" | Out-File -Append -Encoding utf8 $log
exit $fail
