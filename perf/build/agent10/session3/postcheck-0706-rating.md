# M3 live postcheck 07:06 change (S33 kit output via %TEMP%): rating

M10, 2026-11-25 07:09. Read-only: I diffed the live file against its backup and read the kit wrapper and the 07:05 output. Nothing was run.

## Files rated

| file | sha256 (8) | bytes |
|---|---|---|
| build/agent3/s4b/postcheck.ps1 (live) | 123FD6D0 | 13170 |
| build/agent3/s4b/postcheck.ps1.bak-0706 (base, rated SAFE-IF in postwin-rating.md 3B0C445D) | 8B60EBC3 | 12785 |

## Base

postwin-rating.md (3B0C445D) P1-P5.

## Verdict

**SAFE-IF** Q1-Q2 below. The change cannot PASS a bad run:
- The S33 verdict is the kit's exit code. `$x = $LASTEXITCODE` is taken right after the kit call, as before. New-Item and Copy-Item are cmdlets and don't touch `$LASTEXITCODE`, so the exit code still reaches the `Say "s33 $id $row (exit $x)"` line, including the `/fields` suffix on offsf.
- The kit's stdout (with the w6-summary, which the kit also prints) still goes straight to `logs\<id>.s33.txt` (`*> $f`), not through %TEMP%.
- The copied `checks\<row>` folder is supplementary evidence only.

## What changed (only S33)

- `--out` changed from `build\agent3\s4b\checks\<row>` to `%TEMP%\m3-s33\<row>`.
- After the kit call: `New-Item -Force checks\<row>`, then `Copy-Item %TEMP%\m3-s33\<row>\* -> checks\<row> -Recurse -Force`, wrapped in `try { } catch { }`.
- Nothing else in the file changed.

## Your three checks

1. **Copy failures surface? NO.**
   - `catch { }` swallows terminating errors.
   - Copy-Item errors are non-terminating by default (no `-ErrorAction Stop`), so they never reach the catch. They only go to the error stream of the postcheck process, not to `$f` or the Say line.
   - A failed or partial copy is therefore silent. Because of the verdict path above, this loses evidence but cannot turn a FAIL into a PASS.
2. **Kit exit codes still propagate? YES** (see Verdict).
3. **Stale %TEMP% collisions across rows? None across rows, but there is a stale-reuse risk on reruns.**
   - Rows map to `s33-row1a` (s33off, base vs off) and `s33-row1b` (s33offsf, basesf vs offsf). Each id runs S33 at most once per postcheck instance (`$seen`, `<id>.check.txt`), and the two rows use different folders.
   - However, `%TEMP%\m3-s33\<row>` is never cleared before the kit runs, and `s33-row1a` already holds the 07:05 output (w6-summary, logdiff, staging copies of the two game.logs).
   - On any rerun of the same row where the kit stops early (exit 2 usage or exit 3 WINDOW-HOLD) or writes fewer files, the old files are copied into `checks\<row>` and look current. The old version had the same issue with `checks\<row>` itself, so this is not new, but it is now two places.

## Conditions

- **Q1** Clear `$tmp` before the kit call:
  - `if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction Stop }`.
  - Also clear `checks\<row>` before the copy, or copy into a per-run subfolder (for example `checks\<row>\<id>-<HHmm>`).
- **Q2** Make copy failures visible:
  - use `-ErrorAction Stop` on New-Item and Copy-Item;
  - in the catch, append `COPY FAILED: <message>` to `$f` and set `$x = "$x/copy FAIL"`, so the Say line shows it;
  - copy only when the kit's exit code is 0 or 1 (a real result); with exit 2 or 3, write `no kit output (exit $x)` to `$f` instead.

## Findings

- **SHOULD S1** = Q1 and Q2.
- **NIT N1** The kit records `%TEMP%` paths, which include the Windows user profile, in its header and in w6-data.json. These are copied into `checks\<row>` and appear in `logs\<id>.s33.txt`. Sanitise them, or leave them out, wherever these files feed a shared doc.
- **NIT N2** `checks\<row>` now also gets `staging\runs\*\game.log` copies (about 110 KB each). Harmless.
- **INFO** The kit refuses an `--out` inside build/agent3. Writing to %TEMP% and copying into M3's own `checks\` folder, which postcheck already writes, touches no run folder. The wrapper's read-only rule on runs is kept.
- **INFO** `%TEMP%\m3-s33\row1a.txt` (9256 B, 07:05) is a separate manual file. It is not used by postcheck.

## Read / Sent

- Read: the diff (bak-0706 -> live), the full S33 function and its 2 call sites (L157-158), the RUN-S33-LOGDIFF.cmd header, `logs\s33off.s33.txt`, and the `%TEMP%\m3-s33` and `checks\s33-row1a` listings.
- Sent: verdict plus sha8 to the Overseer.

## Conformance check 07:19 (live 1025D1F6, base bak-0709 4ED8202B, which is 123FD6D0 plus the exit lines)

**CONFORMS.** I diffed bak-0706 -> bak-0709 -> live; only the S33 function changed.
- Q1: `$tmp` and `checks\<row>` are removed before the kit call.
- Q2: the copy runs only on kit exit 0 or 1, with `-ErrorAction Stop`, and a failure appends `COPY FAILED: ...` to `$f` and sets `$x` to `$x/copy FAIL`.
- `kit exit $x` is written right after `$x = $LASTEXITCODE`.
- `s33_fields exit` is the last token of `"$x/fields $LASTEXITCODE"`, so it is the real python exit code, also when `/copy FAIL` comes first.
- One minor deviation, not blocking: Remove-Item has no `-ErrorAction Stop`, so a failed clear (for example a locked file) is silent. Exit 2 or 3 now shows only as `kit exit N` with an empty `checks\<row>`, which is fine.
