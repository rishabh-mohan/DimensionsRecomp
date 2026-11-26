# Rating: M2 S5 items 3 (toml-reject) and 4 (native-fsr1)

M10, 2026-11-25 ~18:20. Static review only (FREEZE). M2's single-TU compiles from 17:45-17:46 are taken from its logs; I did not rerun them.

## Files

| File | sha256/16 | Bytes |
|---|---|---|
| build/agent2/s5/toml-reject/toml-reject.diff | 31C19232F88DFD6A | 8001 |
| toml-reject/NOTES.md | F30E80BB69DA3550 | 5353 |
| toml-reject/check.txt | BAFE4332F7B18C59 | 1641 |
| toml-reject/ov/.../src/core/cvar.cpp | 4C967C64AF26794B | 27236 |
| toml-reject/ov/.../src/core/logging.cpp | FBA29918A0C68FE5 | 19161 |
| build/agent2/s5/native-fsr1/native-fsr1.diff | 4579F090BD6F0983 | 2656 |
| native-fsr1/NOTES.md | 923AD5E457BB549C | 6075 |
| native-fsr1/check.txt | EEE2B7332C98417E | 2952 |
| native-fsr1/ov/.../src/ui/presenter.cpp | 944B98E5103E137A | 77462 |

## Base

rexglue-sdk a7e79c0 for both; rexlego a8e8dc8 for the native readers. check.txt (both): SDK HEAD and index == a7e79c0, overlay LF like the blob, snap1 copy == blob, apply-check PASS, fsyntax and -c exit 0 with the snap1 Release command, needles in the objs. native-fsr1's 4 warnings are pre-existing (all 4 also in the base TU).

## Verdict

- **toml-reject: code SAFE. A bin with it: SAFE-IF T1-T2.** It is diagnostics only; no cvar value changes.
- **native-fsr1: code SAFE. A bin with it: SAFE-IF F1-F3.**
  - The Xenos presenter behaviour is unchanged.
  - **On native it is a real behaviour and perf change**, because the harness toml asks for FSR 1 (F1).

## What I checked: toml-reject

