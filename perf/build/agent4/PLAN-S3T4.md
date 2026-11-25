# S3T-4 plan: attract shader dump, then the pack bin native4bp

M4 (successor of Agent 4), 2026-11-25 01:25. Paper only. **Nothing here runs before the Overseer's LOAD GO.**
Current native pin: **native4b `9b40acbbef4c57b3`** (Overseer, 11-25 01:16).

## 0. The screenshot kit on native4b: still valid, with two substitutions

Checked 01:18-01:23 (`build/agent4/screenshot-kit/README.md`, 6177F640617B8006):

- Kit files unchanged since the handoff: README 6177F640, `collect-shots.ps1` 071258EF, `native4-drops-r6off.txt`
  5BB27977, `missing_timeline.py` 23EB6EB0. The kit was **never run** (no `shots/` or `runs/`).
- Its inputs unchanged since before the kit was written: `harness/run-game.ps1` C2533FDF (11-22 04:42),
  `harness/routes/attract-long.txt` 4D35FAF4 (11-22 03:39), `build/agent3/vpad/xinput1_4.dll` (11-22 02:48).
- Bins present: devoff4-bin (MANIFEST 16DCC939), native4-bin (00D33D4F), native4b-bin (B63769FE), devoff4b-bin
  (DE11A914). M12 owns the check against the records.
- native4b has the same shader set as native4: only `memory_watch.cpp` and `rexlego/CMakeLists.txt` changed
  (REPIN.md 1.2), and snap1's AOT index is still the merge base 2DB85917 (repin_check [3], 01:20). So native4b drops
  the same draws, and the kit's "MISSING" list carries over.
- **Substitutions for a native4b run** (README not edited, to keep its hash; edit on your word):
  1. Command B: `-BinDir build\agent2\native4b-bin` (keep `-Tag sc-native` and `native_settings_frontend=false`;
     rpb0 booted native4b with the frontend on, but keep the flag so B matches the pack run).
  2. Command A: `build\agent2\devoff4b-bin`, so A and B again come from one source snapshot (S4b + S4c, every switch
     off). devoff4-bin (S4a) is also fine for a look: no S4b switch is on by default.
  - Cosmetic: `collect-shots.ps1` L157 hard-codes the labels "devoff4-bin" / "native4-bin" in `compare.html`.
    Pairing goes by tag, so the result is unaffected.
- The kit needs the user at the visible desktop (agent shells are on a hidden desktop): it is the user's one-hour slot.

## 1. The attract shader dump (one game run; waits for LOAD GO)

Why: from the 3D attract on, native drops draws from 46 more VS objects and 3 PS objects that were never dumped
(HANDOFF L24). The only dump, `0509-sd-r1`, had no input and never reached the attract. The pack may not cover them.

**Pre-flight** (all at the moment of launch): LOAD GO received with its limits; `perf-notes/WINDOW-HOLD.txt` absent;
`Get-Process legodimensions` empty; no build running. `run-game.ps1` only WM_CLOSEs/kills the PID it launched
(L297-304; the WerFault scan is read-only), so it can't touch Minecraft.

**Command** (repo root, agent slot, hidden desktop, functional only; ~9.5 min). Validated with `-DryRun` at 01:23:
every path absolute, nothing launched (`build/agent4/s3t4-dump/runs/20261125-012340-dump-dry`).

```
$d = "$PWD\build\agent4\s3t4-dump"
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\native4b-bin -Seconds 540 -Tag dump-attract-n4b -RunsRoot "$d\runs" -InputScript harness\routes\attract-long.txt -Cvar 'native_settings_frontend=false' -Env "LEGO_DUMP_MISSING_SHADERS=$d\shader-dumps;LEGO_NATIVE_TRACE_DIR=$d\trace"
```

- **Not `=1`.** `LEGO_DUMP_MISSING_SHADERS` is the dump **root directory** (`shaders.cpp` L562-597:
  `<root>/<category>/vs|ps-<hash>.bin`); `0509-sd-r1` used `<run>\shader-dumps`. `=1` would write into a folder named
  `1` under the run dir (CWD). Any non-empty value also turns on the copy verify in `hooks_buffer.cpp` L334 and keeps
  the full lookup path (`shaders.cpp` L212-224): functional only.
- `-Seconds 540`: the route's last step (`stop`) comes ~472 s after launch, after ~380 s of idle, which is enough to
  see the attract sequence (and a loop, if any). The kit's 360 s stops after S5.
- The trace turns off some fast paths and saves a present frame every 5 s (max 128): functional only, pairs only
  with traced runs. The game creates the trace dir itself.
- Bin: native4b-bin, the pin. No pack, no miss cache (`LEGO_NATIVE_SHADER_MISS_CACHE` unset).

