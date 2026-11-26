# S5 item 3: log rejected TOML cvar values to game.log (staged, NOT built, NOT applied)

Base: rexglue-sdk a7e79c0. Diff: `toml-reject.diff` (+136/-3, 2 files). Verification: `check.py` → `check.txt` (RESULT: PASS).

## Problem
- `ApplyTomlTable` logs a rejected value (e.g. `present_effect = 'fsr'` against `.allowed({"bilinear"})`, presenter.cpp:74-78) with REXLOG_WARN at the moment of rejection.
- `LoadConfig` runs at rex_app.cpp:224/277, which is before `InitLogging` at rex_app.cpp:293. That means no file sink exists yet, so the line never reaches game.log.
- Correction to fsr-fallback.md: on Windows the early msvc (debugger) sink is NOT removed. The removal at logging.cpp:235-243 is under `#if !REX_PLATFORM_WIN32`. So the warning reaches a debugger only. The conclusion (it never appears in game.log) is unchanged.

## Design
All changes are in rexcore. No header changes. No exe change.

### src/core/cvar.cpp (overlay line numbers)
- Deferred queue, in the anonymous namespace (:77-148):
  - `DeferredConfigWarning{bool error; std::string text}`, a mutex and a `flushed` flag.
  - `g_config_file`.
  - `DeferConfigWarning()` (:99): dedupes, and does nothing once flushed.
  - `SourceName()`.
  - `DescribeConstraints()` (:130), which renders as "allowed: a, b", "range [lo, hi]", "custom validator" or "unparseable value".
- TOML reject (:213, `case ApplyResult::kRejected`): queues `Config: <key> = '<v>' in <file> rejected (<constraints>); keeping '<current>' (<source>)`. The entry is read under the registry mutex. The immediate REXLOG_WARN is kept, so the debugger still sees it at once.
- Unsupported TOML type (:193-195): also queued.
- `LoadConfig` parse error (:775-): queued as an ERROR: "... none of its settings were applied".
- `ApplyEnvironment` parse failure (:794-): queued.
- New `void rex::cvar::FlushDeferredConfigWarnings()` (:836):
  - Swaps the queue out under the lock, sets `flushed`, then logs each item outside the locks as REXLOG_WARN/ERROR, with the suffix " (reported before logging started)".
  - After the flush, `DeferConfigWarning` is a no-op, because the normal REXLOG path now reaches the file.
- `testing::ResetAllForTesting` (:883) also clears the queue and the flag.

### src/core/logging.cpp
- A local declaration `namespace rex::cvar { void FlushDeferredConfigWarnings(); }` (:66). This avoids touching `rex/cvar.h` and `rex/logging.h`.
- `InitLogging`: `lock_guard` → `unique_lock` (:218). At the end of the first-init path, after `flush_every`: `lock.unlock(); cvar::FlushDeferredConfigWarnings();` (:307-308).
- Unlocking first matters: the flush calls REXLOG, and REXLOG does not take `g_mutex`, but this keeps the lock order trivial anyway.
- Result: the warnings land in game.log right after the logger exists. That is before the app's `OnPostInitLogging` (rex_app.cpp:299) and before its fsr2/fsr3 remap.
- Why InitLogging and not rex_app.cpp: rex_app.cpp is NOT an SDK TU. It is compiled into the game exe via cmake/rexglue_helpers.cmake:70-82, so a call there would need a game rebuild and a new exe→rexruntime import.

## CLI / env path (unvalidated store)
- `ApplyFromSource` (:161) still applies CLI, env and late-registration replay values without validation (call sites :341/:345/:349, :727/:733, :806). The behaviour is unchanged.
- Fix applied: when `ValidateConstraints` fails, it now queues `<source>: <name> = '<v>' is outside the cvar's constraints (...); applied unvalidated, ...` (:168). This is warn-only.
- Making these sources reject values would change behaviour (e.g. a CLI `--present_effect=fsr` works today). So it is not done; that decision belongs upstream.

## Not fixed (noted)
- `FinalizeInit` is never called (src/system/xmemory.cpp:64 comment). So "Config: unknown cvar" never fires, and unknown TOML keys (e.g. today's unregistered `present_fsr_*`) stay silent.
- Flushing those at InitLogging would raise false positives for cvars that are defined in modules loaded later, so it was left alone.

## Expected effect on game.log (existing tomls)
- One WARN per rejected key, e.g. `Config: present_effect = 'fsr' in <...>.toml rejected (allowed: bilinear); keeping 'bilinear' (default) (reported before logging started)`.
- New WARNs for any CLI/env value outside its constraints.
- No value or behaviour changes.

## Risks
- Lock order is registry mutex → deferred mutex. Nothing takes them in the reverse order, and the flush logs outside both.
- If `InitLogging` is never called (a tool that uses only `InitLoggingEarly`), the queue stays in memory. It is small and deduped.
- `FlushDeferredConfigWarnings` is exported from rexruntime.dll via WINDOWS_EXPORT_ALL_SYMBOLS (src/system/CMakeLists.txt:56). This is harmless: the export is additive and nothing imports it.
- Duplicate immediate WARNs still go to the debugger sink only.

## PCH / rebuild scope
- Headers changed: none. `rex/cvar.h` is in every target's cmake_pch.hxx, which is why it was deliberately left untouched.
- Rebuild: 2 rexcore TUs (cvar.cpp, logging.cpp; rexcore is an OBJECT lib, src/core/CMakeLists.txt:4, without a PCH), then a rexruntime.dll relink. No game-exe rebuild.
- Single-TU timings from check.txt: cvar.cpp compiles in 22.7 s, logging.cpp in 5.4 s, both with 0 warnings.
- Independent of item 4 (native-fsr1 touches only presenter.cpp). The two diffs apply together.
