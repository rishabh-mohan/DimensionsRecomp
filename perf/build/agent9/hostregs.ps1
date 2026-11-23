# Agent 9: host code that touches ctx.ctr / ctx.cr* / ctx.xer / ctx.reserved / ctx.fpscr / ctx.lr outside codegen.
# Stage A (ctr/xer/reserved/cr_as_local) is only safe if no host function consumes the guest caller's value of these
# registers on entry, and no guest code consumes a host write of them after the host function returns.
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
$out = "$R\build\agent9\diff\batch-nolr\host-regs.txt"
New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
$files = @(Get-ChildItem "$R\DimensionsRecomp\rexlego\src" -Recurse -File -Include *.cpp,*.h,*.hpp,*.inl) +
  @(Get-ChildItem "$R\DimensionsRecomp\rexglue-sdk\src", "$R\DimensionsRecomp\rexglue-sdk\include" -Recurse -File -Include *.cpp,*.h,*.hpp,*.inl |
    Where-Object { $_.FullName -notmatch '\\(codegen|thirdparty|third_party)\\' })
$pat = '(ctx|context|ppc_context|ctx_|self_ctx|state\.context)(\.|->)(ctr|xer|cr[0-7]?|reserved|fpscr|lr)\b'
$hits = @($files | Select-String -Pattern $pat)
$lines = foreach ($h in $hits) { "{0}:{1}: {2}" -f ($h.Path -replace '.*\\DimensionsRecomp\\', ''), $h.LineNumber, $h.Line.Trim() }
[IO.File]::WriteAllLines($out, [string[]]$lines)
"files scanned=$($files.Count) hits=$($hits.Count) -> $out"
$hits | Group-Object { $_.Path -replace '.*\\DimensionsRecomp\\', '' } | Sort-Object Count -Descending |
  ForEach-Object {
    $regs = ($_.Group | ForEach-Object { [regex]::Matches($_.Line, $pat) | ForEach-Object { $_.Groups[3].Value } } | Sort-Object -Unique) -join ','
    "{0,5}  {1}  [{2}]" -f $_.Count, $_.Name, $regs
  }
