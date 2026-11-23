# Agent 2 - task #1 step 2: run codegen (optionally wait until the baseline SDK build has linked rexglue.exe).
# Run: powershell -NoProfile -File build\agent2\codegen-watch.ps1 [-NoWait] [-Exe <rexglue.exe>] [-OutDir <dir>] [-IgnoreStamp]
#   -Exe     run this rexglue.exe instead of the SDK out-tree one (e.g. the frozen copy in build\agent2\codegen-tool,
#            so a parallel SDK build that relinks rexglue.exe/rexruntime.dll cannot touch the running tool).
#   -OutDir  where to put the codegen log/steps (default build\agent2). The generated tree always goes to
#            <manifest dir>\generated (manifest: baseline\DimensionsRecomp\rexlego\legodimensions_manifest.toml,
#            or -ManifestDir).
param([switch]$NoWait, [switch]$IgnoreStamp, [string]$Exe = '', [string]$ManifestDir = '', [string]$Tag = 'codegen', [string]$CodegenArgs = '')
$R = '<workspace>'
$log = "$R\build\agent2"
$sdkExe = "$R\baseline\DimensionsRecomp\rexglue-sdk\out\win-amd64\Release\rexglue.exe"
if (-not $Exe) { $Exe = $sdkExe }
if (-not $ManifestDir) { $ManifestDir = "$R\baseline\DimensionsRecomp\rexlego" }
$buildLog = "$log\sdk-build.log"
$steps = "$log\sdk-baseline-steps.txt"
$out = "$log\$Tag-steps.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -Append -FilePath $out }
if (-not $NoWait) {
    Note "waiting for $Exe"
    while ($true) {
        if (Test-Path $Exe) {
            $hit = Select-String -Path $buildLog -Pattern 'Linking CXX executable \S*rexglue\.exe' -Quiet
            if ($hit) {
                try { $fs = [IO.File]::Open($Exe, 'Open', 'Read', 'None'); $fs.Close(); break } catch { }
            }
        }
        if (Select-String -Path $steps -Pattern 'END   build' -Quiet) {
            if (Test-Path $Exe) { break }
            Note 'build ended without rexglue.exe'; exit 1
        }
        Start-Sleep -Seconds 15
    }
}
$fi = Get-Item $Exe
$h = (Get-FileHash $Exe -Algorithm SHA256).Hash
Note "rexglue.exe ready: $Exe $($fi.Length) bytes, $($fi.LastWriteTime.ToString('HH:mm:ss')), sha256 $h"
$dll = Join-Path (Split-Path $Exe) 'rexruntime.dll'
if (Test-Path $dll) { Note "rexruntime.dll: $((Get-Item $dll).Length) bytes, sha256 $((Get-FileHash $dll -Algorithm SHA256).Hash)" }
Set-Location $ManifestDir
$extra = ''; if ($CodegenArgs) { $extra = ' ' + $CodegenArgs }; if ($IgnoreStamp) { $extra += ' --ignore-stamp' }
Note "BEGIN codegen in $ManifestDir$extra"
$sw = [Diagnostics.Stopwatch]::StartNew()
cmd /d /c "`"$Exe`" codegen$extra legodimensions_manifest.toml > `"$log\$Tag.log`" 2>&1"
$code = $LASTEXITCODE
$t = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
$g = Get-ChildItem generated -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum
$free = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
Note ("END   codegen exit=$code wall=${t}s files=$($g.Count) bytes=$($g.Sum) size={0:N1} MB freeC=${free}GB" -f ($g.Sum / 1MB))
Select-String -Path "$log\$Tag.log" -Pattern 'patch|version' | Select-Object -First 10 | ForEach-Object { Note ("log: " + $_.Line.Trim()) }
exit $code

