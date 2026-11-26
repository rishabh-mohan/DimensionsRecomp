# dump6 B GO check (Step A install + dryruns): GO-OK

- Who/when: M10, 2026-11-26 08:26
- Base: dump6-stepA-rating.md F7E38737 (Conditions 1-5); dump6-stepC-rating.md B0A9B0C6; dump6-plan-rating.md 5749F60E (B-C1..B-C7)

## Files (sha256/16, computed by M10)

| File | sha256/16 |
|---|---|
| live gameplay-run.ps1 | DE16A2D29C0F040A (= b\) |
| live RUN-GAMEPLAY.cmd | 603916BBDD6710C0 (= b\) |
| live RUN-EXPLORE.cmd | B6E8DAD4DB9E51C1 (= b\) |
| live RUN-MANUAL.cmd | 6B5C3FC6D0271D82 (= b\) |
| logs\gameplay-dryrun-20261126-081845.txt | D41692EA9AC8DE09 |
| logs\gameplay-dryrun-20261126-082021.txt | C2F1D92A9362B6A1 |
| logs\gameplay-dryrun-20261126-082148.txt | 93AE50852C38C202 |
| logs\gameplay-dryrun-20261126-082322.txt | C95A76812FE80D8D |

## Verdict

GO-OK for `RUN-GAMEPLAY.cmd|603916BBDD6710C0213AFDE818619FA16431268DDA343801ACB8EA93C6CB6B5B|nativeonly cand5 zone dump`,
subject to the Overseer's CG2 preflight passing, a start by 09:30, hands off and an exclusive window (B-C2/B-C3).

## What I checked

- Step A Cond 1-2: the 4 live shas equal the rated b\ shas. Pincheck, parse and tamper x3 as reported by M3
  (I did not repeat the tamper test).
- Dryrun 1 (081845), `nativeonly cand5 zone dump`:
  - DIAGNOSTIC line L3 with LEGO_DUMP_MISSING_SHADERS=<kit>\shader-dumps-native-<stamp>;
  - ZONE L4; CAND5 L5 (MANIFEST 787CD694, tag gp5d-native, trace-native5d, --expect-fp a349d529);
  - the COMMAND env carries both the trace and dump dirs;
  - verify-bins on native5pack-bin and bin-native5: 0 FAIL;
  - SIDECAR ends `--led-shots --zone --zone-delay 45`, with no then-mark;
  - 13/13 word combos exit 2 as expected;
  - DRY RUN ALL PASS; the only refusal note is the hidden-desktop one.
  - No shader-dumps-native-081845 dir left (only the old 051154 dir exists).
  - The 2 `FAIL` lines (L96 st0, L254 native toypad) are inside the replayed reference post blocks (st0/st1/native
    INFO rows), not kit checks. They are the same in all 4 logs and do not affect the ALL PASS.
- Dryrun 2 (082021), `nativeonly cand5 zone`: no LEGO_DUMP or DIAGNOSTIC line; ALL PASS; 13/13 combos.
- Dryrun 3 (082148), RUN-MANUAL `dryrun dump nativeonly`: dump env present, gpman-native; ALL PASS.
- 082322, RUN-EXPLORE `dryrun nativeonly`: gpexp-native, 246 steps; ALL PASS. Step A Cond 4 is met for both cmds
  (pincheck via the shared kit pins, exit 0).

## Conditions (carried over, unchanged)

- B-C4..B-C7 and the Step C Conditions 1-3 apply to the run and its post: dump6_post 7887B90A with --fp and --dump-dir,
  plus the C-S1 time/cap check, inserts 0 and G7 hashes unchanged after the run.
