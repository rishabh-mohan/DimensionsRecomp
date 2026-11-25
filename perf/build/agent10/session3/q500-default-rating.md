# #24 Q=500 default-ON rating: `q500-default.diff` (M9, S3T-9)

M10 (successor of Agent 10), session 3. Read-only work on 2026-11-25, 01:51-02:00: nothing was built or run. The diff was applied to a scratch copy only, which I then deleted. Rated for the **final build only**, not tonight.

**Files rated** (`build/agent9/session3/q500/`):

| file | sha256 (first 16) | size |
|---|---|---|
| `q500-default.diff` | 28F0D1DE76F824F0 | 5615 B, +33/-5, one file |
| `RISKS-FOR-M10.md` | 5FBF4B748997BC88 | 5799 B, 74 lines |
| `base/gpu_wait_backoff.cpp` (== live `DimensionsRecomp/rexlego/src/`) | 01D9F8F3464C8614 | 18177 B |
| `new/gpu_wait_backoff.cpp` | 74115EEA26C4AEB2 | 19865 B, 423 lines |
| `check.txt` | 9C059CD36707207B | 1353 B, RESULT PASS |

**Base and apply.** The live TU is 01D9F8F3, the file b2r §32/§37 rated and devoff4b's MANIFEST names. I copied it to a scratch tree and ran `git -c core.autocrlf=false apply --verbose`: it applied cleanly and gave 74115EEA == `new/`. `apply -R --check` exits 0. The diff touches only the TU: no CMake edit.

## Verdict

- **The code: SAFE.** The logic does what RISKS §Behaviour says:
  - unset or empty → the build default (500, so ON at Q 500);
  - `off`, any case, exact → OFF, no WARN, one INFO line (none when STATS prints its own line);
  - digits → as before;
  - anything else → WARN and OFF, as before.
  - A negative `-D` value restores the old behaviour exactly. The magic static and the hooks are unchanged; every hook still tests only `c.on`/`c.stats` (L327, L346, L367, L380, L410).
