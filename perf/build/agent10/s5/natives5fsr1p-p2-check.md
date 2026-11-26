# Cross-check: natives5fsr1p P1 (stage) + P2 (kit diff)

M10, 2026-11-26 ~04:36. Read-only. git apply ran on my own scratch copies (build/agent10/s5/scratch-p2, deleted afterwards).

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent2/s5/natives5fsr1p-bin/MANIFEST.txt | 15A92E4DBFD634FC | 3539 |
| build/agent2/s5/rt-bin/b-fsr1p/stage.txt | 5ABAF1B3 | - |
| build/agent2/s5/rt-bin/stage-fsr1p.py | C564FAB3 | - |
| build/agent2/s5/rt-bin/BIN-PINS-natives5fsr1p.md | 2D519CFF | - |
| build/agent2/s5/rt-smoke/delta-fsr1p/fsr1p.diff | 51F25C0C | 9637 |
| delta-fsr1p/new/rt-smoke-run.ps1 | 8275759B | 27435 |
| delta-fsr1p/new/rt_smoke_post.py | 749274A7 | 22823 |
| delta-fsr1p/new/RUN-RT-SMOKE.cmd | 1F72668D | 4562 |
| delta-fsr1p/new/manual-capture.ps1 | 1A4081C6 | 4937 |

## Base

- Rating: natives5fsr1p-rating D3E2EF03 (P1-P6).
- Live kit: ps1 02C6C88C, post 6034CA36, cmd 34425077, all unchanged at 04:35. The delta's orig/ copies equal these, and orig/manual-capture equals fix1 26894137.

## Verdict

**P1 CLOSED. P2 CONFIRMED.** The diff is byte-true, covers everything P2 asked for, and changes nothing else. K1-K4 and N2-N6 still hold.

## What I checked

- **P1 (stage):**
  - The new bin has 8 files + MANIFEST. Seven are byte-equal to native4bp-bin: exe FA761654, map 493DA6DA, rexgpu-xenos 9A7CC3F4, FiraSans C29556A2, TracyClient 85044850, achievement wav A7070191, amd_fidelityfx 12A50812. rexruntime is DF527CBC.
  - M2 is right that my "8 kept + 6 shared" overcounted by one: it is 7 kept + 1 replaced.
  - The MANIFEST records the sources, the pe-check (453/453, exports equal), "fingerprint 39129c4c059be5f0, first boot cold", the P6 data-use line, and 8 PASS copy checks.
  - stage.txt shows verify-bins PASS on the new bin (MANIFEST 15A92E4D) and on the other pinned bins.
  - native4bp-bin MANIFEST is still C5181520, and natives5fsr1-bin is still 102AAD90.
- **P2 (diff):**
  - `git apply` of fsr1p.diff on scratch copies of orig/ gives all 4 new/ files byte for byte (8275759B, 749274A7, 1F72668D, 1A4081C6).
  - Hunks:
    - cmd: 2 comment lines (bin name) and 2 pin lines (ps1 → 8275759B, post → 749274A7). The other pins are unchanged.
    - ps1: header comments, `$binFsr1` path → natives5fsr1p-bin, MANIFEST pin → 15A92E4D…AD90. T2's bin and pin and the bilinear toml pin are unchanged.
    - post: docstring; REFS group `nativefinal2` → `native4bp`, with 1812-cold-n4bp60 / 1825-n4bp60-r1 game.log pins 93E1754B…3502 / 5AD5426A…D1E9 (full sha256 match my hashes); F3A/F3B `bin=` → natives5fsr1p-bin and `ref='native4bp'`. No other `nativefinal2` or `natives5fsr1-bin` text is left. S1 is done.
    - manual-capture: one line, the default `$Times` goes from (60, 62, 122.25, 146.75, 201.5) to (122.25, 146.75, 201.5).
  - Parse checks: post ast OK; PS 5.1 ParseFile shows 0 errors for the new ps1 and manual-capture.
- **The manual-capture change is enough for N5 at ≥120 s:**
  - The N5 check is on the first F3A zoom actually taken. That is now 122.25 s, or a later time if that one is SKIPPED or late (`$first` stays true until a zoom is taken).
  - The ~50 s desktop shot (local only, the scale source for K2) is unchanged.
  - N2 gate (exit 4), windows/focus check (N3), the zoom region and the 1366x800 + 2% rule are unchanged.
  - K1-K4 still hold as written.

## Conditions (remaining)

- **P3 (install):**
  - Copy the 3 kit files byte-equal from delta-fsr1p/new/.
  - Run pinsonly (14 files), tamper ALL PASS and `RUN-RT-SMOKE.cmd dryrun noshots` DRY RUN ALL PASS, with "MANIFEST sha256 15A92E4D… = pin" for natives5fsr1p-bin and verify-bins 0 FAIL. Send the log shas.
  - manual-capture isn't kit-pinned, so its live copy (M2 scratch) must hash 1A4081C6 before the GO. Report that sha with the GO.
- **P4-P6** stand as in D3E2EF03:
  - one GO `noshots arms=F3A,F3B` after the desktop is free;
  - P5 pass criteria per arm (fp 39129c4c, both boot shaders adopted, 0 failed draws in the first 120 s, N5 ≥2% at 122.25 s);
  - still black → stop;
  - perf only within this bin.
- **N6 carry-over:** a FAIL on the two kit screenshot gates is expected with noshots. Any other post FAIL is real, including a marker or new-error FAIL against the new native4bp refs.

## Findings

- **NIT N1.** In manual-capture, `$ws` inside the loop is the window list, not the workspace (no clash in this script). Leave it, but don't copy the name into kit code.
