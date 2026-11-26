# Rating: M3 S1 candidate (RUN-GAMEPLAY gameplay() moved onto boot2)

M10, 2026-11-26 ~04:15. Read-only review. I ran nothing of M3's in place: git apply, gen --check and the parse ran on my own scratch copies (build/agent10/s5/scratch-s1, deleted afterwards).

## Files

| file | sha256/16 | bytes |
|---|---|---|
| kit.titlegate-to-s1.diff (build/agent3/gameplay) | F674E49A7641FF39 | 23412 |
| cand-s1/gen_gameplay_route.py | 2C1977DE3652DF24 | 12096 |
| cand-s1/gameplay-route.txt | 705A3A504BF6B669 | 11091 |
| cand-s1/explore-route.txt (unchanged) | CB271440130C47ED | 8314 |
| cand-s1/gameplay-run.ps1 | 28F7785BDB47FBDF | 26972 |
| cand-s1/RUN-MANUAL.cmd | DC22DF4FCF57BF89 | 5689 |
| cand-s1/RUN-EXPLORE.cmd | 5B4A31A98F52F74C | 5493 |
| cand-s1/RUN-GAMEPLAY.cmd | 09304AC0606A3EED | 5210 |

cand-s1 is in M3's brain scratch.

## Base

The cand-title files (rated in m3-titlegate-rating 4AD1E9BC, not installed yet), plus the live ps1 D97C9228.

## Verdict

**SAFE-IF G1-G5: native arm only.** The default both-arms mode and `xenosonly` are **not approved** (B1). The xenos arm can't pass the boot2 gates: no xenos bin logs the frontend transition lines that every gate waits for.

## What I checked

- **Diff is byte-true.** `git -c core.autocrlf=false apply` on scratch copies of the base reproduces all 7 candidates byte for byte.
- **gameplay-run.ps1 28F7785B** (vs D97C9228):
  - The changes are comments plus one code line, `$Seconds = if ($Manual) { 1200 } else { 1500 }`. Route mode goes from 900 s to 1500 s; manual stays at 1200 s.
  - PS 5.1 ParseFile: 0 errors.
- **gen 2C1977DE:**
  - ast.parse OK.
  - `--check` (scratch copy plus both routes): "same" for explore-route (246 steps, 66 marks) and gameplay-route (302 steps, 57 marks), exit 0.
  - Code changes: prefix() and ORANGE are removed; prompts(L) is factored out and shared by explore and gameplay; gameplay() is now boot2 + prompts + O (6 × 10 s) + skip probes + walk cycles.
  - The blind `sleep 50` + one START that I flagged as S1 in 4AD1E9BC is gone.
- **cmds:** a line compare against cand-title differs only in GPPIN_01 (ps1), GPPIN_04 (gen) and GPPIN_06 (gameplay-route) in all three. RUN-GAMEPLAY also changes the L3 comment ("~2 x 15-25 min, cap 25 min each"). Swap-back gives 2960C11B / E0787CC1 / 1EC3D142.
- **gameplay-route 705A3A50**, 26 wait_log + wait_first_frame 240:
  - fe 7 (120 s), fe 0 ×6, fe 12 (420 s), fe 13 ×6 (10 s), TITLE GATE CHECK fe 5 pending=0 (20 s), then fe 17 / 47 / 49 / 54 / 55 / 55-pending0;
  - then 3 × `Toypad listener: LOAD -> pad=N` (240 s);
  - then O, probes, 18 walk cycles, `stop`.
  - Budget: sleep 185.5 s + input ~230 s + wait timeouts 1761 s = **worst case ~2177 s** (M3 says ~2165). With no waits the floor is ~416 s.