1. **Locks: no deadlock, no inversion.**
   - The registry mutex is a `std::recursive_mutex` (cvar.cpp:43-44). So the new `lock_guard(GetRegistryMutex())` in the kRejected case (:219) is safe even if it is re-entered. In fact it isn't held there: SetFlagFromSource has returned.
   - `DeferConfigWarning` takes `g_deferred_mutex` and may run under the registry lock (ApplyFromSource from RegisterFlag :341-349, Init's CLI callbacks :727/:733). That gives the order registry → deferred, and nothing takes the reverse.
   - `DeferConfigWarning` doesn't log. `FlushDeferredConfigWarnings` swaps the queue out under the deferred lock and logs outside it.
   - In logging.cpp, `InitLogging` now uses `unique_lock`. The re-init path returns at :231 (RAII unlock). The first-init path unlocks at :307 before the flush, at the end of the function.
2. **Unknown keys don't reach the new kRejected message.** ApplyTomlTable defers unregistered keys before SetFlagFromSource (:199-204). So kRejected (:213) only means one of: constraint failure, setter failure, or init-only after finalize (unreachable; FinalizeInit is never called). This matches NOTES.
3. **ApplyFromSource (CLI, env, late replay): behaviour unchanged.**
   - The value is still applied first. `ValidateConstraints` only adds a deferred warning, and ValidateConstraints itself has no side effects beyond its own REXLOG_WARN lines (:277/:281/:296/:303).
   - Those existing WARN lines now also fire for CLI/env values outside their constraints. Before the flush they reach only the early sink; after it they reach game.log. So a late-registered cvar's out-of-range value is still visible after the flush, although the richer deferred message is a no-op by then.
4. **Statics.** `std::mutex` (constexpr ctor), `bool`, a `std::string` and a function-local static vector, all in rexruntime. They are initialised before any later-loaded DLL can trigger a late-registration replay. `ResetAllForTesting` clears the queue.
5. **Hot path:** none. All of this runs at config load, CLI parse, env parse or cvar registration.
6. **Expected game.log change on the harness toml** (harness/legodimensions.toml L37-40: `present_effect = 'fsr'`): one `Config: present_effect = 'fsr' in ... rejected (allowed: bilinear); keeping 'bilinear' (default) (reported before logging started)` per run.
   - `present_fsr_*` / `present_fsr_quality_mode` stay silent (unregistered keys are deferred).
   - run-timing counts game.log lines (L295) and the input scripts' wait_log steps match lines; one more line is harmless (T2).

## What I checked: native-fsr1

1. **Only the `#else` (no FidelityFX) branch changes**, and the FFX branch is byte-identical.
   - SDK readers of `present_effect`: only `BuildGuestOutputPaintConfigFromCVar` (presenter.cpp:266). Under `#else`, ParsePresentEffect (overlay :120-139) returns kBilinear for "fsr", so the Xenos output is identical to "bilinear".
   - The `present_fsr_*` getters in the SDK (:277-278) are FFX-only.
   - The new cvars match `include/rex/ui/flags.h:23-24` (int32_t, double), and nothing else defines them: git grep in rexlego/src finds only name-based reads.
   - The once-INFO uses an atomic exchange and runs at presenter init (after InitLogging).
2. **Native readers (rexlego a8e8dc8):**
   - device.cpp:2048 `fsr1_requested` (`!NativeFsr3Enabled() && present_effect == "fsr"`);
   - :2064/:2066 Query of sharpness and passes (clamped 1-4);
   - settings_snapshot.cpp:69-71; native_overlay.cpp:116-143; settings_frontend.cpp:141/231-234; settings_registry.cpp:40-42 (same defaults 0.2 / 4 and ranges); legodimensions_app.h:446-449 (fsr2/fsr3 → fsr remap).
   - Today the TOML 'fsr' is rejected, so none of these paths run FSR 1. With the diff they do.
3. **The harness toml enables FSR 1 for every native timed run** once a bin carries this diff. Both harness/legodimensions.toml (B763DABB, pinned via C2) and DimensionsRecomp/perf/harness/legodimensions.toml have:
   - `present_effect = 'fsr'` (L37)
   - `present_fsr_max_upsampling_passes = 1` (L38)
   - `present_fsr_sharpness_reduction = 0.0` (L40)
   - `native_fsr3 = false` (L73)
   - EASU/RCAS, plus the forced clear at device.cpp:2058, add GPU time. Every native perf number from such a bin is on a different workload from S5 and all earlier baselines.

## Conditions

- **T1:** Build only after the window, with the FREEZE lifted, on the Overseer's GO. It changes rexruntime.dll (rexcore TUs), so a bin with it is a new bin: new MANIFEST/BIN-PINS, pe-check exports NEW ⊇ REF (one additive export, FlushDeferredConfigWarnings). The pinned S5 bins are never rebuilt in place.
- **T2:** First smoke: game.log has the one `present_effect ... rejected` line (without native-fsr1) and no new ERROR. wait_log patterns in the input scripts still match.
- **F1:** A bin with native-fsr1 must not be compared against S5 or earlier native numbers with the current harness toml. Either:
  - set `present_effect = 'bilinear'` in a copy of the toml used for perf (a new pinned toml sha, C2-style); or
  - treat FSR 1 on as a new arm and re-baseline.
  - Say which one in the plan before any timed run.
- **F2:** Update perf/bench/agent7/native3_boot_check.py:340-347 (as NOTES says) before running it on such a bin. Otherwise it reads `present_fsr_sharpness_reduction` in rexruntime.dll as "FFX SDK built" and misreports.
- **F3:** Visual check on native with FSR 1 actually on (passes 1, sharpness 0.0 as in the toml): `spatial_fsr_presented=1`, no artefacts, overlay/settings menu toggles work. The kRequiresRestart semantics stay as before.

## Findings

- **S1 (SHOULD, native-fsr1):** F1 is the main risk. The diff silently changes the native workload of every existing bench config. Mark it in the bin's MANIFEST ("native FSR 1 active with harness toml").
- **n1 (NIT, toml-reject):** On a setter failure for a cvar with constraints, the message lists the constraints rather than "unparseable value". Slightly misleading, but harmless.
- **n2 (NIT, toml-reject):** After the flush, `DeferConfigWarning` is a no-op, so the richer "applied unvalidated" text never appears for late-registered cvars. ValidateConstraints' own WARN still does.
- **n3 (NIT, native-fsr1):** `0.2f` stores 0.2000000030 in a double. The FFX build's constant behaves the same, and NOTES confirms the serialised text is unchanged.
- **n4 (NIT, both):** With both diffs applied, toml-reject's "rejected" line for 'fsr' disappears and the INFO line appears instead. The T2 smoke expectation depends on which diffs the bin carries.
