# Black scene in natives5fsr1 (F3A and F3B): diagnosis

M2, 2026-11-26 ~04:11. Read-only. Nothing was launched or changed.

## Finding: the cause is the bin, not FSR, env or capture

natives5fsr1 = nativefinal2 + a rebuilt rexruntime.dll. Its exe is nativefinal2's (090A420B, native GPU fingerprint 1616ce65e973c583). That exe **lacks the AOT placement pack** that native4bp adds: "nativefinal2 + AOT placement pack (83 containers)", fingerprint 39129c4c059be5f0, index 19116 -> 19267 rows (native4bp MANIFEST).

The first scene shader pair the title binds isn't in nativefinal2's index:

| | gpman 02:42 (native4bp) | RT F3A 04:03 / F3B 04:07 (natives5fsr1) |
|---|---|---|
| `Native GPU [fp]` | 39129c4c059be5f0 | 1616ce65e973c583 |
| VS 0xAC449538 | `adopted vertex shader ... hash=0xACAF01F01E1C03D2` (game.log L417) | `placement vertex shader ... prefix=0xDCD4AD8441398283 missing from AOT index`, then `unrecognized vertex shader resource` (L405-407; F3B L416) |
| PS 0xAC448F28 | `adopted pixel shader ... hash=0x75A4D1ABA62F7594` (L418) | `unrecognized pixel shader resource` (L408-409; F3B L418) |
| DoF filter | `pixel shader filter matches 1 AOT containers` | `... matches 0 AOT containers` |
| other | - | `query ... invalidated by failed draw` x16, only here |

Static check of the AOT indexes:
- snap1/nativefinal2 `snap1\...\out\native-gpu\lego-microcode-index.cpp` (2DB85917): ACAF01F01E1C03D2 0 hits, 75A4D1ABA62F7594 0 hits.
- native4bp pack `agent16\pack\run-20261125-173813\lego-microcode-index.cpp` (401C1801):
  - `{ 0xDCD4AD8441398283, 0x033935513ABF2DCB, 0xACAF01F01E1C03D2, 324, 0, 0 }`
  - `{ 0xC77B3ABB6F87ACD9, 0x0DD13E570A16128B, 0x75A4D1ABA62F7594, 208, 1, 1 }`

`BindShader` (shaders.cpp:782-801) clears the bound shader for an unrecognized resource and returns false, so those draws fail. The `unrecognized` warning stops after 32 lines (`g_shader_warning_count < 32`), so the log can't show the full count. M10 noted 700-1800 draws per frame; those are attempted draws.

The present path is fine:
- device.cpp:2042-2149 clears the target (always under FSR1) and copies the source with FSR1 or bilinear, then draws the fps digits with clears.
- A black scene with a live counter means the source texture itself is black.
- Same in both arms. Scene and output sizes are identical to gpman (1920x1080 -> 2240x1294).
- No scale or viewport difference: frames.csv config and toml match, per M10 and my diff.

## Ranked hypotheses

1. **Bin, ~certain.** nativefinal2's exe has no placement containers. Placement-shader draws fail, so the scene is black in both arms. Evidence: the log lines and index check above.
2. **Trace env, very unlikely.** `LEGO_NATIVE_TRACE_DIR` only turns on `LongProbeEvent` file writes. long_probe.h:1 says "No guest or rendering state is modified here". The only side effect is `g_probe_capture_requested`. It can't make shaders unrecognized.
3. **vpad / xinput input, very unlikely.** The failure starts at 04:03:16.5, about 1.5 s after the first present and before any route step matters. F3A and F3B show the same thing.
4. **Rebuilt rexruntime (presenter.cpp) / FSR1, ruled out.** F3B (bilinear) is black too, and the failure is in exe-side shader lookup.

## Cheapest separating test / fix (each needs an M10 rating)

The static check already separates (1) from (2) and (3). The cheapest test that also fixes the problem:

- **Stage `s5/natives5fsr1p-bin`** = native4bp-bin with only `rexruntime.dll` replaced by natives5fsr1's.
  - natives5fsr1 differs from nativefinal2 only in rexruntime.dll.
  - native4bp differs from nativefinal2 only in exe and map.
  - native4bp's MANIFEST already has "pe-check ON exe vs nativefinal2 (exports/imports equal)".
- Gates:
  - Every file identical to its source.
  - rexruntime sha equals natives5fsr1's.
  - pe-check of exe imports vs the new rexruntime exports.
  - Offline: none.
- Then the kit with only the bin pin changed (pinsonly + tamper + dryrun). Then one GO `noshots arms=F3A,F3B` with manual-capture, N5 check at >=120 s (per M10: state 0, not the 60 s install prompt).
- Expected:
  - Log shows `Native GPU [39129c4c059be5f0]` and `adopted vertex shader 0xAC449538`. No `unrecognized` at boot.
  - Content in both arms.
  - If it's still black with the 4bp exe, hypothesis 1 is wrong and (2)/(3) are next, e.g. the same kit with the trace env set.
- Cold PSO cache: fingerprint 39129c4c means the first boot compiles from scratch, as in the 03:50 hang note (stall-frames.md). The kit already starts with an empty cache, so nothing changes there.

Optional zero-launch extra check: the gpman trace `events.tsv` (build\agent3\gameplay\trace-native-20261126-024214) gives native4bp's uncapped `unrecognized_shader` count. Not needed for the decision.

Not done: smoke3d-native.png wasn't found under the WS (`dir /s` timed out or found nothing). Its bin is unknown.

Helpers: SCR\logdiff.py, output SCR\logdiff-out.txt.