- **B1 evidence (xenos fe lines).** I scanned every game.log under build/ whose legodimensions.toml has `native_settings_frontend = true`:
  - Xenos runs (no `Native GPU [fp]` line, log >20 KB): 102, and **0** of them have a `Native frontend transition` line. This includes RT T2 (devs5toml, 240.9 s, reached the amber intro LED), all ship60 natcmp rows, devfinal2-smoke and final2-3d-xenos.
  - Native-GPU runs: every long run has 3-82 of these lines. The fe=0 native runs are all short (~58 KB) logs.
  - Source: the line comes from `NativeSettingsBridge::TraceTransition` (settings_native_bridge.cpp L1048-1055), called from the `sub_82FEA350` hook through `GetBridge()` (settings_native_hooks.cpp L83-125, L186-191). The cvar is on in these xenos tomls and krnl info logging works (T2 has `XamUserReadProfileSettings` info lines), so on xenos the bridge doesn't trace for some other reason. I didn't pin down which.
  - Either way, M3's note (a) "xenos fe markers verified in source only" doesn't hold in practice.
  - Toypad lines do appear on xenos: `lit 99 42 0E` is in many xenos logs, and the sidecar's `Toypad listener:` lines come from the harness side.

## Conditions

- **G1 (scope).**
  - Approved real runs: only `RUN-GAMEPLAY.cmd nativeonly`; the dryrun likewise with `nativeonly`.
  - Not approved: the default both-arms run, `RUN-GAMEPLAY xenosonly` and `RUN-EXPLORE xenosonly`. RUN-EXPLORE uses the same boot2 gates, so the last one also applies to the installed title gate.
  - A xenos route needs its own gate on lines xenos does log (Toypad LED/listener lines) and a new rating.
- **G2 (install).**
  - Install only after T1-T3 of the title gate are closed and after the manual Toypad session ends.
  - Use the exact cand-s1 files.
  - Evidence: live hashes = the table above; pincheck ×3 exit 0; PS 5.1 parse 0; `gen --check` exit 0; swap-back reproduces 2960C11B / E0787CC1 / 1EC3D142.
- **G3 (tamper).** A tamper log for the changed pins (GPPIN_01/04/06), with sha.
- **G4 (dryruns).**
  - `RUN-GAMEPLAY dryrun nativeonly` must be DRY RUN ALL PASS, with route gameplay-route.txt 705A3A50 and `-Seconds 1500` in the header.
  - `RUN-EXPLORE dryrun` and `RUN-MANUAL dryrun` must still pass, because the ps1 is shared.
  - Send the log shas.
- **G5 (first run).** T4/T5 apply to the gameplay route too: report the title try number, its delay after fe(12) and the gate-check result, and treat a gate-check TIMEOUT as FAIL (ignore the tail). Also report the three s-* prompt waits (LOAD vs TIMEOUT) and whether `stop` was reached before 1500 s.

## Findings

- **B1 BLOCKER (both-arms / xenos mode only).** On devfinal2, every boot2 wait would TIMEOUT: fe 7 (120 s), fe 0 ×6, fe 12 (420 s), fe 13 ×6, the gate check and the menu waits.
  - The route would then run blind, at the timeout spacing, through the menus.
  - The arm would exceed the 1500 s cap (worst case ~2177 s) and post FAIL by construction (gameplay_post counts waits ≥20 s).
  - Not a host-safety issue: the user dir is sandboxed per run. It wastes ~25 min of the desktop and gives no data.
  - G1 contains it.
- **S1 SHOULD.** Until a xenos route exists, make route mode default to native (as explore/manual already do), or make the RUN-GAMEPLAY header say `nativeonly` is required. Today L2/L3 still advertise "native4bp, then xenos (devfinal2)" and "~2 x 15-25 min".
- **N1 NIT.** On native the worst case (~2177 s) exceeds the 1500 s cap only when at least ~3 long waits time out, and such a run is a FAIL anyway. The cap is fine.
- **N2 NIT.** The prompts are shared between the explore and gameplay routes now, so a future change to prompts(L) moves both pins. That's fine, but say so in the next diff.
