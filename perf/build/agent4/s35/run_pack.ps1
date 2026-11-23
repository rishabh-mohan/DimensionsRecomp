<#
  run_pack.ps1 - Agent 4, build\agent4\s35: scratch AOT pack for the placement shaders
  (task (b), notes S3.5). Compiles, indexes and checks offline. Nothing is applied, built or staged.

  Approval (Agent 1, 2026-11-22 06:14): scratch only, in build\agent4\s35\; <=2 threads at BelowNormal;
  no live apply, no bin; no writes to the game/SDK trees, the generated junction or any bin dir;
  stop by 08:25. Gates: (1) Agent 7 cleared the PS words (06:22); (2) Agent 8 confirms its last run
  has ended (~07:30). Pass -Go, with -GateEvidence, only when both are met.

  Each run writes to a new build\agent4\s35\run-HHmmss\ directory, and TMP/TEMP point inside it.
  Inputs, tools, the old index and the main cache are hash-pinned and re-checked after the run.
  The top level of every watched directory outside s35 is listed before and after the run.

  Usage (from the workspace root):
    powershell -NoProfile -ExecutionPolicy Bypass -File build\agent4\s35\run_pack.ps1 -PlanOnly [-Mask 2]
    powershell -NoProfile -ExecutionPolicy Bypass -File build\agent4\s35\run_pack.ps1 -Go -GateEvidence "Agent 8 HH:MM: last run ended"
#>
param(
    [switch]$PlanOnly,
    [switch]$Go,
    [string]$GateEvidence = '',
    [long]$Mask = 3,
    [datetime]$NotAfter = '2026-11-22T08:05:00'
)
$ErrorActionPreference = 'Stop'
$W = '<workspace>'
$S35 = Join-Path $W 'build\agent4\s35'
$Stamp = Get-Date -Format 'HHmmss'
$QuietStart = [datetime]'2026-11-22T06:33:00'
$QuietEnd = [datetime]'2026-11-22T07:15:00'

if ($PlanOnly -eq $Go) { Write-Host 'Pass exactly one of -PlanOnly or -Go.'; exit 2 }
if ($Go -and -not $GateEvidence) { Write-Host '-Go needs -GateEvidence (who confirmed gate 2, and when).'; exit 2 }
$cpus = 0
for ($b = $Mask; $b -ne 0; $b = $b -shr 1) { if ($b -band 1) { $cpus++ } }
if ($cpus -lt 1 -or $cpus -gt 2) { Write-Host ('Mask 0x{0:X} allows {1} CPUs; the limit is 2.' -f $Mask, $cpus); exit 2 }

# Self-limit first: every child process inherits BelowNormal and this affinity mask.
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$me.ProcessorAffinity = [IntPtr]$Mask

