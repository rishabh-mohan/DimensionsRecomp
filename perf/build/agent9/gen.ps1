# Agent 9: run codegen for one option variant into build\agent9\generated\<Variant>\default.
# Never touches baseline\ or the dev generated junction.
#   powershell -NoProfile -File build\agent9\gen.ps1 -Variant off
#   powershell -NoProfile -File build\agent9\gen.ps1 -Variant crso -Options 'cr_compare_so_zero = true'
#   powershell -NoProfile -File build\agent9\gen.ps1 -Variant batch -ConfigFile build\agent9\configs\batch.toml
# -Options: TOML root-key lines, prepended to a copy of DimensionsRecomp\rexlego\legodimensions_config.toml.
# -ConfigFile: a complete LEGO config, copied byte for byte (exclusive with -Options). The batch uses this, so the
#   config that goes to Agent 2 is exactly the one that produced the code.
# -Exe: rexglue.exe to run (default build\agent9\bin\rexglue.exe = pin SDK + Agent 9 codegen).
param([Parameter(Mandatory = $true)][string]$Variant, [string]$Options = '', [string]$Exe = '', [string]$ConfigFile = '')
# -Options is one string; separate TOML lines with ';' (e.g. 'skip_lr = true;cr_as_local = true').
$OptLines = @($Options -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
if (-not $Exe) { $Exe = "$R\build\agent9\bin\rexglue.exe" }
if ($ConfigFile) {
  if ($OptLines.Count) { throw '-ConfigFile and -Options are exclusive' }
  $ConfigFile = (Resolve-Path -LiteralPath $ConfigFile).Path
}
$dir = "$R\build\agent9\generated\$Variant"
$logs = "$R\build\agent9\logs"
New-Item -ItemType Directory -Force $dir, $logs | Out-Null
if (Test-Path "$dir\default") { Remove-Item -Recurse -Force "$dir\default" }
$steps = "$logs\gen-steps.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) [$Variant] $m" | Tee-Object -Append -FilePath $steps }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$manifest = @"
# Agent 9 variant '$Variant' (copy of baseline manifest; output stays under build\agent9\generated\$Variant).
[project]
name = "legodimensions"
sdk_version = "0.10.0"
game_root = "../../../../game/disc"

[entrypoint]
file_path = "../../../../game/disc/Default.xex"
out_directory_path = "default"
includes = ["legodimensions_config.toml"]
"@
[IO.File]::WriteAllText("$dir\legodimensions_manifest.toml", $manifest.Replace("`r`n", "`n"), $utf8)
if ($ConfigFile) {
  Copy-Item -LiteralPath $ConfigFile -Destination "$dir\legodimensions_config.toml" -Force
  $cfgNote = "config=$ConfigFile"
} else {
  $cfg = [IO.File]::ReadAllText("$R\DimensionsRecomp\rexlego\legodimensions_config.toml")
  $head = "# Agent 9 variant '$Variant' options`n" + ($OptLines -join "`n") + "`n`n"
  [IO.File]::WriteAllText("$dir\legodimensions_config.toml", $head + $cfg, $utf8)
  $cfgNote = "options=[$($OptLines -join '; ')]"
}
Set-Location $dir
# At most 2 cores (grid rule): hold both Agent 9 CPU slots and pin the codegen process to CPUs 0-1.
. "$R\bench\agent9\slots.ps1"
$held = Enter-Agent9Slots 2
try {
  # Hash after the slots are held: build-tool2.ps1 relinks the exe while it holds them.
  $h = (Get-FileHash $Exe -Algorithm SHA256).Hash.Substring(0, 16)
  Note "BEGIN exe=$Exe sha=$h $cfgNote"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process -FilePath $Exe -ArgumentList 'codegen', '--ignore-stamp', 'legodimensions_manifest.toml' `
    -RedirectStandardOutput "$logs\gen-$Variant.log" -RedirectStandardError "$logs\gen-$Variant.err.log" `
    -NoNewWindow -PassThru
  $null = $p.Handle  # keep the handle open, or ExitCode/TotalProcessorTime read empty after exit
  try { $p.ProcessorAffinity = [IntPtr]3 } catch { }
  $p.WaitForExit()
  $code = $p.ExitCode
  $cpu = [Math]::Round($p.TotalProcessorTime.TotalSeconds, 1)
} finally { Exit-Agent9Slots $held }
Add-Content "$logs\gen-$Variant.log" (Get-Content "$logs\gen-$Variant.err.log" -ErrorAction SilentlyContinue)
$t = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
$g = Get-ChildItem "$dir\default" -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum
Note ("END exit=$code wall=${t}s cpu=${cpu}s files=$($g.Count) bytes=$($g.Sum) ({0:N1} MB)" -f ($g.Sum / 1MB))
Select-String -Path "$logs\gen-$Variant.log" -Pattern 'patch applied|fallback|blocked|rejected|error|Error|WARN|skip_lr|so_zero|XER' |
  Select-Object -First 25 | ForEach-Object { Note ("log: " + $_.Line.Trim()) }
exit $code
