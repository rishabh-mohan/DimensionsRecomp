# S4a precise-wait ON smoke (#38) for Agent 3 (Agent 11, run-2 task #14, 13:28)

Functional only (hidden desktop), never timed. One short run, no level load. Your queued r4 already fits; this pins its flag, its proof line and its pass lines.

## Run (= your queued r4)

- **devoff4**, identical to your OFF run r1 (same bin folder, route `harness\routes\b-gate-menus-long.txt`, `-Seconds 420`, attach.ps1 sampling) except one setting.
- **Flag:** `--timer_queue_precise_wait=true` on top of the standard flags.
  - With run-game.ps1, `-Arg 'timer_queue_precise_wait=true'` puts it on the command line: `--log_file=... --log_flush_interval=1 --perf_log_csv=... --native_settings_load=false --discord_rpc=false --audio_mute=true --pause_when_unfocused=false --timer_queue_precise_wait=true --input_backend=xinput`.
  - Your queued `-Cvar 'timer_queue_precise_wait=true'` (the run's own toml) is equivalent: the cvar is kInitOnly and is read at the first `QueueTimer`, after the command line, environment and config are applied. Either is fine; the proof line decides.
- Nothing else ON. #38 is SDK code, so native4 has it too, but one devoff4 run is enough.

## Proof it's on

The diff's only new log line (`timerq.diff` L49 = staged `timer_queue.cpp`:71, `REXLOG_INFO` inside `std::call_once`):

```
TimerQueue: precise wait (timer_queue_precise_wait)
```

- **r4:** exactly 1 line, at `[info]`, early in boot, before the first frame. The first `QueueTimer` is the 1 ms KeTimeStampBundle timer, created in the XboxkrnlModule constructor. s4a_check shows it as `precise_wait=1`.
- **r1:** 0 lines.
- No line in r4 means the switch is not on: stop, report, don't rate.

## Pass (all three)

1. **Boots to attract:** summary verdict OK, first frame logged, all route steps done as in r1, a clean WM_CLOSE (exit 0), no dumps, no crash events.
2. **No new errors or asserts:**
   - logdiff vs r1 at warning: NEW 0 and FLAG 0. No `--allow-new` is needed: the proof line is info level, so it shows up only under "NEW at info".
   - [error] count no higher than r1's.
   - No `[FATAL]`, `STUCK-LOCK` or assert lines beyond r1's.
3. **Ticks still advance:**
   - (a) The TimerQueue thread runs the whole time: in `threads-s4a.csv` its `cycles` rise in every 2 s sample. Its `cpu_ms` is charged in timer-tick steps, so at a few % it can stay flat for one sample; `cycles` is exact.
   - (b) The game moves on its own clock: intro to title/attract without input, and the same stable scenes at the route marks as r1 (s4a_check scenes). A frozen TickCount would show up as a hang or a frozen scene.

## CPU drop (the effect; report it, it's not a timing number)

- **Thread name:** `rex::thread::TimerQueue` (`set_current_thread_name`, staged `timer_queue.cpp`:245). s4a_check matches `*TimerQueue*`.
- **Command:** `python build/agent3/s4a/s4a_check.py --cand <r4 run> --base <r1 run> --tq-ref <r1 run>` prints both runs' share, as % of one core from the first frame + 20 s to the last sample - 10 s.
- **Before (r1, OFF = spin):** expect ~30-45% of one core. Earlier measurements: 31.0-44.1% in 3 hidden-desktop runs (03:30-04:00), 62% in window 3 (interactive desktop), 52% native.
- **After (r4, ON):** expect a few %. Game-free bench: precise 1.9% against spin 30.4%; blocking in game was 0.3-0.5%.
- **Effect seen:** r4 <= ~5% and <= 1/5 of r1.
  - If r4 stays near r1 (> 10%), the high-resolution timer is probably missing (the bench's "no high-res" row: 32.7%).
  - Report that as "on, no effect". It is still a functional pass if 1-3 hold.

## Then

Send me (Agent 11) the r4 and r1 run dirs and the s4a_check text. I write the verdict into `perf-notes/agent11-kernel.md`.
