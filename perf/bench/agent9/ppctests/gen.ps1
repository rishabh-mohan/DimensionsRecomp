# Generate the Catch2 test sources for one variant with Agent 9's rexglue tool.
#   default: no --config (built-in codegen defaults)
#   opt:     --config DimensionsRecomp/rexglue-sdk/tests/ppc/opt_config.toml
#   crso:    --config bench/agent9/ppctests/crso_config.toml (cr_compare_so_zero only, XER in ctx; for test F)
#   opt9:    --config bench/agent9/ppctests/opt9_config.toml (S2.10's 9 keys = opt without skip_lr = LEGO build B)
# Tools built before Agent 9's test_recompiler.cpp --config fix need a TOML with file_path:
#   -Config build/agent9/ppctests/opt_local.toml (includes the SDK opt_config.toml + a dummy file_path)
# Run (holds one Agent 9 CPU slot):
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/gen.ps1 -Variant opt"
# Output: build/agent9/ppctests/<variant>/generated/{ppc_config.h,ppc_test_decls.h,ppc_test_functions.cpp,ppc_test_cases.cpp}
#         and build/agent9/ppctests/<variant>/gen.log
param([ValidateSet('default', 'opt', 'crso', 'opt9')][string]$Variant = 'default', [string]$Tool = 'build/agent9/bin/rexglue.exe',
      [string]$Config = '')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
Set-Location $root
if (-not $Config) {
  $Config = @{ default = ''; opt = 'DimensionsRecomp/rexglue-sdk/tests/ppc/opt_config.toml'; crso = 'bench/agent9/ppctests/crso_config.toml'
               opt9 = 'bench/agent9/ppctests/opt9_config.toml' }[$Variant]
}
$out = "build/agent9/ppctests/$Variant"
$gen = "$out/generated"
if (Test-Path $gen) { Remove-Item -Recurse -Force $gen }
New-Item -ItemType Directory -Force $gen | Out-Null
$a = @('recompile-tests', "--output=$gen", '--bin-dir=build/agent9/ppctests/bin', '--asm-dir=DimensionsRecomp/rexglue-sdk/tests/ppc/asm')
if ($Config) { $a += "--config=$Config" }
$t = Get-Item $Tool
$sha = (Get-FileHash -Algorithm SHA256 $t.FullName).Hash.Substring(0, 16)
$sw = [Diagnostics.Stopwatch]::StartNew()
$o = & $t.FullName @a 2>&1 | ForEach-Object { "$_" }
$code = $LASTEXITCODE
$sw.Stop()
$cases = 0; $funcs = 0
if (Test-Path "$gen/ppc_test_cases.cpp") { $cases = @(Select-String -Path "$gen/ppc_test_cases.cpp" -Pattern '^\s*TEST_CASE\(' -CaseSensitive).Count }
if (Test-Path "$gen/ppc_test_functions.cpp") { $funcs = @(Select-String -Path "$gen/ppc_test_functions.cpp" -Pattern '^DECLARE_REX_FUNC\(' -CaseSensitive).Count }
$head = @(
  "gen ${Variant}: exit $code, {0:n1} s, TEST_CASEs $cases, functions $funcs" -f $sw.Elapsed.TotalSeconds
  "tool: $($t.FullName) (sha256 $sha, $($t.Length) bytes, $($t.LastWriteTime))"
  "cmd: $Tool $($a -join ' ')"
)
Set-Content -Path "$out/gen.log" -Value ($head + $o) -Encoding UTF8
$head | ForEach-Object { Write-Host $_ }
$o | Select-String -Pattern 'error|warn|cr_compare_so_zero: [1-9]|REGISTER_OUT' | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
exit $code
