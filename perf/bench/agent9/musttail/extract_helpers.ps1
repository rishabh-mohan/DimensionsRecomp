# Copy the tail-call helper block of context.cpp (the anonymous namespace with kMustTailReturn
# through the end of emit_tail_call) to gen_out/helpers.inc, so emit_test.cpp always tests the
# live code. Text processing only.
param([string]$Out = (Join-Path $PSScriptRoot 'gen_out/helpers.inc'))
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$src = Join-Path $root 'DimensionsRecomp/rexglue-sdk/src/codegen/builders/context.cpp'
$lines = [IO.File]::ReadAllLines($src)
$k = -1; $end = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($k -lt 0 -and $lines[$i] -like 'constexpr std::string_view kMustTailReturn*') { $k = $i }
  if ($lines[$i] -like 'void BuilderContext::emit_function_call(uint32_t address) {*') { $end = $i; break }
}
if ($k -lt 0 -or $end -lt 0) { throw 'helper block not found in context.cpp' }
$start = $k
while ($start -gt 0 -and $lines[$start] -ne 'namespace {') { $start-- }
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$hdr = "// Extracted from context.cpp lines $($start + 1)-$end by extract_helpers.ps1. Do not edit."
Set-Content -Path $Out -Value (@($hdr) + $lines[$start..($end - 1)])
"helpers.inc: context.cpp lines $($start + 1)-$end"
