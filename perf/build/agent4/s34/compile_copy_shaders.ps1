# Full -c compile of a shaders.cpp copy with shaders.cpp's own build/dev command (env/compile-one.ps1 -PrintOnly),
# with only the source path swapped for the copy. -Extra is appended last (e.g. "-march=x86-64-v2").
# Same as build/agent4/s32/compile_copy.ps1 with draw -> shaders. Put the copy at
# <scratch tree>/DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp. shaders.cpp's quote includes
# ("gpu_native/*.h", "cheat_menu.h") are not found next to the copy, exactly as in the real tree, so they
# resolve through the same -I directories.
# One clang process (1 thread, BelowNormal priority). Writes only <OutDir>\shaders.cpp.obj, its .d file and -Log.
param([Parameter(Mandatory)][string]$Source, [Parameter(Mandatory)][string]$OutDir, [string]$Extra = '',
      [Parameter(Mandatory)][string]$Log)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$outFull = [IO.Path]::GetFullPath((Join-Path $root $OutDir))
$print = & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\env\compile-one.ps1" `
    "$root\DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp" -OutDir $outFull `
    -Db "$root\build\dev\compile_commands.json" -PrintOnly
if ($LASTEXITCODE) { throw "compile-one -PrintOnly failed: $LASTEXITCODE" }
$dir = (@($print | Where-Object { $_ -like 'cd *' })[0]).Substring(3)
$cmdline = @($print | Where-Object { $_ -match 'clang\+\+\.exe' })[0]
$notes = @($print | Where-Object { $_ -like 'note:*' })
if ($cmdline -notmatch ' -c ' -or $cmdline -match 'fsyntax-only') { throw 'expected a full -c command' }
$copy = (Resolve-Path (Join-Path $root $Source)).Path.Replace('\', '/')
$pattern = '[A-Za-z]:[\\/][^ "]*?DimensionsRecomp[\\/]rexlego[\\/]src[\\/]gpu_native[\\/]shaders\.cpp(?![.\w])'
$hits = [regex]::Matches($cmdline, $pattern).Count
if (-not $hits) {
    $pattern = '(\.\.[\\/])+DimensionsRecomp[\\/]rexlego[\\/]src[\\/]gpu_native[\\/]shaders\.cpp(?![.\w])'
    $hits = [regex]::Matches($cmdline, $pattern).Count
}
if ($hits -ne 1) { throw "expected the shaders.cpp source exactly once in the command, found $hits" }
$new = [regex]::Replace($cmdline, $pattern, $copy)
if ($Extra) { $new += " $Extra" }
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') -Quiet 6>$null | Out-Null }
New-Item -ItemType Directory -Force -Path $outFull | Out-Null
$exe = $new.Substring(0, $new.IndexOf(' '))
$arguments = $new.Substring($new.IndexOf(' ') + 1)
$psi = New-Object Diagnostics.ProcessStartInfo $exe, $arguments
$psi.WorkingDirectory = $dir
$psi.UseShellExecute = $false
$psi.RedirectStandardError = $true
$psi.RedirectStandardOutput = $true
$sw = [Diagnostics.Stopwatch]::StartNew()
$process = [Diagnostics.Process]::Start($psi)
try { $process.PriorityClass = 'BelowNormal' } catch { }
$errTask = $process.StandardError.ReadToEndAsync()
$outTask = $process.StandardOutput.ReadToEndAsync()
$process.WaitForExit()
$err = $errTask.Result
$warnings = ([regex]::Matches($err, ': warning:')).Count
$errors = ([regex]::Matches($err, ': error:')).Count
$obj = Join-Path $outFull 'shaders.cpp.obj'
$size = if (Test-Path $obj) { (Get-Item $obj).Length } else { -1 }
$summary = "compile_copy_shaders: source=$copy extra='$Extra' replaced=$hits exit=$($process.ExitCode) warnings=$warnings errors=$errors obj_bytes=$size seconds=$([int]$sw.Elapsed.TotalSeconds) notes=$($notes.Count)"
Set-Content -Path $Log -Value ("cd $dir`r`n$new`r`n" + ($notes -join "`r`n") + "`r`n" + $outTask.Result + $err + "`r`n" + $summary)
$summary
exit $process.ExitCode
