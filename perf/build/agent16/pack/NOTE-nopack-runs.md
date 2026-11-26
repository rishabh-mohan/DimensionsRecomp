# NOTE: S5 runs on native bins WITHOUT the 4bp AOT placement pack (M16, read-only, 2026-11-26 04:15)

Source:
- every run.json under `build\` and `runs\` that started on or after 2026-11-25 00:00 and whose game.log has "Native GPU" lines (44 runs).
- Shader ids come from the game.log warning lines.
- Magnitude comes from the native trace `draw_missing_*` events. Only my trace runs have those.
- Scratch: `nopack-runs.tsv`, `nopack-ids.txt`.

## Which bins lack the pack

Every run on these bins logs placement VS 0xAC449538 / PS 0xAC448F28 "missing from AOT index" and as
"unrecognized ... shader resource":
- nativefinal-bin
- nativefinal-off-bin
- nativefinal2-bin (MANIFEST 4E5E2620)
- dump\bin-nf2 (a copy of nativefinal2)
- s5\natives5fsr1-bin (MANIFEST 102AAD90)

These bins have the pack and **0** miss lines on attract-long:
- native4bp-bin (C5181520)
- smoke4bp bin-4bp
- psorows ref and pso (CA1FB212)

M3's gameplay bin-native is C5181520 as well. It has no title misses, only the known story/menu misses:
- VS 0xAC44BC64
- PS 0xAC49B8F8 (in 204323)

## Log counts are capped, so they can't measure the drops

Every no-pack run shows exactly 8 placement lines and 16 "unrecognized" lines (the shared counter stops at 32), so these
counts are saturated. Timing runs on native also carry no per-frame miss counter: perf.csv draw_calls and input.csv
scene_draws are empty or 0 for native. The only magnitude data is the trace runs on the same attract-long route:

| run (trace) | bin | 3D frames | missing draws/frame median (p90) | recorded draws/frame median | dropped share |
|---|---|---|---|---|---|
| smoke-20261125-174125 "before" (nf2) | nativefinal2 | 4700 | 98 (127) | 610 | ~14% |
| smoke-20261125-192908 "before" (nf2ref) | bin-nf2 | 6581 | 96 (129) | 499 | ~16% |
| both "after" (4bp) | native4bp | 3291 | 0 (0) | 518 | 0 |
| dump-attract-nf2 (whole run, 300 s) | bin-nf2 | 29142 | 8 on miss frames | 8 on miss frames | 562,761 VS-miss events (52 guest VS), 390 PS (3 guest PS) |

## Runs on no-pack bins, with run dirs

| when | run dir | bin | mode |
|---|---|---|---|
| 11-25 08:38 / 08:43 | build\agent3\runs\20261125-083841-fx6-nativefinaloff-plain, -084301-fx7-nativefinal-level | nativefinal(-off) | FUNCTIONAL |
| 11-25 16:52 | build\agent8\session3\smoke-final2\runs\20261125-165219-final2-3d-native | nativefinal2 | FUNCTIONAL |
| 11-25 17:24 | build\agent16\dump\runs\20261125-172426-dump-attract-nf2 | bin-nf2 | FUNCTIONAL (the dump) |
| 11-25 19:29 | build\agent16\smoke4bp\runs\20261125-192914-smoke-nf2ref | bin-nf2 | FUNCTIONAL ("before" reference) |
| 11-25 18:09-19:14 | build\agent8\s5\matrix\20261125-1804\runs\ 1809-cold-nat60, 1820/1835/1904/1914-nat60-r1..r4, 1830/1844-natU-r1..r2 | nativefinal2 | **TIMING** (S5 0.3 baseline) |
| 11-26 01:36-04:07 | build\agent2\s5\rt-smoke\runs\ 20261126-013637/014102/022926/023351/030312/030737/035021/035446/040310/040735-s5rt-f3a/b | natives5fsr1 | FUNCTIONAL (RT smoke, 10 runs) |

## Conclusions at risk

- **AT RISK, S5 0.3 baseline (Agent 8, 20261125-1804):**
  - nat60: 3D 50.02 fps, p99 56.6 ms.
  - natU: 106 fps, "FASTER".
  - Both ran with ~14-16% of 3D draws dropped (~96 draws/frame), so they flatter native frame time and GPU time.
  - n4bp60 (45.65 fps, p99 71 ms) does the full work. So "n4bp slower than nf2" (-9% fps, worse p99) is partly the cost of
    the restored draws, not a regression.
  - The uncapped native headline (natU) is too optimistic by an unknown amount, at most about the dropped share.
- **AT RISK, M2's RT smoke / res-scale / FSR arms (natives5fsr1, 10 runs):**
  - The title is black and the same draws are dropped.
  - Any GPU-time or res-scale delta, and any image-quality read, is invalid until it is rebuilt on top of the pack.
- **NOT at risk, NATCMP +4.6% (2/2):**
  - The native arm is native4bp-bin (0 miss lines in 0159/0209/0214).
  - The ship arm is the Xenos renderer (devfinal2), which has no native AOT index.
- **NOT at risk, the PSO rows:** ref (C5181520) and pso (CA1FB212) both log 0 misses in all 9 runs.
- **NOT at risk, the dtime kit:** it uses the native4bp work copy.
- **Minor, known: M3's gameplay native runs.** They are on the pack bin, but menu/story misses (AC44BC64,
  AC49B8F8, A81E1C30) still drop ~3.4 events/frame. Covered by B48DA281 and the story-dump plan.
