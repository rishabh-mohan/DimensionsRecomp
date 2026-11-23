# Agent 9: build "pin + Agent 9 codegen" tools without rebuilding the runtime.
#
# The tool is the pin SDK (baseline/DimensionsRecomp/rexglue-sdk, built by Agent 2 in build/sdk)
# with only the Agent 9-owned codegen sources/headers taken from the dev tree:
#   src/codegen/**, src/rexglue/**, include/rex/codegen/**, include/rex/ppc/context.h
# Everything else (runtime headers, thirdparty, generated templates, runtime/thirdparty libraries)
# is the pin's, so the ABI matches the pin rexruntime.dll that rexglue.exe loads. The dev tree's
# other agents' runtime edits (logging, xmemory, ...) are deliberately NOT part of this tool.
#
# Outputs (build/agent9/bin): rexglue.exe, regression_interior_entries.exe, rexruntime.dll, TracyClient.dll
# Incremental: re-run after edits; robocopy keeps timestamps and ninja rebuilds only changed TUs.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\build-tool2.ps1 [-Jobs 2] [-Stage build\agent9\stage]
param([int]$Jobs = 2, [string]$Stage = '')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$pinSdk = "$R\baseline\DimensionsRecomp\rexglue-sdk"
$devSdk = "$R\DimensionsRecomp\rexglue-sdk"
$pinBuild = "$R\build\sdk"
$pinOut = "$pinSdk\out\win-amd64\Release"
$work = "$R\build\agent9\tool"
$wsdk = "$work\sdk"
$obj = "$work\obj"
$outBin = "$R\build\agent9\bin"
$logs = "$R\build\agent9\logs"
New-Item -ItemType Directory -Force $work, $obj, $outBin, $logs | Out-Null
. "$R\env\devshell.ps1" 6>$null | Out-Null
# Hold Agent 9 CPU slots for the whole build (2 slots at -Jobs 2); this also serializes two builds.
. "$R\bench\agent9\slots.ps1"
$held = Enter-Agent9Slots ([Math]::Max(1, [Math]::Min(2, $Jobs)))
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -Append -FilePath "$logs\build-tool2-steps.txt" }
$total = [Diagnostics.Stopwatch]::StartNew()

# 1. Overlay tree: pin src/include, then the Agent 9-owned dev parts on top.
robocopy "$pinSdk\include" "$wsdk\include" /MIR /XD "$pinSdk\include\rex\codegen" /NFL /NDL /NJH /NJS /NP | Out-Null
robocopy "$devSdk\include\rex\codegen" "$wsdk\include\rex\codegen" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
robocopy "$devSdk\include\rex\ppc" "$wsdk\include\rex\ppc" context.h /NFL /NDL /NJH /NJS /NP | Out-Null
robocopy "$pinSdk\src" "$wsdk\src" /MIR /XD "$pinSdk\src\codegen" "$pinSdk\src\rexglue" /NFL /NDL /NJH /NJS /NP | Out-Null
foreach ($d in 'codegen', 'rexglue') {
    robocopy "$devSdk\src\$d" "$wsdk\src\$d" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
}
New-Item -ItemType Directory -Force "$wsdk\tests\regression" | Out-Null
robocopy "$devSdk\tests\regression" "$wsdk\tests\regression" emit_interior_entries.cpp /NFL /NDL /NJH /NJS /NP | Out-Null

# 1b. Staged files (-Stage <dir> holding SDK-relative paths, e.g. build\agent9\stage\src\codegen\...)
#     override the dev copies. Used while DimensionsRecomp/** is frozen (S1 snapshot).
if ($Stage) {
    $Stage = (Resolve-Path $Stage).Path
    Get-ChildItem $Stage -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($Stage.Length).TrimStart('\')
        $dst = Join-Path $wsdk $rel
        New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
        Copy-Item $_.FullName $dst -Force
        Note "stage: $rel"
    }
}
# 1c. robocopy/Copy-Item keep the source's (older) timestamps, so a dev<->stage flip could hide a
#     content change from ninja. Touch every overlay input whose content changed since the last run.
$hashFile = "$work\inputs.sha.txt"
$old = @{}
if (Test-Path $hashFile) { Get-Content $hashFile | ForEach-Object { $kv = $_ -split '\|', 2; $old[$kv[0]] = $kv[1] } }
$now = Get-Date; $new = New-Object System.Collections.ArrayList; $touched = 0
foreach ($d in @("$wsdk\src\codegen", "$wsdk\src\rexglue", "$wsdk\include\rex\codegen", "$wsdk\include\rex\ppc", "$wsdk\tests\regression")) {
    Get-ChildItem $d -Recurse -File | ForEach-Object {
        $h = (Get-FileHash $_.FullName -Algorithm SHA1).Hash
        $k = $_.FullName.Substring($wsdk.Length)
        [void]$new.Add("$k|$h")
        if ($old.ContainsKey($k) -and $old[$k] -ne $h) { $_.LastWriteTime = $now; $touched++ }
    }
}
Set-Content $hashFile $new
Note "overlay inputs touched (content changed since last run): $touched; stage=$Stage"

