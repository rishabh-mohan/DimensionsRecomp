# rt-noshots manual-capture fix1: cross-check

M10, 2026-11-26 03:53. Requested by the Overseer after the F3A capture stopped in the noshots GO.

| file | sha256/16 | bytes |
|---|---|---|
| M2 scratch manual-capture.ps1 (fix1) | 2689413732758F9F | 4945 |
| M2 scratch manual-capture-v1-E893368A.ps1 (old copy) | E893368ADBE182C6 | 4929 |
| M2 scratch manual-capture-fix1.diff | C7883576AA13376D | 2992 |

Base: s5/rt-noshots-capture-check.md 9FEEFB50 (CONFIRMED on E893368A, operating notes K1-K4).

## Verdict

CONFIRMED.

## What I checked

- Diff: `git diff --no-index --stat` from the v1 copy to fix1 gives 1 file, +4/-4. Those are the 4 lines in C7883576: the function definition and the 3 call sites (screenshot, windows, zoom) renamed from `Cli` to `CompCli`. No other bytes changed. LF only.
- No `Cli` word is left in fix1. The only remaining matches are the header comment and the `$cli` path variable, which are not commands.
- PS 5.1 ParseFile: 0 errors.
- Name-clash scan (my own AST scan: every FunctionDefinitionAst name checked against Get-Alias and Get-Command, plus every CommandAst name resolved):
  - Run on v1, it reproduces the bug: `Cli: alias=Clear-Item`. So the scan does detect this kind of clash.
  - On fix1, none of the functions (Say, CompCli, Mark, NonBlack) is an alias, cmdlet, function or application in PS 5.1.
  - Every other command in fix1 resolves to a cmdlet (Add-Content, Add-Type, ConvertFrom-Json, Copy-Item, ForEach-Object, Get-ChildItem, Get-Date, Join-Path, New-Item, Out-Null, Out-String, Select-Object, Select-String, Sort-Object, Split-Path, Write-Host) or to an application (`node`, `powershell`). None of them goes through an alias.
  - rt-mark.ps1 80589B0D defines no functions and uses only cmdlets (Get-Date, Get-Process, Join-Path, Select-Object, Sort-Object, Split-Path, Start-Sleep, Where-Object).
- Impact of the failed attempt, as reported: `Clear-Item screenshot` ran against the non-existent path `projects\screenshot` and stopped with PathNotFound. Nothing was cleared and computer-cli was never called. The N2-N5 logic is unchanged by fix1.

## Conditions

- F1: before the fresh GO, M2 runs the call path offline against a stub `node`/computer-cli (screenshot, windows, zoom) and against the N2 gate. Send me the log sha. The stub must not touch the real desktop.
- F2: the fresh GO uses fix1 2689413732758F9F unchanged. K1-K4 still apply. The current run counts as a functional smoke only, with no captures, and it does not satisfy N2-N6.

## Findings

- SHOULD: put a self-check at the top of the script, e.g. `if (Get-Alias CompCli -ErrorAction SilentlyContinue) { exit 6 }`. Better still, don't use short function names in future helpers. Not required for this GO.
