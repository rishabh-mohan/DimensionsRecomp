# Agent 11 session 2: helper A micro-benchmarks

RESUME (helper A, 18:40): all 5 benches written and compiled to build\agent11\a\ (bench_sleep, timer_highres_check,
bench_clock, bench_waitsignal, bench_lookup), plus run.ps1. bench_common.h: helpers appended in namespace bench_a only.
Smoke run (1 run each) -> build\agent11\a\smoke.txt. Next: fix smoke issues, then
`powershell -NoProfile -File bench\agent11\run.ps1` (logs build\agent11\a\<bench>.txt), then write results here +
README.md, then send_message to parent 08978114-9171-4eca-b7fa-525a8ba6df91.
Notes so far: clock.cpp now has the seqlock (bench_clock replicates it as NEW); Win32Timer still arms ABSOLUTE due
times from WClock_::now() = GetSystemTimeAsFileTime (coarse) -> timer_highres_check check 3 measures the effect.

(Results will replace this section.)
