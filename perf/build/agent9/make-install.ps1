# Agent 9: make the install tree build\agent9\install\<Variant> in baseline layout, for Agent 2's codegen-option build.
#   powershell -NoProfile -File build\agent9\make-install.ps1 [-Variant batch]
# Layout (recipe step 3 in perf-notes/agent9-codegen.md):
#   generated\rexglue.cmake        baseline's (the variant copy names variant paths)
#   generated\default\...          the variant's codegen output, with baseline's codegen.d (same deps: xex, manifest, config)
#   legodimensions_config.toml     the config that produced the output (build\agent9\generated\<Variant>\)
#   SHA256SUMS.txt                 sha256 of every file above, relative paths with '/'
param([string]$Variant = 'batch')
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
$gen = "$R\build\agent9\generated\$Variant"
$inst = "$R\build\agent9\install\$Variant"
$baseGen = "$R\baseline\DimensionsRecomp\rexlego\generated"
if (-not (Test-Path "$gen\default\legodimensions_init.cpp")) { throw "no codegen output in $gen\default" }
foreach ($f in "$baseGen\rexglue.cmake", "$baseGen\default\codegen.d", "$gen\legodimensions_config.toml") {
  if (-not (Test-Path $f)) { throw "missing $f" }
}
$steps = "$R\build\agent9\logs\install-steps.txt"
# The file is UTF-16 LE (Tee-Object -Append in Windows PowerShell 5.1) and Agent 2's prep-b.py reads it as UTF-16 (02:21):
# keep appending with Tee-Object so the encoding never mixes.
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) [$Variant] $m" | Tee-Object -Append -FilePath $steps }
. "$R\bench\agent9\slots.ps1"
$held = Enter-Agent9Slots 1
try {
  Note "BEGIN $gen -> $inst"
  New-Item -ItemType Directory -Force "$inst\generated\default" | Out-Null
  robocopy "$gen\default" "$inst\generated\default" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
  Copy-Item "$baseGen\rexglue.cmake" "$inst\generated\rexglue.cmake" -Force
  Copy-Item "$baseGen\default\codegen.d" "$inst\generated\default\codegen.d" -Force
  Copy-Item "$gen\legodimensions_config.toml" "$inst\legodimensions_config.toml" -Force
  $files = @(Get-ChildItem $inst -Recurse -File | Where-Object { $_.Name -ne 'SHA256SUMS.txt' } | Sort-Object FullName)
  $sums = foreach ($f in $files) {
    '{0}  {1}' -f (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower(), $f.FullName.Substring($inst.Length + 1).Replace('\', '/')
  }
  [IO.File]::WriteAllLines("$inst\SHA256SUMS.txt", [string[]]$sums)
  $tus = @($files | Where-Object { $_.Name -match '^legodimensions_recomp\.(\d+)\.cpp$' } |
    ForEach-Object { [int]($_.Name -replace '^legodimensions_recomp\.(\d+)\.cpp$', '$1') } | Sort-Object)
  $cfgSha = (Get-FileHash "$inst\legodimensions_config.toml" -Algorithm SHA256).Hash.Substring(0, 16)
  Note ("END files=$($files.Count) bytes=$(($files | Measure-Object Length -Sum).Sum) TUs=$($tus.Count) " +
    "last=legodimensions_recomp.$($tus[-1]).cpp config_sha=$cfgSha")
} finally { Exit-Agent9Slots $held }
