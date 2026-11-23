# GPU-wait back-off ON by default through cvars: design note (proposal)

Task #30 item 2. **This is a proposal only.** None of it is in a live tree. Apply none of it before the formal W9
readout from Agents 7 and 8 and the gates in section 8. Paths are relative to the workspace root. Line numbers
were checked on 11-23 at about 06:00.

## 1. Why

- Today #24 is set only by environment variables. `DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp` reads
  `LEGO_GPU_WAIT_BACKOFF_US`, `LEGO_GPU_WAIT_SPIN_US` and `LEGO_GPU_WAIT_STATS` once, in `Cfg()` (:17-25,
  :119-149). If Q is unset, the back-off is OFF.
- Turning it on by default through the environment would mean every user sets a variable. The game already has
  a config system for this, the SDK cvars:
  - they load from `legodimensions.toml` next to the exe (`DimensionsRecomp/rexglue-sdk/src/ui/rex_app.cpp:222-224`);
  - they can also be set from the command line and from `REX_*` environment variables.
- W9 shows the back-off saves 0.7-0.8 core with no fps cost (HANDOFF.md section 4). With the default ON, every
  user of the Xenos path gets that. The cvar keeps a one-line way back.

## 2. The cvars

Define them in gpu_wait_backoff.cpp, the TU that uses them. Follow the pattern of `gpu_native_texture_watch`
(`DimensionsRecomp/rexlego/src/gpu_native/memory_watch.cpp:13-18`) and `native_fps_limit`
(`DimensionsRecomp/rexlego/src/gpu_native/device.cpp:75-76`).

