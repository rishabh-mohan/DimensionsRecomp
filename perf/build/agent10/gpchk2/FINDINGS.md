# E10.2: M3 prompt_sidecar + EXPLORE2 delta, static review (2026-11-25 21:20-21:30)

The kit is in `build\agent3\gameplay\` itself. There is no `kit\` subfolder.

Scratch: `pincheck.ps1` (pin re-hash), `tamper.ps1` (tamper copies, deleted afterwards), `ps1-FE06-vs-1F79.diff`.

## Hashes: all OK

| file | sha256 (first 16) |
|---|---|
| prompt_sidecar.py | 31C33A80A2DC9973 |
| selftest_prompt.py | BAA14BFC266D6502 |
| selftest\prompt-selftest.txt | A35673CC |
| toypad\fake_listener.py | 3446BA57 |
| gameplay-run.ps1 | 1F7900B9BCD7400D |
| gen_gameplay_route.py | 92629EF3 |
| explore-route.txt | D2D7D26D (236 steps, 0 tp- marks) |
| gameplay_post.py | E33DF654 |
| RUN-MANUAL.cmd | 1C3F7D85 |
| RUN-EXPLORE.cmd | E3F5890B |
| RUN-GAMEPLAY.cmd | 5F8D0192 |
| delta diff | 4C6D5A30 |

## Delta gap

- The diff (4C6D5A30) has no gameplay-run.ps1 section. It covers only gen, post, explore-route and the 3 cmds.
- M3's 21:14 backup (`kit-backup-2114\gameplay-run.ps1`) is FE060F86, not 06C4134C.
- FE060F86 vs 1F7900B9 has 2 hunks: the header comment and L50 Seconds (explore 1500).
- The prompt-sidecar wiring (06C4134C -> FE060F86) therefore has no diff. I read 1F7900B9 in full.
- Its offsets against M10's 06C4134C line refs are consistent with only additions:
  - +5 at L49-50;
  - +6 for L57-62 ($psc, $pst, $fake, $onSpecs);
  - so the lock moves L69 -> L80, the refusals L106-147 -> L117-158, and D1 L124-125 -> L135-136.

Details are in the report to M10.
