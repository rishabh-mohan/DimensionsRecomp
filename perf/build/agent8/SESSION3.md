# M8 session 3 (S3T-8) log

## Windows staged 2026-11-25 01:43-01:46 (stage-window.ps1 -Promote -VerifyFiles, all OK, PlanOnly started nothing: matrix folders 28/28)

| Window | file in bench/agent8/run | sha256 | runs / runner est. | arms (file order) |
|---|---|---|---|---|
| WC1 | matrix-windowC.json | 00E3EE97A18A3B31944D8E2BB1D67273D8282D8D48D3524A5B1803AF8F5F1896 | 17 / 39 min | s0, win3, c1np, p2fc (devoff4b-bin) |
| W8a | matrix-window8a.json (unchanged) | A06E5E3AAEE25B079532DE8BFC9134D7462B5F842ECB9FADA19B6FD8DD8A475E | 15 / 35 min (repeats 7) | n0, mc (native4b-bin) |
| WC2 | matrix-windowC2.json | D0AE477F26E21A7A92D04E455C3D727C9AF4B3E69C75A7771B131AF6F924F3B4 | 17 / 39 min | p2fc, c1np, win3, s0 (devoff4b-bin) |
| W10 | matrix-window10.json | 289F4B4F008FA0C8D2EDD6371F9FAA28C3A40AABF554BA680042367D5A975F55 | 13 / 30 min | s0 (devoff4b-bin), cg26 (devoff4b-cg26-bin) |

GO lines:
- `GO WC1 matrix-windowC.json 00E3EE97A18A3B31944D8E2BB1D67273D8282D8D48D3524A5B1803AF8F5F1896 only=s0,win3,c1np,p2fc repeats=4`
- `GO W8a matrix-window8a.json A06E5E3AAEE25B079532DE8BFC9134D7462B5F842ECB9FADA19B6FD8DD8A475E only=n0,mc repeats=7`
- `GO WC2 matrix-windowC2.json D0AE477F26E21A7A92D04E455C3D727C9AF4B3E69C75A7771B131AF6F924F3B4 only=s0,win3,c1np,p2fc repeats=4`
- `GO W10 matrix-window10.json 289F4B4F008FA0C8D2EDD6371F9FAA28C3A40AABF554BA680042367D5A975F55 only=s0,cg26 repeats=6`

Reports: build/agent8/readout/w-followup/stage-{WC1-014309,WC2-014336,W8a-014445,W10-014619}.txt

## Decisions
- Launcher always passes `-Only -Repeats -ColdShared -NoPrompt`: -Repeats overrides per-arm repeats, so no separate warm-up arm is possible and every window has exactly 1 cold run. W10 is therefore 1 cold + 12 = 13 runs, not 2 cold + 12; cg26's first launch (round 1) is its cold run.
- GPU warm-up = round 1, discarded in the C read-out (scored rounds 2-4 = shifts 1-3, Latin rows). Pass 2 reverses file order.
- W8a repeats 7 = round 1 discard + 3/3 balanced starts; repeats 6 (13 runs, 30 min) is the file's original GO.
- Window ids start with W (pre-go.ps1 pattern `^W[0-9A-Za-z-]+$`).

## Item 4: staged runner improvements (02:08, nothing installed)

| File | sha256 prefix |
|---|---|
| `staged/run-matrix.ps1` | 72370A1E737A3A34 |
| `staged/frame_summary.py` | 987E0EC03456D5DC |
| `staged/sys_summary.py` | 6FCE3630B13134D5 |
| `staged/drivers\sys-csv.ps1` | F3F06AB013F2423E |
| `staged/drivers\LdSys.cs` | 4EFD5C91B5DF3F68 |
| `staged/RUNNER-NOTES.md` | 20E9A688CA75445B |
| `staged/SAMPLER-NOTES.md` | 16548A673E712D68 |
| `staged/run-matrix.diff` | 1038DE52317B1E58 |
| `staged/frame_summary.diff` | 2E32EDDD57EDEDD6 |
| `staged/LdSys.cs.diff` | A4890BD480CC8A2F |
| `staged/sys-csv.ps1.diff` | 4EA25AE821D2D175 |
| `staged/sys_summary.py.diff` | B930659A15AF75DD |

Tests: test/test-plan.ps1 (plan identical with warm-up 0; warm3 20 runs/46 min; validation), frame_summary on 2 real runs, E9.1 synthetic + cmp_old re-run by M8 ALL OK. Pinned originals unchanged (sys_summary C95767DE, sys-csv 017A4F3E, LdSys B452D258, run-matrix 1A522CDF, frame_summary 0A7D3587). Install notes: RUNNER-NOTES.md + SAMPLER-NOTES.md.


## Morning 2026-11-25 (07:30-07:52)

- **Runner install (C1)** at 07:30:31, after run-night exited at 07:30:25. Script: `session3/install/install.ps1`; log: `install/install-log.txt`; backup: `session3/backup/20261125-073031/`.
  - bench/agent8/run: run-matrix 1A522CDF → 72370A1E, frame_summary 0A7D3587 → 987E0EC0, sys_summary C95767DE → 6FCE3630, drivers/sys-csv 017A4F3E → F3F06AB0, drivers/LdSys B452D258 → 4EFD5C91.
  - The new runner's -PlanOnly matches the old one's for W10 and WC (`install/plan-old`, `install/plan-new`).
- **Selftest (C2):** `selftest/sys_selftest.ps1` → 5C2D2038.
  - Changes: the header is now 31 columns, and the old `$r`/`$R` clobber in check g is fixed (`$nCsv`).
  - Result: SELFTEST OK, 28 pass / 0 fail.
- **Smoke (C4/C5):** `session3/smoke/out-0734`, 4/4 runs OK. `smoke/check-out-0734.txt` shows items 3, 4, 6 and 10 PASS.
- **ProcEvery ABBA:** `smoke/ab-*`, analysed in `smoke/ab-align.txt`. P5 shows no snapshot periodicity. sys-csv.ps1 was restored afterwards and checked at F3F06AB0. The default stays 5 (Overseer accepted); re-check it at the first idle timed window.
- **Day re-pin:** `session3/day-repin/` (README 13006CF7, install-day.ps1 D2D1D11F, install-day.diff D7F81F97). The only hard pin is L43 (run-matrix).
- **run-timing stop_line fix:** `session3/run-timing-fix/`. The Overseer installed it at 07:47, so run-timing.ps1 is now 9CCE9827.
- **C3 reminder:** never pool 24-column sys.csv rows (before 07:30) with 31-column rows.
- **Confirmation windows (draft, not installed):** `session3/confirm/` (README.md).
  - CF1 = D36A40CA: ship (devfinal) vs s0.
  - CF2 = DF8A2D3B: nf (nativefinal) vs mc (native4b).
  - Each is 13 runs, ~30 min. Checked by stage-confirm.ps1 against run-day.ps1 B67EBD6C; all checks OK.
