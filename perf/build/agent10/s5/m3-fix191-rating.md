# Rating: M3 gameplay-run.ps1 L191 PS 5.1 parse fix (fix191)

Who/when: M10, 2026-11-26 ~01:53 local. Static check plus a PS 5.1 parser check (no script run).

## Files (sha256/16)

| file | sha256/16 |
|---|---|
| WS\build\agent3\gameplay\gameplay-run.1F7900B9-fix191.diff | 7758FE272BB8AF13 |
| candidate gameplay-run.fix191.ps1 (M3 scratch) | 8B07F5D76F34C4FF (LF, 0 CR) |
| current pinned gameplay-run.ps1 | 1F7900B9BCD7400D |

Base: m3-prompt-explore2-rating.md 28C92370 (C1-C3; S1 closed by diff 37DD414F).

## Verdict: SAFE-IF (F1-F2)

## What I checked

- PS 5.1.26100 `[Parser]::ParseFile`:
  - 1F7900B9 has 2 errors, both at L191 ("Unexpected token '$_`""'"). The escaped quote inside `$( ... )` inside a double-quoted string doesn't parse in 5.1.
  - The candidate has 0 errors. A parse error stops the whole script before any statement runs, so 1F7900B9 could never have launched anything (real runs included). That fits both C1 dryruns exiting 1.
- Compare-Object of 1F7900B9 vs the candidate shows the same single change as the diff: 1 line out, 2 lines in, at L191 inside `if ($DryRun) { foreach ($arm ...) }`.
  - The new code builds `$sca` (same quoting logic: `'"' + $_ + '"'` for args with whitespace) and prints the same SIDECAR echo line.
  - No other byte differs, so the lock, refusals, finally/Stop-Ours, Sidecar-Args and the real-run path are unchanged.
- Correction to 28C92370: my static review didn't parse-check under 5.1. From now on I parse-check every .ps1 under PowerShell 5.1 as part of a rating.

## Conditions

- F1: M3 installs the candidate as gameplay-run.ps1 with sha 8B07F5D7. New .cmd pins in RUN-MANUAL/RUN-EXPLORE (and RUN-GAMEPLAY) replace 1F7900B9, fail-closed with the count check unchanged. Send me the new cmd shas.
- F2: C1 still applies: a dryrun ALL PASS on the new pins for RUN-MANUAL and RUN-EXPLORE before use. Send me the log shas.

## Findings

- NIT: the pre-fix kit (1F7900B9) was rated SAFE-IF and pinned without a parse check. No harm (it couldn't run), but a dryrun before GO caught it, as intended.
