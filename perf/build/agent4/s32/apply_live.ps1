# Task #12 step 2: hash-guarded write of the live draw.cpp (run ONLY at Agent 1's GO, after Agent 10 rates it SAFE).
# -DryRun checks every precondition and writes nothing.
param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$live = Join-Path $root 'DimensionsRecomp\rexlego\src\gpu_native\draw.cpp'
$patched = Join-Path $root 'build\agent4\s32\draw.cpp'
$backup = Join-Path $root 'build\agent4\scratch\draw.before-s32.cpp'
$patch = Join-Path $root 'build\agent4\s32\draw-s32.patch'
$before = '50AA3B1DEE61567838076EDF19CB7A5466727C3CC31BE3A80E6DCC3722D7BDD6'
$after = '5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410'
$sha = [Security.Cryptography.SHA256]::Create()
function Hash([byte[]]$b) { ([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-', '') }

$liveBytes = [IO.File]::ReadAllBytes($live)
$newBytes = [IO.File]::ReadAllBytes($patched)
if ((Hash $liveBytes) -ne $before) { throw "live draw.cpp is $(Hash $liveBytes), expected $before; NOT writing" }
if ((Hash $newBytes) -ne $after) { throw "patched copy is $(Hash $newBytes), expected $after; NOT writing" }
"preconditions OK: live $($before.Substring(0,8)) ($($liveBytes.Length) B), patched copy $($after.Substring(0,8)) ($($newBytes.Length) B)"
if ($DryRun) { 'dry run: nothing written'; exit 0 }

[IO.File]::WriteAllBytes($backup, $liveBytes)
if ((Hash ([IO.File]::ReadAllBytes($backup))) -ne $before) { throw "backup hash mismatch; NOT writing live" }
"backup: $backup"
# Re-read right before the write, in case the file changed during the backup.
if ((Hash ([IO.File]::ReadAllBytes($live))) -ne $before) { throw 'live draw.cpp changed during the backup; NOT writing' }
[IO.File]::WriteAllBytes($live, $newBytes)
$check = [IO.File]::ReadAllBytes($live)
$got = Hash $check
$item = Get-Item $live
$crlf = ([regex]::Matches([Text.Encoding]::UTF8.GetString($check), "`r`n")).Count
"live now: $got  $($check.Length) B  $crlf CRLF lines  mtime $($item.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
if ($got -ne $after) { throw "live hash after the write is $got, expected $after" }
Push-Location (Join-Path $root 'DimensionsRecomp')
try {
    & git --no-optional-locks apply --check -R $patch
    "git apply --check -R (read-only): rc=$LASTEXITCODE"
    & git --no-optional-locks diff HEAD --numstat -- rexlego/src/gpu_native/draw.cpp
} finally { Pop-Location }
'WRITE OK'
