# Agent 9: write build\agent9\configs\<Out> = the live LEGO config with the S2.10 block (perf-notes/agent9-codegen.md)
# inserted after line 22, before [functions]. The BOM and the CRLF line endings are kept. Never edits the live file.
#   powershell -NoProfile -File build\agent9\make-batch-config.ps1 [-Out batch-nolr.toml]
# 23:52: skip_lr dropped (Agent 10 Review 4 row 21: LEGO host hooks and XexGetProcedureAddress read ctx.lr as the caller).
#   configs\batch.toml (23:16, with skip_lr) stays as the record of build\agent9\install\batch (23:28); don't build that one.
# Session 3 (02:05): -Drop 'k1,k2' writes a rollback config (recipe step 9): it removes those key lines and the comment
#   that heads them (when all of its keys are gone), and adds one '# Rollback' line after the title. Without -Drop the
#   output is unchanged (batch-nolr.toml sha256 E60EAF1C...). -Drop is one string (powershell -File passes no arrays).
param([string]$Out = 'batch-nolr.toml', [string]$Drop = '')
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
$src = "$R\DimensionsRecomp\rexlego\legodimensions_config.toml"
$out = "$R\build\agent9\configs\$Out"
$block = @(
  ''
  '# Codegen options (task #8, Agent 9). Root keys: they must come before [functions].'
  '# Stage A register localization. The body= entries, their owners and their callers keep registers in ctx automatically.'
  'ctr_as_local = true'
  'xer_as_local = true'
  'reserved_as_local = true'
  'cr_as_local = true'
  '# Compares use SO = 0 where XER.SO is provably 0 (it changes nothing without xer_as_local).'
  'cr_compare_so_zero = true'
  'rlwinm_lowering = true'
  'flush_mode_elision = true'
  'vmx_vector_fallbacks = true'
  '# Never in a Tracy build (REXGLUE_PROFILE_GUEST_FUNCTIONS + REXGLUE_ENABLE_PROFILING): musttail fails to compile there.'
  'musttail_calls = true'
  '# Not for LEGO: skip_lr (host hooks and XexGetProcedureAddress read ctx.lr as the caller), skip_msr (STATUS decision 4).'
  '# Later: non_argument_as_local + non_volatile_as_local (Stage B/C: together, after the gate).'
)
$dropKeys = @($Drop -split '[,; ]+' | Where-Object { $_ })
if ($dropKeys.Count) {
  foreach ($k in $dropKeys) { if ($block -notcontains "$k = true") { throw "-Drop: '$k' is not a key of the block" } }
  # Comment lines that head keys: dropped only when every key they head is dropped.
  $heads = @{
    '# Stage A register localization.' = @('ctr_as_local', 'xer_as_local', 'reserved_as_local', 'cr_as_local')
    '# Compares use SO = 0' = @('cr_compare_so_zero')
    '# Never in a Tracy build' = @('musttail_calls')
  }
  $kept = foreach ($l in $block) {
    if ($l -match '^(\w+) = true$' -and $dropKeys -contains $Matches[1]) { continue }
    $head = @($heads.Keys | Where-Object { $l.StartsWith($_) })
    if ($head.Count -and @($heads[$head[0]] | Where-Object { $dropKeys -notcontains $_ }).Count -eq 0) { continue }
    $l
    if ($l.StartsWith('# Codegen options (task #8')) { "# Rollback (recipe step 9, perf-notes/agent9-codegen.md): dropped $($dropKeys -join ', ')." }
  }
  $block = @($kept)
}
$bytes = [IO.File]::ReadAllBytes($src)
$bom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
$skip = if ($bom) { 3 } else { 0 }
$text = [Text.Encoding]::UTF8.GetString($bytes, $skip, $bytes.Length - $skip)
if ($text.Replace("`r`n", '').Contains("`n")) { throw 'live config has bare LF line endings; expected CRLF' }
$lines = $text -split "`r`n"
if ($lines[22] -ne '' -or $lines[23] -ne '[functions]') { throw "unexpected layout: line 23 '$($lines[22])', line 24 '$($lines[23])'" }
$keys = 'skip_lr|skip_msr|\w+_as_local|cr_compare_so_zero|rlwinm_lowering|flush_mode_elision|vmx_vector_fallbacks|musttail_calls'
if ($text -match "(?m)^\s*($keys)\s*=") { throw "the live config already sets $($Matches[1])" }
$new = @($lines[0..21]) + $block + @($lines[22..($lines.Count - 1)])
$outText = $new -join "`r`n"
# Self-check: removing the block gives back the live text exactly.
$back = (@($new[0..21]) + @($new[(22 + $block.Count)..($new.Count - 1)])) -join "`r`n"
if ($back -cne $text) { throw 'self-check failed: the output minus the block differs from the live config' }
New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
[IO.File]::WriteAllText($out, $outText, (New-Object Text.UTF8Encoding($bom)))
$o = [IO.File]::ReadAllBytes($out)
"wrote $out ($($o.Length) B from $($bytes.Length) B; BOM=$bom; block = lines 23-$(22 + $block.Count); [functions] at line $(24 + $block.Count))"