# 2. Compile commands: the pin Release entries, retargeted at the overlay tree.
$db = Get-Content "$pinBuild\compile_commands.json" -Raw | ConvertFrom-Json
$entries = @($db | Where-Object { $_.file -match 'rexglue-sdk[\\/]src[\\/](codegen|rexglue)[\\/]' -and $_.command -match 'CMAKE_INTDIR=\\"Release\\"' })
$pinFwd = $pinSdk.Replace('\', '/'); $wFwd = $wsdk.Replace('\', '/')
function Retarget([string]$cmd) {
    $cmd = $cmd.Replace("$pinFwd/include", "$wFwd/include").Replace("$pinFwd/src", "$wFwd/src")
    $cmd = $cmd.Replace("$pinSdk\src\", "$wsdk\src\")
    # The pin PCH was built from pin headers; parse its header textually instead.
    $cmd = $cmd -replace '\s-Xclang\s+-include-pch\s+-Xclang\s+\S+', ''
    return $cmd
}
function NinjaPath([string]$p) { return $p.Replace('$', '$$').Replace(' ', '$ ').Replace(':', '$:') }
$nj = New-Object System.Text.StringBuilder
[void]$nj.AppendLine('ninja_required_version = 1.5')
[void]$nj.AppendLine('rule cc')
[void]$nj.AppendLine('  command = $cmd')
[void]$nj.AppendLine('  description = CC $out')
[void]$nj.AppendLine('  depfile = $out.d')
[void]$nj.AppendLine('  deps = gcc')
$lib = "$work\rexcodegen.lib"
$llvmBin = Split-Path ((Get-Command clang++).Source)
[void]$nj.AppendLine('rule ar')
if (Test-Path "$llvmBin\llvm-lib.exe") {
    [void]$nj.AppendLine("  command = $llvmBin\llvm-lib.exe /nologo /OUT:`$out `$in")
} else {
    [void]$nj.AppendLine("  command = $llvmBin\llvm-ar.exe rcs `$out `$in")
}
[void]$nj.AppendLine('  description = LIB $out')
$codegenObjs = @(); $rexglueObjs = @{}
foreach ($e in $entries) {
    if ($e.command -notmatch '\s-o\s+(\S+)') { continue }
    $pinObj = $Matches[1]
    $tail = ($pinObj -split '\\Release\\', 2)[1]
    $isGlue = $pinObj -match 'rexglue\.dir'
    $o = if ($isGlue) { "$obj\rexglue\$tail" } else { "$obj\codegen\$tail" }
    $src = $e.file.Replace('/', '\').Replace("$pinSdk\src\", "$wsdk\src\")
    $cmd = (Retarget $e.command).Replace(" -o $pinObj ", " -o `"$o`" -MD -MF `"$o.d`" ")
    [void]$nj.AppendLine("build $(NinjaPath $o): cc $(NinjaPath $src)")
    [void]$nj.AppendLine("  cmd = $($cmd.Replace('$', '$$'))")
    if ($isGlue) { $rexglueObjs[$pinObj] = $o } else { $codegenObjs += $o }
}
# Regression producer: rexglue's flags (rexcodegen public includes) without the CLI PCH.
$main = $entries | Where-Object { $_.file -match 'rexglue[\\/]main\.cpp$' } | Select-Object -First 1
$prodSrc = "$wsdk\tests\regression\emit_interior_entries.cpp"
$prodObj = "$obj\producer\emit_interior_entries.cpp.obj"
$main.command -match '\s-o\s+(\S+)' | Out-Null; $mainObj = $Matches[1]
$pcmd = (Retarget $main.command) -replace '\s-Xclang\s+-include\s+-Xclang\s+\S+', ''
$pcmd = $pcmd.Replace(" -o $mainObj ", " -o `"$prodObj`" -MD -MF `"$prodObj.d`" ").Replace("$wsdk\src\rexglue\main.cpp", $prodSrc)
[void]$nj.AppendLine("build $(NinjaPath $prodObj): cc $(NinjaPath $prodSrc)")
[void]$nj.AppendLine("  cmd = $($pcmd.Replace('$', '$$'))")
[void]$nj.AppendLine("build $(NinjaPath $lib): ar $(($codegenObjs | ForEach-Object { NinjaPath $_ }) -join ' ')")
Set-Content "$work\build.ninja" $nj.ToString() -Encoding ascii
Note "ninja: $($codegenObjs.Count) codegen + $($rexglueObjs.Count) rexglue objects + producer"
$sw = [Diagnostics.Stopwatch]::StartNew()
& ninja -C $work -j $Jobs *> "$logs\build-tool2-ninja.log"
$code = $LASTEXITCODE
Note "compile exit=$code wall=$([int]$sw.Elapsed.TotalSeconds)s"
if ($code -ne 0) { Get-Content "$logs\build-tool2-ninja.log" | Select-String -Pattern 'error|FAILED' | Select-Object -First 25 | ForEach-Object { Note "  $($_.Line)" }; exit 2 }

# 3. Link with the pin link line: our rexcodegen.lib and objects, pin runtime/thirdparty libs.
Push-Location $pinBuild
$exe = ((& ninja -f build-Release.ninja -t targets all) | Select-String 'rexglue\.exe: ' | Select-Object -First 1).Line -replace ': [^:]*$', ''
$link = @(& ninja -f build-Release.ninja -t commands $exe)[-1]
Pop-Location
Set-Content "$logs\link-pin.txt" $link
function LinkWith([string]$line, [string]$out, [string[]]$objsIn) {
    # CMake wraps the link as: cmd.exe /C "cd . && <clang++ ...> && cd ."; keep the clang++ part.
    if ($line -match 'cd \. && (.*) && cd \.') { $line = $Matches[1] }
    foreach ($k in $rexglueObjs.Keys) { $line = $line.Replace(" $k ", ' ').Replace(" $($k.Replace('\', '/')) ", ' ') }
    foreach ($form in @("$pinOut\rexcodegen.lib", "$pinOut\rexcodegen.lib".Replace('\', '/'))) { $line = $line.Replace($form, $lib) }
    $line = $line.Replace($exe, $out).Replace($exe.Replace('/', '\'), $out)
    $line = $line -replace '(-Xlinker\s+/implib:|/IMPLIB:|-Wl,--out-implib,)(\S+)', "`$1$work\discard.lib"
    $line = $line -replace '(-Xlinker\s+/pdb:|/PDB:)(\S+)', "`$1$($out -replace '\.exe$','.pdb')"
    return $line.Replace(' -o ', " $($objsIn -join ' ') -o ")
}
foreach ($t in @(@{ out = "$outBin\rexglue.exe"; objs = @($rexglueObjs.Values) }, @{ out = "$outBin\regression_interior_entries.exe"; objs = @($prodObj) })) {
    $line = LinkWith $link $t.out $t.objs
    $name = Split-Path $t.out -Leaf
    Set-Content "$logs\link-$name.txt" $line
    Push-Location $pinBuild
    cmd /d /c "$line > `"$logs\link-$name.log`" 2>&1"
    $code = $LASTEXITCODE
    Pop-Location
    Note "link $name exit=$code"
    if ($code -ne 0) { Get-Content "$logs\link-$name.log" | Select-Object -First 25 | ForEach-Object { Note "  $_" }; exit 3 }
}
foreach ($dll in 'rexruntime.dll', 'TracyClient.dll') { Copy-Item "$pinOut\$dll" $outBin -Force }
Note "DONE rexglue.exe sha256 $((Get-FileHash "$outBin\rexglue.exe").Hash.Substring(0,16)) total=$([int]$total.Elapsed.TotalSeconds)s"
Exit-Agent9Slots $held
exit 0