$DumpDir = Join-Path $W 'build\agent8\matrix\20261122-0509\runs\0509-sd-r1\shader-dumps\placement-containers'
$Inputs = [ordered]@{
    'vs-ACAF01F01E1C03D2.bin' = '6C4F65C3161DF6BEE23F9C551F34971D60275BB49C3DB6327CFF9084F4317A66'
    'ps-75A4D1ABA62F7594.bin' = '09D05274AFBC26A2605D0B91E5C2A0E0C95303C4C0C84F4D463105EB678D66EE'
    'vs-CCD7655302B54D80.bin' = 'F4EE30B28DEE9E4AB5AE2E9204D54195A0AC9D8D5497B7F2C8FAC11D90EEC65E'
    'ps-E81FD692C3AB35E1.bin' = '58B4FA21E35500529895AA400F4B307F0DD09BBBBDB71F5C7C8E8748B31170F1'
}
$Pins = [ordered]@{
    gradient   = @('build\agent6\aot\gradient-build\gradient_compiler.exe', '705980C4F6071E9B675DFBB57A33ED64C0C74BA6F8172FD7094850A76371A653')
    dxcompiler = @('build\agent6\aot\gradient-build\dxcompiler.dll', '0689E2FEE0A1C9DF8662A59680469F24E2A3AD7CE6BBBCC9284F7A83172BFC59')
    dxil       = @('build\agent6\aot\gradient-build\dxil.dll', '64BE2368211D257A038A7D4EA6BB3E24C878EB8D588C7B8414FCCF759B69C2AC')
    fmt        = @('build\agent6\aot\gradient-build\fmt.dll', 'BB89FF51186F9E8F8F7CAE69E5A229C9D1D322562B033C0D8DD35071434A1FE5')
    common     = @('DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h', '362E9EDBA0B9E4AC156982E7D75A70AF1341C6E1F1F52139BE03978DB3AA1E8F')
    indexer    = @('build\agent6\aot\microcode-index\lego_gpu_microcode_index.exe', '3B5A68FE447DF23D46BCFF7913E590A8AF4A14A2FBBE28453B17EB23144BB9A1')
    oldindex   = @('build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\lego-microcode-index.cpp', '2DB859177B4656477D2858B87F37E7F068CABA420362FA21AFA1B3C8C6DD13A2')
    maincache  = @('build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\aot\lego-dxil-cache.cpp', 'FF9386C1CD435E7EE12781F43A6F42F97AED7062A4147D4E649AF2450157A819')
    merge      = @('DimensionsRecomp\tools\gpu-aot\merge_microcode_index.py', '20986E998AB8B6F83FC0390A15A45DABB86F37E81206A9ED06D06E205DDB1BE2')
    lookup     = @('DimensionsRecomp\tools\gpu-aot\test_placement_capture_lookup.py', '856D0A8E0E827D6AECF99FC0D34DDCCB0FE0F182D9EE372A20048FDC3350058B')
    archive    = @('DimensionsRecomp\rexlego\src\gpu_native\shader_archive.cpp', '1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC')
    archiveh   = @('DimensionsRecomp\rexlego\src\gpu_native\shader_archive.h', '83B030F92C504D1FF5AD554371745A8DA38C52310B290DA9246A212CC3F743D5')
    snaparch   = @('build\agent2\snap1\DimensionsRecomp\rexlego\src\gpu_native\shader_archive.cpp', '1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC')
    checker    = @('build\agent4\s35\check_pack.py', '')
    wrapper    = @('build\agent4\s35\run_lookup.py', '')
}
# Read-only directories outside s35 whose top level must not change during the run.
$Watch = @(
    'build\agent6\aot\gradient-build',
    'build\agent6\aot\microcode-index',
    'build\agent8\matrix\20261122-0509\runs\0509-sd-r1\shader-dumps',
    'build\agent8\matrix\20261122-0509\runs\0509-sd-r1\shader-dumps\placement-containers',
    'DimensionsRecomp\rexlego\out\native-gpu',
    'DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source',
    'DimensionsRecomp\rexlego\src\gpu_native',
    'DimensionsRecomp\tools\gpu-aot',
    'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu',
    'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\aot',
    'build\agent2\native3d-bin'
)

function PinPath([string]$Key) { return (Join-Path $W $Pins[$Key][0]) }

# Windows PowerShell 5.1 turns redirected native stderr into a terminating error under 'Stop';
# capture native output with a function-local 'Continue' instead.
$script:NativeRc = $null
function Get-NativeOutput([string]$Exe, [string[]]$ArgList) {
    $ErrorActionPreference = 'Continue'
    $o = @(& $Exe @ArgList 2>&1 | ForEach-Object { "$_" })
    $script:NativeRc = $LASTEXITCODE
    return , $o
}

$script:LogPath = $null
function Log([string]$Text) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $Text
    Write-Host $line
    if ($script:LogPath) { [System.IO.File]::AppendAllText($script:LogPath, $line + "`r`n", [System.Text.Encoding]::ASCII) }
}