**Pass / read-out** (paper, after the run):
1. Exit 0, `run.json` OK, no dump/WER, `input.csv` shows START, A, A delivered.
2. `$d\shader-dumps\placement-containers\` holds the 4 known containers with the same names and bytes as
   `0509-sd-r1` (ps-75A4D1AB 1716 B, ps-E81FD692 1640 B, vs-ACAF01F0 1304 B, vs-CCD76553 944 B): this doubles as
   VISUAL-CHECK 3.2's stability capture.
3. List every **new** file (any category). `missing_timeline.py` on `$d\trace\events.tsv` gives the drop timeline;
   compare it with `native4-drops-r6off.txt` (the 46 VS / 3 PS objects first bound ~117.7 s in).
4. Outcomes:
   - **No new containers** although the attract drops: the drops are not lookup misses that dump (another path). Then
     the 4-shader pack is what can be built; record that the attract stays partly dropped.
   - **New containers:** request (via the Overseer) M7's container check, as Agent 7 did for the first 4. Then a new
     scratch pack: `build/agent4/s35/run_pack.ps1` with the new containers as extra inputs, in a new run dir (it
     compiles: needs LOAD GO). That pack has new hashes, so `repin_check.ps1`'s `$S35` (run-071627) and
     `$PACK_HASHES` (4 entries) must be pointed at it first (a small edit I would stage).

## 2. The pack bin native4bp and its own re-pin

Order (REPIN.md 4.2; HANDOFF L27, L31, L33; RESUME 7 step 8). Owners in brackets; cross-manager steps go through
the Overseer.

| # | step | who | pass |
|---|---|---|---|
| 1 | Plan the copies: `repin_check.ps1 -Line snap1 -Pack` (dry run) | M4 | **done 01:21**: 0 FAIL, 0 WARN; plans the s35 cache copy (AEA36683) and the index copy over the merge base (E4C05782) (`repin/s3t4/after-snap1-pack-plan.txt`) |
| 2 | Agent checks VISUAL-CHECK 2-3 setup: decide the pack (4 shaders, or 4 + the attract's from section 1) | M4 + M7 | section 1 done |
| 3 | Apply the copies (`-Go -W4bDone` on the Overseer's word, or M2 by hand with backups and mtime = now), `cmake -D LEGO_NATIVE_RUNTIME_SHADER_CACHE=<tree>/rexlego/out/native-gpu/runtime-cache.cpp build/agent2/snap1-on`, the native build (it re-runs `lego_gpu_prelink_runtime` and the shader-preparation step, FINDINGS L147), stage to a **new** `build/agent2/native4bp-bin` with MANIFEST | M2, LOAD GO | build OK; native4b-bin untouched |
| 4 | `repin_check.ps1 -Line snap1 -Pack -BinDir build\agent2\native4bp-bin -FullHash -Report build\agent4\repin\pin-native4bp-<HHMM>.txt` | M4 | [4] built = recomputed, **not** 9b40acbbef4c57b3 (the fixed rule FAILs exactly this case, proven on a synthetic build dir: `repin/s3t4/synthetic-pack-oldpin.txt`); 4 of 4 pack hashes prelinked; [5] MANIFEST = built, not a pin |
| 5 | The user's look: kit command B with native4bp-bin, against the kit's reference shots and MISSING list (HANDOFF L28: rename `shots/` to `shots-before/`, keep tag `sc-native`) | user + Overseer | user's yes |
| 6 | `matrix-repin-packhit.json` (t0 native4b-bin vs t0p native4bp-bin, traced, 2 runs, ~12 min; always `-OutDir build\agent3\runs\...`) | M3, LOAD GO | t0 shows the misses (positive control); t0p 0 `draw_missing_*`, draws/frame >= t0, `check_n_rows.py` exit 0 |
| 6b | Suggested addition: a 1-run frontend-on boot check like rpb0 (`matrix-repin-native4b-boot.json` with the bin swapped), for D's `MANIFEST <fp>, game.log <fp>` identity line | M3 | `native3_boot_check.py` exit 0 |
| 7 | **PSO and seed recording for native4bp**: its first start rejects native4b's `native-pso-recipes.bin` / `native-pso-seed.bin` (fingerprint key) and builds PSOs cold. Record with native4bp itself: one unscored cold run on native4bp (run-matrix's default cold run per bin; not `-NoCold`, not `-ColdShared` across bins), and `seed_cache` only from native4bp arms. Never copy `cache/` or seeds from native4b runs | M8/M3 | cold run OK; later arms show a warm start |
| 8 | The Overseer announces native4bp as the pin | Overseer | 4-7 pass |

On any fail: native4bp-bin is parked, the pin stays native4b; rollback = the backup copies plus
`cmake -D LEGO_NATIVE_RUNTIME_SHADER_CACHE=<tree>/rexlego/out/native-gpu/stubs/runtime-cache.cpp build/agent2/snap1-on`.

**Trap for the next checker edit.** After native4bp is pinned, don't just add its fingerprint to `$PINS`: [4] FAILs
"pack configured + fingerprint in `$PINS`", and snap1-on would then sit in exactly that state with native4bp's own
fingerprint. Same lesson as today: change the rule first (e.g. FAIL only on pre-pack pins), add the bin to
`$oldBins`, and only then the `$PINS` line.
