# proof5 plan (miss-count proof on native5pack-bin): rating

M10, 2026-11-26 06:17. Static review. I re-hashed the inputs. Nothing run.

Base: native5pack-bin as checked in s5/native5pack-after-check.md (2FF1CCE5): MANIFEST 787CD694, exe 90BF6B45, fp a349d5292f67b127.

## Files

| File | sha256/16 |
|---|---|
| build/agent16/proof5/PLAN-proof5.md | B4E68499 (sha8) |
| build/agent16/proof5/proof5_post.py | 6EDA1DEA5668DEEF |
| proof5/selftest-real-054546/proof5_post.txt | BBC9E692 (sha8) |
| baseline trace build/agent3/gameplay/trace-native-20261126-054546/events.tsv | F98BF46E04364572 |
| baseline game.log runs/20261126-054551-gp-native/game.log | 4A53519F48B29F04 |
| build/agent16/pack/DUMP-TARGETS-story.txt | 9C18525029FE333D |

## Verdict

SAFE-IF P1-P6. The design (A/B against the 05:45 native4bp route run, functional only) is sound. The post script is read-only and writes only a new dir under proof5. The run itself needs its own GO once the cand5 kit revision and its dryruns are rated.

## What I checked

- Baseline inputs, re-hashed by me:
  - trace F98BF46E and game.log 4A53519F match the plan;
  - game.log has `Native GPU [39129c4c059be5f0]` at 05:45:53.600;
  - targets 9C185250 match the dump rating.
- Real-data self-test BBC9E692: the post's sha line equals 6EDA1DEA. Baseline vs itself gives 40881 frames, 220710 missing draws (VS 134404 / PS 86306), 5398.8 per 1000 frames, 46 guests, 16 keys, 64 inserts. These match the plan's baseline numbers. INVALID, as expected, with no cand log.
- proof5_post.py:
  - Read-only on its inputs; Idle + low-I/O priority.
  - Refuses (exit 2) an `--out` outside build/agent16/proof5 or one that already exists, and a cand fp equal to the base fp or not 16 lowercase hex.
  - Writes one LF report. Exit 0 = PASS / PASS-WITH-CHECKS, 1 otherwise.
  - A missing cand log gives INVALID.
  - NaN rates (0 frames) fall to FAIL, because `not rc < rb` is true for NaN.
  - STABLE targets are compared by guest address. Those addresses are guest-image addresses, so they don't depend on the host exe.
- Coarse keying: in the baseline, VS key C77B3ABB6F87ACD9 holds 19 guests, including 4 STABLE targets, and PS C77B3ABB6F87ACD9 holds 13. The plan's NOTE correctly limits the headline to the rate, the STABLE table and the guest lists.
- Safety (§5): writes stay in M3's run/trace/copy dirs and proof5/post-<stamp>. Pins, LATEST files, native4bp-bin and nativefinal2-bin are untouched. None of my D1 strings appear.

## Conditions

- P1 (order): first my rating of M3's cand5 kit revision; then install, pins, tamper and dryruns, which get their own rating; then a GO for the run. The dryrun copies and hashes about 365 MB, so it runs in a slot of its own.
- P2 (run shape): `RUN-GAMEPLAY.cmd nativeonly cand5` only.
  - **No `zone`.** The zone ctl changes scene progression, so the route would no longer be comparable with 054546, where pad 3 timed out and pad 2 was still open at the stop.
  - No dump. No ctl. X1: hands off.
  - `--led-shots` is passive and doesn't affect draws; it is allowed.
- P3 (preflight, §5): no legodimensions process; the s5wait status ends in END; no HOLD file; native5pack_check RESULT PASS (A357A041). The cand kit pins MANIFEST 787CD694, and its copy dir `bin-native5` must match that MANIFEST.
- P4 (post timing): run proof5_post only after the waiter END and after M3's G5 post for the run. Use the exact command in §3 with a fresh `post-<stamp>`, and `--base-log` passed. Report the report sha, the RESULT line, both totals lines, the STABLE table and the REMAIN/NEW guest lists.
- P5 (interpretation): the RESULT counts only if M3's post shows the same route outcome as 054546:
  - gate HIT; prompts 3/3; 302/302 steps; stop at L310; all exits 0; the zone step running out its hints with no ctl;
  - frames within ±10% of 40881.
  Otherwise the proof is inconclusive, whatever the RESULT says. This is functional only: the first boot is cold (new fp), so no timing claims.
- P6 (no promotion): even a PASS does not promote native5pack-bin (N4). Promotion needs its own package and rating. Re-rate if PLAN, the post script or the bin changes.

## Findings

- SHOULD P-S1: a bare "rate lower" threshold is weak with one baseline and no run-to-run variance. Either print a frames-ratio line plus a route-completion line in the report, or rely on P5. P5 holds in either case.
- NIT P-N1: `--base-log` is optional in the script, and without it the base fingerprint is "not checked" but not INVALID. Make it required, or treat a missing base log like a missing cand log.
- NIT P-N2: a guest that is prefix-keyed in one run and @-keyed in the other (no insert event) shows up as FIXED under one key and NEW under the other. Mark @-keyed NEW entries as "possibly REMAIN" in the report.
- NIT P-N3: "about 2 s each" for streaming a 268 MB trace in Python is optimistic. It doesn't matter, since this runs after the run.
