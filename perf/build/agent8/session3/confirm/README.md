# Confirmation windows CF1 / CF2 (M8, session 3) — draft, NOT installed

Per the Overseer's 07:46 brief: the shipped combo on devfinal vs s0 on devoff4b, and nativefinal (N-A) vs native4b mc on the W8a route. Both use the same structure as WC1/W8a, and every new-bin arm follows BIN-PINS D7 (FE4CD4FF).

| file | sha256 |
|---|---|
| matrix-windowCF1.json (Xenos) | D36A40CA5277CC7C3E127E10D5367DD892E43160D7AA834D04E2A936EE63D44F |
| matrix-windowCF2.json (native) | DF8A2D3B7D0ACA1428F3B41AC2F5E587741BA8D1C5D390CD68C3646900AE0F60 |
| stage-confirm.ps1 (stage-window.ps1 + `-Launcher`, default `bench\agent5\day\run-day.ps1`; TEST/RECHECK only) | 448D6FAD5B1B486B03F5B733ED361EE38D73728CDCC802A7B076D86C94F38D5D |
| make-stage-confirm.ps1 (builds stage-confirm.ps1 from stage-window.ps1 by 8 exact, single-hit replacements) | - |

## GO lines (checked by run-day.ps1 B67EBD6C's own Parse-Go / Test-Matrix / Get-BinHashes / Get-Plan)

| id | GO | runs | runner est. | stage report |
|---|---|---|---|---|
| CF1 primary | `GO CF1 matrix-windowCF1.json D36A40CA5277CC7C3E127E10D5367DD892E43160D7AA834D04E2A936EE63D44F only=ship,s0 repeats=6` | 1 cold + 12 | ~30 min | stage/stage-CF1-075114.txt (-VerifyFiles) |
| CF2 primary | `GO CF2 matrix-windowCF2.json DF8A2D3B7D0ACA1428F3B41AC2F5E587741BA8D1C5D390CD68C3646900AE0F60 only=nf,mc repeats=6` | 1 cold + 12 | ~30 min | stage/stage-CF2-075130.txt (-VerifyFiles) |
| CF1 alt (WC1 shape + anchors) | `... only=ship,s0,win3,dfoff repeats=4` | 1 cold + 16 | ~39 min | stage/stage-CF1-075138.txt |
| CF2 alt (+ W8a's n0) | `... only=nf,mc,n0 repeats=6` | 1 cold + 18 | ~44 min | stage/stage-CF2-075134.txt |

Primary pair: about 60 min of runner time, plus the gap between the two GOs. All four checks gave result OK, and the matrix folder count was 33 / 33 before and after -PlanOnly. The -PlanOnly runs started while M3's queue was idle (it was waiting for f10aL and f10bL).

## Design

- **Default arm (D7):**
  - CF1: `ship` = devfinal, cvars `framerate_limit=0` only, env {}.
  - CF2: `nf` = nativefinal, W8a's cvars plus `LEGO_NATIVE_FRAME_METRICS` only.
- **References:**
  - CF1: `s0` = devoff4b, framerate_limit=0, env {}. This is WC's s0; old bins keep env {}.
  - CF2: `mc` = native4b with `LEGO_NATIVE_SHADER_MISS_CACHE=1`, which is W8a's mc as timed.
- **Optional arms (only with the alt GO):**
  - CF1 `win3`: WC's arm exactly.
  - CF1 `dfoff`: devfinal with the D7 OFF set, i.e. the 12 old values plus `LEGO_GPU_WAIT_BACKOFF_US=off`.
  - CF2 `n0`: W8a's n0.
- **Cold run / caches:**
  - The new-bin arm is first in file order. The launcher's -ColdShared then puts the single unscored cold run on the new bin: devfinal for CF1, nativefinal for CF2. The -PlanOnly output confirms this.
  - nativefinal's new fingerprint makes its first launch cold in any case.
  - The old bins keep their own warm caches. Nothing copies or seeds a cache.
- **Warm-up policy:** the read-out drops round 1 of every arm as GPU warm-up, the same as the WC1-3 read-out that M10 confirmed. It scores rounds 2-6 (5 per arm) and gives every verdict with and without round 1. The read-out also checks gpu.csv for the ~1500 MHz plateau at round 2.
- **Proof per run:** run.json `env_set` + the bin's MANIFEST sha + `final\check-defaults.py --mode`:

  | arm | mode / proof |
  |---|---|
  | ship | xenos |
  | dfoff | off |
  | win3 | legacy |
  | nf | native-old |
  | mc, n0 | env_set only |
  | s0 | no proof lines at all |

  On top of that, every run gets the normal functional check, and STUCK-LOCK is judged by the finding-10 rule per arm.
- **Read-out metrics:** fps mean, p99, the 1 % low and cores, not median ms (READOUT-NIGHT S1). Every row has a bootstrap CI. Runs flagged by the M12 non-game-load gate are reported both with and without them. All sys.csv rows have 31 columns; never pool them with the 24-column rows.

## Not done / for the Overseer

- Nothing has been copied to bench\agent8\run. The test copies are under `confirm/test/CF1` and `confirm/test/CF2`. Promoting them means a byte copy to `bench\agent8\run\` plus `stage-confirm.ps1 -Recheck`, which is the Overseer's call.
- The "latest start" line in the stage reports uses the night rule (07:30). The day launcher instead refuses a GO when now + estimate + 10 min passes its `-StopAt`.
