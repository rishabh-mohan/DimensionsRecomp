# M2 nops-smoke Z4 post fix rating

- Who/when: M10, 2026-11-25 20:46 (static review; no run)
- Request: Overseer 02:44Z (from M2)

## Files

| file | sha256/16 | bytes | note |
|---|---|---|---|
| build/agent2/s5/z4-post-delta.diff | 7F6CA2E9BA348477 | 5447 | 74 lines |
| build/agent2/s5/nops_smoke_post.py | 1B869FFC496516BD | 22011 | was 54BA5CF9 (pins-test/post-54BA5CF9.py, hash verified) |
| build/agent2/s5/nops-smoke/synth/synth_post.py | 4D2546933DB78905 | 4266 | was AE08FB82 (pins-test/synth-prev.py, hash verified) |
| build/agent2/s5/RUN-NOPS-SMOKE.cmd | B3B2A7BBE2E92E20 | 4410 | was 51E7A02E (pins-test/cmd-51E7A02E.cmd, hash verified); CRLF 73/73 |
| build/agent2/s5/nops-smoke/post/nops-smoke-post-20261125-201245-z4fix.txt | 6C2D24244FA390DC | 21108 | re-post of the 6 runs |

Base: nops-smoke-kit-delta-rating 51B6688E, kit-d1v2 43AD8609.

## Verdict

**SAFE**. No conditions beyond the open nops-kit ones (K4-K7/Z3/Z5/D2).

## What I checked

1. **The diff is complete.** `git diff --no-index --numstat` against the kept copies gives post +12/-3 and synth +10/-0, which equals the delta. The cmd differs from 51E7A02E in exactly 1 line: the post pin, now 1B869FFC = the file. There are still 13 `call :pin` lines and the `PINOK==13` fail-closed check is unchanged, so the tamper behaviour (19/19 at D1 v2) carries over: the pin block's structure is identical and only one hash value changed.
2. **The Z4 logic (L213-218).** The relaxed branch needs all three: `n_sd == 0`, at least one counter row, and `Title terminated; hard-exiting process` somewhere in `lines`. `lines` is the full joined game log of the arm (L289 `joined_log(rd)`, passed at L310), so the search isn't limited to occlusion lines. Every other case keeps the old `n_sd == 1` gate, so 2+ shutdown lines still FAIL.
3. **A crashed arm can't PASS through this.** A crash normally leaves no hard-exit line, which means no relaxed branch, so Z4 FAILs. Even if a crash came after the hard-exit line, Z4 is not the only gate: `clean exit` (exit 0, not early, close wm_close/script_stop) at L282 and `no dumps / crash events / WER` at L286 are separate gates (gate=g), and RESULT needs every gate to PASS. Z4 only stops the false FAIL on a clean WM_CLOSE.
4. **The synth cases** cover the PASS case (counter rows + hard-exit, which reports the stand-in periodic line), the FAIL case with rows but no hard-exit, and the FAIL case with hard-exit but no rows (2 Z4 fails asserted). This is the right negative set.
5. **The re-post 6C2D2424:** RESULT PASS. All 6 arms (A1 A2 T1 T2 N1 N2) show clean exit PASS (exit 0, wm_close), check-defaults PASS, and Z4 PASS via "shutdown line absent: hard-exit", with the stand-in a periodic line (frames 9096-11752, 13-15 counter lines each).

## Findings

- NIT N1: the hard-exit line isn't required to come after the last counter row. In practice nothing is logged after the hard exit, so this doesn't matter, but a `lines` index comparison would make the condition exact.
- NIT N2: the check name still reads '"shutdown" line once' when it passes through the hard-exit branch. The detail text explains it, but a name such as 'shutdown line once, or hard-exit + counters' would read better in summaries.
- NIT N3 (report-only data): in 6/6 runs the zpd-log "shutdown" counter line never appears on WM_CLOSE, so the S1 totals miss everything after the last periodic line (up to one period). This is fine for a report-only number. If exact totals matter later, either log the counters before the hard exit or say the totals are lower bounds.
- NIT N4: I didn't re-run tamper for B3B2A7BB. It's a one-hash change in mkpins output, so the result carries over (see check 1).