function Assert-InS35([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($S35 + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "refusing to write outside build\agent4\s35: $full"
    }
    return $full
}

function Test-Pins([bool]$Strict) {
    $bad = 0
    foreach ($k in $Pins.Keys) {
        $rel = $Pins[$k][0]; $want = $Pins[$k][1]
        $p = Join-Path $W $rel
        if (-not (Test-Path -LiteralPath $p)) { Log "PIN  $k MISSING $rel"; $bad++; continue }
        $got = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
        $ok = (-not $want) -or ($got -eq $want)
        $tag = 'ok  '
        if (-not $want) { $tag = 'logd' } elseif (-not $ok) { $tag = 'FAIL' }
        Log ('PIN  {0,-10} {1} {2} {3}' -f $k, $tag, $got, $rel)
        if (-not $ok) { $bad++ }
    }
    foreach ($n in $Inputs.Keys) {
        $p = Join-Path $DumpDir $n
        if (-not (Test-Path -LiteralPath $p)) { Log "IN   $n MISSING"; $bad++; continue }
        $got = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
        $ok = $got -eq $Inputs[$n]
        Log ('IN   {0,-24} {1} {2}' -f $n, $(if ($ok) { 'ok  ' } else { 'FAIL' }), $got)
        if (-not $ok) { $bad++ }
    }
    if ($bad -and $Strict) { throw "$bad pinned file(s) missing or changed" }
    return $bad
}

function Get-Listing([string[]]$Dirs) {
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($d in $Dirs) {
        $p = Join-Path $W $d
        if (-not (Test-Path -LiteralPath $p)) { $out.Add("$d|MISSING"); continue }
        foreach ($i in Get-ChildItem -LiteralPath $p -Force) {
            $len = '<dir>'
            if (-not $i.PSIsContainer) { $len = [string]$i.Length }
            $out.Add(('{0}\{1}|{2}|{3}' -f $d, $i.Name, $len, $i.LastWriteTimeUtc.Ticks))
        }
    }
    return , $out.ToArray()
}

function Invoke-Tool {
    param([string]$Name, [string]$Exe, [string[]]$ArgList, [string]$Cwd, [int]$TimeoutSec = 600)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = (($ArgList | ForEach-Object { '"' + $_ + '"' }) -join ' ')
    $psi.WorkingDirectory = $Cwd
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    Log "RUN  $Name : `"$Exe`" $($psi.Arguments)"
    $t0 = Get-Date
    $p = [System.Diagnostics.Process]::Start($psi)
    try {
        $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
        $p.ProcessorAffinity = [IntPtr]$Mask
        Log ('     {0} pid={1} priority={2} affinity=0x{3:X}' -f $Name, $p.Id, $p.PriorityClass, [long]$p.ProcessorAffinity)
    } catch { Log "     $Name priority/affinity not re-set (inherited from the script): $($_.Exception.Message)" }
    $so = $p.StandardOutput.ReadToEndAsync()
    $se = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($TimeoutSec * 1000)) {
        Log "FAIL $Name timed out after $TimeoutSec s; killing its process tree"
        & cmd.exe /d /c "taskkill /PID $($p.Id) /T /F >nul 2>&1"
        [void]$p.WaitForExit(30000)
    }
    $p.WaitForExit()
    $wall = ((Get-Date) - $t0).TotalSeconds
    $cpu = -1
    try { $cpu = $p.TotalProcessorTime.TotalSeconds } catch { }
    [System.IO.File]::WriteAllText((Join-Path $script:LogDir "$Name.stdout.txt"), $so.Result)
    [System.IO.File]::WriteAllText((Join-Path $script:LogDir "$Name.stderr.txt"), $se.Result)
    Log ('DONE {0} exit={1} wall_s={2:N1} cpu_s(parent)={3:N1}' -f $Name, $p.ExitCode, $wall, $cpu)
    return [int]$p.ExitCode
}

# ---------------------------------------------------------------- preflight
$s35Item = Get-Item -LiteralPath $S35 -Force
if ($s35Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 's35 is a reparse point; refusing' }
if ($PlanOnly) {
    $script:LogPath = Assert-InS35 (Join-Path $S35 "plan-$Stamp.txt")
} else {
    $Run = Assert-InS35 (Join-Path $S35 "run-$Stamp")
    if (Test-Path -LiteralPath $Run) { throw "$Run already exists" }
    $In = Assert-InS35 (Join-Path $Run 'runtime-input')
    $script:LogDir = Assert-InS35 (Join-Path $Run 'logs')
    $Hlsl = Assert-InS35 (Join-Path $Run 'hlsl')
    $Work = Assert-InS35 (Join-Path $Run 'work')
    $Tmp = Assert-InS35 (Join-Path $Run 'tmp')
    $CacheOut = Assert-InS35 (Join-Path $Run 'runtime-cache.cpp')
    $AddOut = Assert-InS35 (Join-Path $Run 'index-addition.cpp')
    $IndexOut = Assert-InS35 (Join-Path $Run 'lego-microcode-index.cpp')
    $MergeReport = Assert-InS35 (Join-Path $Run 'merge-report.json')
    $LookupOut = Assert-InS35 (Join-Path $Run 'lookup')
    $LookupMainOut = Assert-InS35 (Join-Path $Run 'lookup-main')
    $CheckOut = Assert-InS35 (Join-Path $Run 'pack-check.json')
    foreach ($d in $Run, $In, $script:LogDir, $Hlsl, $Work, $Tmp) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    $script:LogPath = Join-Path $Run 'pack-log.txt'
}
$mode = 'Go'
if ($PlanOnly) { $mode = 'PlanOnly' }
Log ('run_pack.ps1 mode={0} pid={1} priority={2} affinity=0x{3:X} ({4} CPUs) ps={5}' -f $mode, $PID, $me.PriorityClass, [long]$me.ProcessorAffinity, $cpus, $PSVersionTable.PSVersion)
Log "script sha256=$((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash)"
Log 'gate 1: Agent 7 cleared the PS words at 06:22 (build\agent7\sd\ps-words-check.txt)'
if ($Go) { Log "gate 2: $GateEvidence" } else { Log 'gate 2: not claimed (PlanOnly)' }
$now = Get-Date
$inQuiet = ($now -ge $QuietStart) -and ($now -lt $QuietEnd)
Log "time window: now=$($now.ToString('HH:mm:ss')) quiet(06:33-07:15)=$inQuiet notAfter=$($NotAfter.ToString('HH:mm'))"
if ($Go -and $inQuiet) { throw 'inside the 06:33-07:15 quiet window: no compiles' }
if ($Go -and $now -gt $NotAfter) { throw "after $($NotAfter.ToString('HH:mm')): too close to the 08:25 stop" }

$badPins = Test-Pins -Strict $Go.IsPresent
. (Join-Path $W 'env\devshell.ps1') -Jobs 1 -Quiet
$clang = Get-Command clang++ -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $clang) { throw 'clang++ is not on PATH after env\devshell.ps1' }
Log "clang++ = $($clang.Source) | $((Get-NativeOutput $clang.Source @('--version')) | Select-Object -First 1)"
$py = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
Log "python = $py | $((Get-NativeOutput $py @('--version')) | Select-Object -First 1)"

if ($PlanOnly) {
    Log "precheck of the pinned inputs in place (read-only): $DumpDir"
    $pre = Get-NativeOutput $py @((PinPath 'checker'), 'precheck', $DumpDir)
    $preRc = $script:NativeRc
    foreach ($l in $pre) { Log "     $l" }
    Log 'plan for -Go (all outputs under build\agent4\s35\run-HHmmss\):'
    Log '  1 stage the 4 containers into runtime-input\ and re-verify sha256; precheck'
    Log '  2 gradient_compiler.exe runtime-input runtime-cache.cpp shader_common.h  (XENOS_RECOMP_DXIL_ONLY=1, XENOS_RECOMP_HLSL_DUMP=hlsl\)'
    Log '  3 lego_gpu_microcode_index.exe index-addition.cpp runtime-input'
    Log '  4 merge_microcode_index.py <snap1 index 2DB85917> index-addition.cpp lego-microcode-index.cpp --report merge-report.json'
    Log '  4b check_pack.py prelookup (static checks; no lookup is started unless they pass)'
    Log '  5 run_lookup.py test_placement_capture_lookup.py runtime-input lego-microcode-index.cpp runtime-cache.cpp lookup\'
    Log '  6 the same with --main-cache <snap1 lego-dxil-cache.cpp FF9386C1> into lookup-main\'
    Log '  7 check_pack.py post; re-check the pins; listing diff of the watched dirs; SHA256SUMS.txt'
    $ok = ($badPins -eq 0) -and ($preRc -eq 0)
    Log "PLAN $(if ($ok) { 'OK' } else { 'NOT OK' }) (bad pins/inputs: $badPins, precheck exit: $preRc)"
    if ($ok) { exit 0 } else { exit 1 }
}

# ---------------------------------------------------------------- Go
$OrigTmp = $env:TMP
$OrigTemp = $env:TEMP
$env:TMP = $Tmp
$env:TEMP = $Tmp
$before = Get-Listing $Watch
$Failed = $null
$rcCheck = $null
try {
    # 1. stage
    foreach ($n in $Inputs.Keys) {
        $dst = Assert-InS35 (Join-Path $In $n)
        Copy-Item -LiteralPath (Join-Path $DumpDir $n) -Destination $dst
        $h = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
        if ($h -ne $Inputs[$n]) { throw "staged $n has sha256 $h, not the pinned value" }
        Log "staged $n $h"
    }
    $rc = Invoke-Tool 'precheck' $py @((PinPath 'checker'), 'precheck', $In) $Work 120
    if ($rc -ne 0) { throw "precheck failed (exit $rc)" }

    # 2. compile the 4 containers (DXIL only)
    $env:XENOS_RECOMP_DXIL_ONLY = '1'
    $env:XENOS_RECOMP_HLSL_DUMP = $Hlsl
    try { $rc = Invoke-Tool 'gradient' (PinPath 'gradient') @($In, $CacheOut, (PinPath 'common')) $Work 900 }
    finally { Remove-Item Env:XENOS_RECOMP_DXIL_ONLY, Env:XENOS_RECOMP_HLSL_DUMP -ErrorAction SilentlyContinue }
    if ($rc -ne 0 -or -not (Test-Path -LiteralPath $CacheOut)) { throw "gradient_compiler failed (exit $rc)" }

    # 3. index rows for the 4 containers only
    $rc = Invoke-Tool 'indexer' (PinPath 'indexer') @($AddOut, $In) $Work 120
    if ($rc -ne 0) { throw "indexer failed (exit $rc)" }

    # 4. merge into the index native3d-bin was built with (snap1 copy)
    $rc = Invoke-Tool 'merge' $py @((PinPath 'merge'), (PinPath 'oldindex'), $AddOut, $IndexOut, '--report', $MergeReport) $Work 120
    if ($rc -ne 0) { throw "merge failed (exit $rc)" }

    # 4b. static checks first: a failed lookup ends in std::abort, so start none that cannot pass
    $rc = Invoke-Tool 'prelookup' $py @((PinPath 'checker'), 'prelookup', $Run, '--old-index', (PinPath 'oldindex')) $Work 300
    if ($rc -ne 0) { throw "prelookup checks failed (exit $rc); no lookup started" }

    # 5. production lookup against the new runtime cache
    $rc = Invoke-Tool 'lookup' $py @((PinPath 'wrapper'), (PinPath 'lookup'), $In, $IndexOut, $CacheOut, $LookupOut) $Work 600
    if ($rc -ne 0) { throw "lookup failed (exit $rc)" }

    # 6. the same with the main archive exposed too, as gameplay does
    $rc = Invoke-Tool 'lookup-main' $py @((PinPath 'wrapper'), (PinPath 'lookup'), $In, $IndexOut, $CacheOut, $LookupMainOut, '--main-cache', (PinPath 'maincache')) $Work 600
    if ($rc -ne 0) { throw "lookup-main failed (exit $rc)" }
} catch {
    $Failed = $_.Exception.Message
    Log "FAIL $Failed"
} finally {
    $env:TMP = $OrigTmp
    $env:TEMP = $OrigTemp
    $after = Get-Listing $Watch
    $diff = @(Compare-Object -ReferenceObject $before -DifferenceObject $after)
    $sideFile = Join-Path $Run 'side-effects.txt'
    if ($diff.Count) {
        [System.IO.File]::WriteAllLines($sideFile, [string[]]($diff | ForEach-Object { '{0} {1}' -f $_.SideIndicator, $_.InputObject }))
        Log "WARN side effects: $($diff.Count) listing change(s) in the watched dirs outside s35 (side-effects.txt)"
    } else {
        [System.IO.File]::WriteAllText($sideFile, "none: the top level of all $($Watch.Count) watched dirs is unchanged`r`n")
        Log "side effects: none (top level of $($Watch.Count) watched dirs unchanged)"
    }
    $tmpFiles = @(Get-ChildItem -LiteralPath $Tmp -Recurse -Force -File -ErrorAction SilentlyContinue)
    Log "tmp: $($tmpFiles.Count) file(s) left in run\tmp"
    $badAfter = Test-Pins -Strict $false
    if (Test-Path -LiteralPath $AddOut) {
        $rcCheck = Invoke-Tool 'check' $py @((PinPath 'checker'), 'post', $Run, '--old-index', (PinPath 'oldindex'), '--main-cache', (PinPath 'maincache'), '--out', $CheckOut) $Work 300
        foreach ($l in (Get-Content -LiteralPath (Join-Path $script:LogDir 'check.stdout.txt'))) { Log "     $l" }
    }
    $verdict = 'FAIL'
    if ((-not $Failed) -and ($rcCheck -eq 0) -and ($diff.Count -eq 0) -and ($badAfter -eq 0)) { $verdict = 'PASS' }
    $sums = Get-ChildItem -LiteralPath $Run -Recurse -File |
        Where-Object { -not $_.FullName.StartsWith($Tmp + '\', [System.StringComparison]::OrdinalIgnoreCase) -and $_.Name -ne 'SHA256SUMS.txt' -and $_.Name -ne 'pack-log.txt' } |
        Sort-Object FullName |
        ForEach-Object { '{0}  {1}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash, $_.FullName.Substring($Run.Length + 1) }
    [System.IO.File]::WriteAllLines((Join-Path $Run 'SHA256SUMS.txt'), [string[]]$sums)
    [System.IO.File]::WriteAllText((Assert-InS35 (Join-Path $S35 'LATEST.txt')), ('run-{0} {1} {2}{3}' -f $Stamp, $verdict, (Get-Date -Format 'HH:mm:ss'), "`r`n"))
    Log ('VERDICT {0} (tools: {1}; check exit: {2}; side effects: {3}; pins changed after: {4})' -f $verdict, $(if ($Failed) { $Failed } else { 'ok' }), $rcCheck, $diff.Count, $badAfter)
}
if ($verdict -eq 'PASS') { exit 0 } else { exit 1 }
