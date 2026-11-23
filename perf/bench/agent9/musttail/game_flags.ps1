# Dot-source. Reads the real LEGO recomp TU flags from build/dev/compile_commands.json
# (legodimensions_recomp.61.cpp; a single-config Release database, so this is the entry
# env/compile-one.ps1 picks), drops -o <obj>, -c <src> and the CMake PCH options (cmake_pch.hxx only
# includes legodimensions_pch.h, which every TU includes itself), and sets:
#   $GameFlagsFull  everything else, as built: -O3 -DNDEBUG -gline-tables-only -march=x86-64-v3 ...
#   $GameFlags      the same minus -O* and -g* (callers add their own -O level)
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$cc = Get-Content (Join-Path $root 'build/dev/compile_commands.json') -Raw | ConvertFrom-Json
$entry = $cc | Where-Object { $_.file -like '*legodimensions_recomp.61.cpp' } | Select-Object -First 1
$tok = @($entry.command -split ' ' | Where-Object { $_ })
$GameFlags = @()
$GameFlagsFull = @()
for ($i = 1; $i -lt $tok.Count; $i++) {
  $t = $tok[$i]
  if ($t -eq '-o' -or $t -eq '-c') { $i++; continue }
  if ($t -eq '-Xclang' -and ($tok[$i + 1] -eq '-include-pch' -or $tok[$i + 1] -eq '-include')) { $i += 3; continue }
  if ($t -eq '-include-pch' -or $t -eq '-include') { $i++; continue }
  $GameFlagsFull += $t
  if ($t -match '^-O\d$' -or $t -like '-g*') { continue }
  $GameFlags += $t
}