| cvar | Type | Default | Range | Automatic env name |
|---|---|---|---|---|
| `gpu_wait_backoff` | bool | false in step A, true in step B | - | `REX_GPU_WAIT_BACKOFF` |
| `gpu_wait_backoff_us` | int32 | 500 (or the readout's pick) | 0..2000 | `REX_GPU_WAIT_BACKOFF_US` |
| `gpu_wait_spin_us` | int32 | 30 | 0..200 | `REX_GPU_WAIT_SPIN_US` |
| `gpu_wait_stats` | bool | false | - | `REX_GPU_WAIT_STATS` |

- All four use category "GPU" and `.lifecycle(rex::cvar::Lifecycle::kRequiresRestart)`, because `Cfg()` reads
  them only once.
- The SDK derives the env names itself (`DimensionsRecomp/rexglue-sdk/src/core/cvar.cpp:70-77`; ApplyEnvironment
  is at :694-717).
- TOML tables flatten with "_" (cvar.cpp:97-103). So `gpu_wait_backoff = false` at the top level and
  `[gpu]` + `wait_backoff = false` both work.

Sketch (not compiled; the modifiers chain as in `DimensionsRecomp/rexglue-sdk/include/rex/cvar.h:281-303`):

```cpp
REXCVAR_DEFINE_BOOL(gpu_wait_backoff, false, "GPU",
    "Sleep instead of spinning in long GPU fence/query waits (Xenos path)")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_INT32(gpu_wait_backoff_us, 500, "GPU",
    "Back-off sleep per poll in us; 0 = yield only")
    .range(0, 2000)
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_INT32(gpu_wait_spin_us, 30, "GPU",
    "Spin before the first yield of a stalled wait, in us")
    .range(0, 200)
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_BOOL(gpu_wait_stats, false, "GPU",
    "Log GPU wait counters every 5 s (profiling only; never in a timed run)")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
```

## 3. Precedence in Cfg()

1. **The legacy env goes first.** If `LEGO_GPU_WAIT_BACKOFF_US` is set and not empty, it decides, exactly as
   today:
   - a valid value means ON with that Q;
   - an invalid value logs the existing WARN, and the back-off is OFF. OFF is the safe state, and whoever set
     the variable meant to control the back-off.

   `LEGO_GPU_WAIT_SPIN_US` and `LEGO_GPU_WAIT_STATS` follow the same rule: if set, they win. An invalid spin
   value logs the WARN and S comes from the cvar.

   With this rule, every existing matrix, gate and note keeps its meaning on old and new bins.
2. **Otherwise the cvars decide.** The SDK has already applied its order: default < toml < `REX_` env <
   command line (cvar.h:142-150).
3. **The TU checks ranges itself.** Command-line and env values skip `.range()`: ApplyFromSource
   (cvar.cpp:87-94) does no validation; only SetFlagFromSource (:298-338) does. So:
   - a negative Q logs a WARN, and the back-off is OFF;
   - a negative S logs a WARN, and S is 30. This is the same as today's "-5" rule (:22-23);
   - values over the maximum clamp, as ParseUs does (:115).

Pseudo-code (S and stats follow the same pattern):

```cpp
const char* q = std::getenv("LEGO_GPU_WAIT_BACKOFF_US");
if (q && *q) {                                   // legacy env decides, unchanged
  c.on = ParseUs(q, 2000, &c.quantum_us);        // invalid -> existing WARN, OFF
  c.why = "LEGO_GPU_WAIT_BACKOFF_US";
} else {
  const int32_t cq = REXCVAR_GET(gpu_wait_backoff_us);
  c.on = REXCVAR_GET(gpu_wait_backoff) && cq >= 0;   // cq < 0 -> WARN, OFF
  c.quantum_us = cq < 0 ? 0u : std::min<uint32_t>(static_cast<uint32_t>(cq), 2000u);
  c.why = SourceText(rex::cvar::GetFlagSource("gpu_wait_backoff"));  // cvar.h:201-202
}
```

`SourceText` maps `rex::cvar::Source` (cvar.h:142-150) to text such as "default", "config", "env" or "command
line".

## 4. Logging

Print at most one init line, as today:
- **ON:** today's line, byte for byte: "GPU wait back-off: ON (quantum Q us, spin S us); stats ...; GetData hook
  built." Agent 8's run proofs and Agent 6's counters match on it, so it must not change.
- **OFF with stats ON:** today's line with "OFF", unchanged.
- **OFF, stats off:** a new line, printed only when OFF was chosen explicitly or forced by an invalid value:
  "GPU wait back-off: OFF (<why>)". Examples: "gpu_wait_backoff=false from config", "LEGO_GPU_WAIT_BACKOFF_US
  invalid".
  - In step A (default false), an untouched run prints nothing, so its OFF logs match today's.
  - In step B (default true), every OFF run is explicit, so its log says why.
- **Expect files:** Agent 6's expect files count lines that contain "GPU wait back-off:".
  - For step-B bins they need separate ON and OFF counters: an off arm expects one OFF line and no ON line.
  - Old bins keep the current rule (perf-notes/agent6-attract-stalls.md:829).

## 5. Ways to turn it off (step B)

- toml: `gpu_wait_backoff = false`, or `[gpu]` + `wait_backoff = false`;
- command line: `--no-gpu_wait_backoff` (bool flags take `--name` and `--no-name`, cvar.cpp:626-633);
- env: `REX_GPU_WAIT_BACKOFF=false`.

The legacy env has no clean OFF value: only an invalid value turns it off, and that logs a WARN. Bench off arms
should use the cvar.

The saved config holds only non-default values (SerializeToTOML, cvar.cpp:578-590). Check whether a step-A save drops a hand-written
`gpu_wait_backoff = false`, which equals the default in step A. If it does, users who want OFF must set it again
after step B.

## 6. Bench and gate rules

- **Old matrices stay valid.** devoff4b-bin has no cvars, and `env {}` still means OFF there.
- **On step-B bins, `env {}` means ON at the default Q,** so every off arm must set the cvar
  `gpu_wait_backoff=false` explicitly.
  - Two checks should refuse an off arm without it on a bin that has the cvar: the window staging check
    (`build/agent8/w-followup/stage-window.ps1`) and the launcher's GO checks
    (`bench/agent5/launch/run-night.ps1`).
  - Such a bin can be recognised by the "gpu_wait_backoff" string in the exe.
- **Unknown names:** a cvar name that isn't registered logs one WARN, "Config: unknown cvar", at FinalizeInit
  (cvar.cpp:719-725). A matrix that sets `gpu_wait_backoff=false` on devoff4b or a native bin only gets that
  WARN, and the logdiff expect files should allow it.

## 7. Build impact

- **Only the TU changes** (gpu_wait_backoff.cpp): no SDK change, no CMake change.
- **Native builds don't compile the TU** (CMakeLists.txt:184), so the cvars don't exist there. A toml that sets
  them logs the unknown-cvar WARN once, which is acceptable.
- **No native re-pin.** The native fingerprint inputs are CMakeLists.txt itself and the local headers
  (CMakeLists.txt:604-625, :753-761), not gpu_wait_backoff.cpp.
- **Do not edit the CMake comment at :181-183** ("Off unless LEGO_GPU_WAIT_BACKOFF_US is set"), even though step
  B makes it stale. Any edit to CMakeLists.txt changes the native fingerprint. Fix the comment at the next planned
  re-pin, and update the TU's own comment (:17-25) in step A.
- **The map check stays at 31 hooked aliases,** because the hooks don't change (perf-notes/agent2-baseline.md:40-44).
- **Size:** about 60-80 changed lines.

## 8. Two steps

**Step A: refactor with default false (no behavior change)**
- Change: sections 2-4, with `gpu_wait_backoff` defaulting to false.
- Gates:
  - Agent 10's static review (section 9);
  - the map check shows 31;
  - a functional pair on the step-A bin against devoff4b-bin: off (nothing set) and env q500. Logdiff must show
    NEW 0 / MORE 0, the same exit codes and the same ON line;
  - one run with only the toml line `gpu_wait_backoff = true`: it must print the ON line with Q 500, S 30;
  - one run with `LEGO_GPU_WAIT_BACKOFF_US=250` plus `--gpu_wait_backoff_us=1000`: the ON line must say
    quantum 250, because the legacy env wins.
- No timed window is needed when the logs match.

**Step B: flip the default to true (a one-line change)**

Before the flip, all of these must be done:
1. The formal W9 readout has picked Q, and the cvar default follows it.
2. A functional Q = 500 run with stats shows sleep_fail == 0. It has never been observed at 500.
3. Agent 6's loaded-machine arm (agent9-codegen.md S5.2.4 step 4) shows no slow-frame regression.
4. A functional pair, default against `--no-gpu_wait_backoff`, shows:
   - logdiff NEW 0 / MORE 0 apart from the init or OFF line;
   - the same exit codes;
   - no new STUCK-LOCK.
5. A timed confirmation: explicit off vs default vs env q500, at least 4 repeats, 2 passes. The default must match
   env q500 within noise and beat off on CPU.

Prefer a quiet host or the new PC for items 3 and 5 (HANDOFF.md, open question 3).

## 9. Checklist for Agent 10

- **OFF path unchanged:** when `!on`, every hook calls `__imp__` at once.
- **No hot-path cost:** the cvars are read only inside the `Cfg()` magic static.
- **Init order:** `Cfg()` must first run after cvar setup:
  - `rex::cvar::Init` and `ApplyEnvironment` (`DimensionsRecomp/rexglue-sdk/src/ui/windowed_app_main_sdl.cpp:40-41`);
  - LoadConfig (`DimensionsRecomp/rexglue-sdk/src/ui/rex_app.cpp:222-224`).

  Both must come before the first hooked fence or query poll. Confirm that no hook runs earlier, for example
  during boot GPU init.
- **Benign race:** a runtime UI write that races with the first `Cfg()` call is harmless. It reads one bool or
  int, and kRequiresRestart says changes apply after a restart.
- **Range checks:** negative and too-large values are handled in the TU, because CLI and env values skip
  `.range()`.
- **No name clashes:** grep `REXCVAR_DEFINE` for `gpu_wait_` in both repos. `REX_GPU_WAIT_*` and
  `LEGO_GPU_WAIT_*` stay distinct names.
- **Documented:** the TU comment (:17-25) covers the legacy precedence and the OFF line.
- **Native builds:** only the unknown-cvar WARN.
