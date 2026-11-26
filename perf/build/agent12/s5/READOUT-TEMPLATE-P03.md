# S5 Phase 0.3 baseline read-out (template; fill in from build\agent12\s5\p03\)

Matrix `build\agent8\s5\matrix-s5-baseline.json` (57255790), out `build\agent8\s5\matrix\<stamp>`; route attract-long; window = 120 s from the sustained ≥1500-draw anchor; cap60 unless stated otherwise.
Sources: `p03-gates.txt` / `.json` (sha8 ____), `p03-readout.txt` / `.json` (____), `p03-readout-noflag.txt` (____). Tools: s5_gates.py ____, s5_readout.py ____.

## Gate verdicts (scored runs; from the read-out header "gate verdicts per arm")

| arm | bin | n run | PASS | FLAG | VOID | VOID / FLAG reasons (p03-gates.txt) |
|---|---|---|---|---|---|---|
| ship60 | devfinal2-bin / 60 | 4 | | | | |
| nat60 | nativefinal2-bin / 60 | 4 | | | | |
| n4bp60 | native4bp-bin / 60 | 4 | | | | |
| natU | nativefinal2-bin / none | 2 | | | | |

Unscored and skipped: cold-ship60, cold-nat60, cold-n4bp60 (gates header "skipped"). The scored set should equal results.csv scored=True (14).

## Arm medians [95 % bootstrap CI of the median] (p03-readout.txt "== arm")

| metric | ship60 | nat60 | n4bp60 | natU (info) |
|---|---|---|---|---|
| fps | | | | |
| p99 ms | | | | |
| 1 % low ms | | | | |
| frames ≥100 ms /min | | | | |
| frames ≥250 ms /min | | | | |
| max ms | | | | |
| GPU util % / clock MHz / W | | | | |
| thermal share | | | | |

## Contrast 1 (PRIMARY): nat60 vs ship60 — "nativefinal2-bin/60 : devfinal2-bin/60"

| metric | nat60 | ship60 | median diff | % of ship60 [95 % CI] | word | paired by round (n, % [CI]) |
|---|---|---|---|---|---|---|
| fps | | | | | | |
| p99 ms | | | | | | |
| 1 % low ms | | | | | | |
| ≥100 ms /min | | | | | | |
| ≥250 ms /min | | | | | | |
| max ms | | | | | | |
| GPU util / clock / W | | | | | | |
| thermal share | | | | | | |

## Contrast 2 (SECONDARY): n4bp60 vs nat60 — "native4bp-bin/60 : nativefinal2-bin/60 (secondary native4bp:nativefinal2)"

Question: does the missing-draw fix (native4bp) cost or gain fps / p99?

| metric | n4bp60 | nat60 | median diff | % of nat60 [95 % CI] | word | paired by round (n, % [CI]) |
|---|---|---|---|---|---|---|
| fps | | | | | | |
| p99 ms | | | | | | |
| 1 % low ms | | | | | | |
| ≥100 / ≥250 ms /min | | | | | | |
| max ms | | | | | | |

## Info: natU vs nat60 — "nativefinal2-bin/none : nativefinal2-bin/60" (n 2 vs 4); n4bp60 vs ship60

| contrast | fps % [CI] | p99 % [CI] | word |
|---|---|---|---|
| natU vs nat60 | | | |
| n4bp60 vs ship60 | | | |

## Sensitivity

- Without FLAG runs (`p03-readout-noflag.txt`): primary fps % [CI] ____ ; secondary fps % [CI] ____ ; same direction? ____
- Literal-first anchor (`p03-readout-first.txt`, info): primary fps % ____

## Host-load confound (M16, 18:34) — `p03-confound.txt` / `.json` (sha8 ____), s5_confound.py ____

> CONFOUND: host load and effective CPU clock varied during window 20261125-1804. M16 saw ship60 / n4bp60 runs at ~5.3-7.5 nongame cores and ~1.6-1.75 GHz vs nat60 at ~3.0-3.8 cores and ~2.7 GHz (MsMpEng 1.35-1.8 vs ~0.9 cores); the per-run table below gives the whole set. The arm fps / p99 contrasts above may mix the renderer effect with host load / CPU clock. This sentence goes into every summary that quotes Contrast 1 or 2.

Confound check (line "== confound check"): PRESENT / not detected — ____

Per run ("== per run"; VOID runs listed but not summarised):

| run | verdict | nongame cores | eff CPU MHz | MsMpEng cores | game cores | thermal share / GPU °C | fps (gate) | low-load fps | low-load median ms | low-load sec share | high-load fps | corr(ng, fps/s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60-r1 | | | | | | | | | | | | |
| … | | | | | | | | | | | | |

Per arm ("== per arm", median [range]):

| arm | n | nongame cores | eff CPU MHz | MsMpEng cores | thermal share | fps (gate) | low-load fps | low-load sec share |
|---|---|---|---|---|---|---|---|---|
| ship60 | | | | | | | | |
| nat60 | | | | | | | | |
| n4bp60 | | | | | | | | |
| natU (info) | | | | | | | | |

POST-HOC low-load contrasts (seconds with nongame < 4 cores only; non-gating, descriptive; "== POST-HOC low-load contrast"):

| contrast | low-load fps % of B [CI] | low-load median ms % [CI] | all-seconds fps % [CI] | low-load seconds A / B | word |
|---|---|---|---|---|---|
| nat60 vs ship60 | | | | | |
| n4bp60 vs nat60 | | | | | |
| n4bp60 vs ship60 | | | | | |

Read-out of this section: does the all-seconds gap shrink on low-load seconds? ____ . Post-hoc caveats: seconds are selected on a host variable after the fact; the scene mix per second differs; loaded arms have few low-load seconds; per-second sys.csv rows are 1 Hz snapshots on the t_s launch clock.

## Wording rules

- CONFOUND: never write "n4bp60 X % slower" (or any "<arm> X % slower/faster") without the confound sentence above in the same paragraph. The low-load rows are post-hoc and can't replace or override the gated contrasts or their verdicts.
- Say "higher" or "lower" only when the CI excludes 0; otherwise say "not resolved". Never write "equal", "no difference" or "no cost".
- p99, 1 % low, max and the ≥100/≥250 ms counts are tails, and at n 4 they are noisy: give ranges and treat them as descriptive.
- ship60 is GPU-bound below the cap (~34-46 fps), so "below cap" is info, not a fault. Native cap60 runs near 60 fps are capped, so a fps difference there is bounded by the cap: read p99 / 1 % low / GPU util for those.
- Thermal is a covariate: report clock, W and thermal share next to fps. Do not adjust fps for it.