- **Default ON in the final build: SAFE-IF**, all of these:
  1. **Step-B gates PASS on the final bin** (RISKS R4, R5, R7):
     - the loaded-machine arm;
     - a functional pair, default vs `off`;
     - a timed confirmation: `off` / default / env 500, at least 4 reps, 2 passes;
     - a quiet-host repeat;
     - an f10 quiet pair, judged by the finding-10 rule (HANDOFF §6): a STUCK-LOCK is WARN only with CS 0x84959EDC, owner in sub_83FAF180 at lr 83FAF188/83FAF200, waiter lr 82A2A270, self-recovery and level reached; anything else FAILs;
     - the new-PC sweep.
     - W9 measured only the uncapped title screen. At Q 500 the mean effective sleep is about 1.06 ms per stalled wait (R5), so the timed arms must include level frame-time tails, not only means.
  2. **Time the shipped combination** (R8, R9). If CG26 (#26) or the d11p timer bundle also ships, the step-B timed and f10 arms run on that combination. Neither pair has been timed with default ON.
  3. **Land late, or pin the old default.** Every bin built from the live tree after this diff lands is default-ON. So land it only after the last bin that needs OFF semantics for an empty env, or build such bins with `-DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1` and record that in their MANIFEST.
  4. **Harness first** (R1, R2, R3, plus my S1). Before any run on a new bin:
     - every new-bin off/ref arm sets `LEGO_GPU_WAIT_BACKOFF_US=off`. That includes STATS-only probe arms like p1, which would otherwise become ON Q 500 plus stats;
     - `stage-window.ps1` and the GO checks refuse a new-bin arm that lacks the key, unless the arm is meant to be the default arm;
     - the expect/row-gate rules are per bin;
     - new-bin matrices name the default arm explicitly. Its log is identical to env 500, so run.json `env_set` plus the bin id is the only proof of which ran.
  5. **Compile and bin checks** (R13). Run `clang -fsyntax-only` with the devoff flags, then the real build.
     - The map's hooked aliases stay at 31 (no new hook).
     - The new exe contains the literal `GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=`. Old exes cannot contain it, since their OFF word is formatted at run time. Use it as the new-bin marker R1 proposes.
     - The native fingerprint is unchanged.
- No BLOCKER. 2 SHOULD, 3 NIT.

## What I checked

- **Parsing.** `IsOff` short-circuits on the first mismatch, so it never reads past the terminator ("", "o", "of" stop at the NUL). nullptr → false. `q_set` (`q && *q`) keeps the old empty = unset rule, and the WARN keeps the old condition, minus `off`. `static_assert(kDefaultQuantumUs <= 2000)` matches ParseUs's clamp. A non-integer `-D` value fails the compile, which is good.
- **Init line.** The ON line uses the same format and arguments as before, so default ON prints exactly env 500's line (R3 holds; W9's q500 expect rule matches it as is).
- **Native and fingerprint (R10).** CMakeLists L184-188 adds the TU only under `NOT LEGODIMENSIONS_NATIVE_GPU`. The fingerprint inputs (L604-625, plus the `src/gpu_native/*.h` glob at L753) don't include it, and the diff doesn't touch CMakeLists (the fingerprint's first input, L605). So there is no re-pin and native bins are unaffected. The CMake comment L181-183 ("Off unless ... set") goes stale. Leave it, per R10 (N2).
- **ON path.** Unchanged from what b2r §26 rated (no guest writes, no lock held while sleeping, the timer fails over to a yield) and §37 landed. W9 and s4bQ5 found sleep_fail 0 in 41 STATS lines and 0 STUCK-LOCK (RISKS §sleep_fail; I did not re-run it).

## Findings

- **S1 (SHOULD, harness). `off` is OFF on old bins, but it is not gate-clean there.** An old bin logs `GPU wait back-off: LEGO_GPU_WAIT_BACKOFF_US="off" is not a plain number; back-off stays OFF.` Every current expect file forbids that: `expect-w9.json` forbids "GPU wait back-off" in its off arm and counts "is not a plain number", whose notes say that text is forbidden in every run. `expect-w5b`/`expect-w4c` forbid "GPU wait back-off" in every arm. So RISKS L37 ("a safe explicit off value for every arm from now on") holds for behaviour, not for the gates. Rule: old-bin arms keep `env {}`; new-bin off arms set `off`. Condition 4 enforces it per bin.
- **S2 (SHOULD, release).** The env var is the only off switch for end users (R11), and Wine/Proton is untested (R6). Before shipping, document `LEGO_GPU_WAIT_BACKOFF_US=off` in the release notes, or land the cvar/toml follow-up. Before Win10 1803 the fallback is the SwitchToThread path (Q 0 behaviour), which is safe but saves less.
- **N1.** The OFF INFO line echoes the value as typed (`=off`, `=OFF`, ...). Write `off` in lowercase in matrices so a single exact rule matches (R14).
- **N2.** Stale text that stays: the TU header L1-2 ("DRAFT", "Syntax-checked only") and CMakeLists L181-183. Label notes and bins by whether they include 74115EEA (R12).
- **N3.** The default applies to Xenos builds only. If the release ships a native bin, this diff changes nothing there. Say so in the read-out so no saving is claimed for native.

## Read / Sent

Read: the diff, RISKS-FOR-M10.md, check.txt, `new/` L1-200 plus a grep for every `c.on`/REXLOG site, rexlego CMakeLists L178-192, L604-625 and L753-761, the `GPU wait` rules in `build/agent6/wnight/expect-w4c.json`, `expect-w5b.json` and `expect-w9.json`, the `GPU_WAIT` names in `bench/agent5/launch/run-night.ps1` (L41 allows the key), and b2r §26 and §37. Sent: this verdict to the Overseer.
