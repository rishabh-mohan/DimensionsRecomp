# Counts x64 instructions per function in gen/x64_forms.s (clang -S, Windows x64 target).
# Function = label v_<old|new|xor>_<form> or c_<...>_<form>; ends at .seh_endproc / .Lfunc_end.
# Counts every instruction except ret.
param([string]$Asm, [string]$Order, [string]$Out, [string]$Listing)
$counts = @{}
$text = @{}
$cur = $null
foreach ($line in Get-Content $Asm) {
  if ($line -match '^([A-Za-z_][\w$.]*):') {
    $name = $Matches[1]
    if ($name -match '^(v|c)_(old|new|xor)_') { $cur = $name; $counts[$cur] = 0; $text[$cur] = New-Object System.Collections.Generic.List[string] }
    elseif ($name -notmatch '^\.L') { $cur = $null }
    continue
  }
  if ($line -match '^\.Lfunc_end') { $cur = $null; continue }
  if ($null -eq $cur) { continue }
  if ($line -match '^\s*\.seh_endproc') { $cur = $null; continue }
  if ($line -match '^\s+([a-z][a-z0-9]*)\b') {
    $text[$cur].Add($line.Trim())
    if ($Matches[1] -notmatch '^ret[lqw]?$') { $counts[$cur]++ }  # AT&T prints retq
  }
}
function C([string]$k) { if ($counts.ContainsKey($k)) { [string]$counts[$k] } else { '-' } }
$rows = @('| form | old (locals) | new (locals) | xor (locals) | old (ctx) | new (ctx) | xor (ctx) |',
          '|---|---|---|---|---|---|---|')
foreach ($f in Get-Content $Order) {
  if (-not $f) { continue }
  $rows += "| $f | $(C "v_old_$f") | $(C "v_new_$f") | $(C "v_xor_$f") | $(C "c_old_$f") | $(C "c_new_$f") | $(C "c_xor_$f") |"
}
Set-Content -Path $Out -Value $rows -Encoding ascii
$rows | ForEach-Object { Write-Host $_ }
if ($Listing) {
  $l = foreach ($k in ($text.Keys | Sort-Object)) { "== $k ($($counts[$k]) insns excl. ret)"; $text[$k] | ForEach-Object { "  $_" } }
  Set-Content -Path $Listing -Value $l -Encoding ascii
}
