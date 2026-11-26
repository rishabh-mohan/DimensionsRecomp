# Rating: M16 dump_post_story.py + DUMP-TARGETS-story.txt (combined-session post); B0#3 P1 scan

M10, 2026-11-26 05:02. Static review. I also ran a refusal test on a copy in my own scratch, with no game and no inputs.

## Files

| file | sha256/16 | role |
|---|---|---|
| build/agent16/dump/dump_post_story.py | D0CBA7CCA4399D8B | new post script, 175 lines |
| build/agent16/pack/DUMP-TARGETS-story.txt | 9C18525029FE333D | post-check list: 124 rows (16 STABLE, 108 HEAP) |
| build/agent16/dump/selftest-story/report.txt | A2C7244BF6513B90 | M16 selftest |
| build/agent2/snap1/DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp | - | event and file-name formats (L192-201, L583-585, L771-772) |
| build/agent2/snap1/DimensionsRecomp/rexlego/src/gpu_native/draw.cpp | - | draw_missing_* events (L2719/L2723) |

Base: s5/story-dump-plan-rating.md 65431D30 (D5/D6); s5/m3-zone-ctl-dump-rating.md C78F02DE (C9); s5/m3-next-session-package-check.md 980A1325.

## Verdict

**SAFE-IF E1-E3** for dump_post_story.py as the C9/D6 post for the combined session.
- DUMP-TARGETS-story.txt: **CONFIRMED** as packet item 2.
- B0#3 (D5/P1): **accepted on M16's report** (FOUND = YES ×2, bin-native MANIFEST C5181520 = native4bp, exe FA761654). p1-scan.txt is not under build/agent16/scratch, so I did not re-read it.

## What I checked

- **Writes:**
  - Only `--out` (plus its parent dir) and `--stage`. Both must be under the script dir (build/agent16/dump), checked with normcase(abspath) and a separator suffix.
  - Run, dumps, trace and targets are opened read-only. Nothing is deleted, nothing goes to the network, and nothing is launched.
  - The process sets background priority.
- **Refusal (my test, copy in scratch):**
  - `--out` outside: exit 2.
  - `--out` using `..` traversal: exit 2.
  - `--stage` outside: exit 2.
  - No file or dir was created in any case.
- **Format match against source and a real trace** (agent16 attract trace 20261125-172422):
  - identity = `stage= 6|7 guest= <dec> … container_hash= <dec>`;
  - ShaderStage kVertex=6 / kPixel=7 matches STAGE;
  - unrecognized = `guest= stage=`;
  - draw_missing_vertex/pixel carry only `guest_vs=` / `guest_ps=`, so GRE takes the right field;
  - file names `{vs,ps}-%016llX.bin` match the lost-file check.
- **Target list:**
  - 124 rows; hex = dec on all rows; no duplicate (stage, guest);
  - holds VS AC44BC64, the 5 portal guests (VS A7FA6E00/A7FA8990, PS A7FA6C00/A7FA8750/A8302100), PS AC53D0AC/AC49B8F8, and PS A81E1C30/A81E6820.
- **Dump-mode line:**
  - The script needs `shader miss cache OFF` together with `LEGO_DUMP_MISSING_SHADERS` on one line.
  - The nf2 attract run logs exactly that (game.log L122). native4bp logs `shader miss cache ON (build default)` when dump is off (041246 L122).
  - The dump-on string in native4bp is not in the snap1 source I have. If the wording differs, the script reports CHECK, which fails closed, so this is not a blocker.
- **Selftest A2C7244B:** fingerprint, dump line, identity, lost-file, DUMPED / MISSING-NO-IDENTITY / NOT-SEEN and stage paths all fired.

## Conditions

- **E1 (when it runs):** only after the session has ended: game exited, waiter END, and the hold file gone. Use one fresh `<stamp>` for `--out` and `--stage`; never reuse a stage dir, because SHA256SUMS.txt is overwritten.
- **E2 (read the result, not just the RESULT line):** RESULT says USABLE even when there are lost files or the 256 cap was hit. The selftest shows "lost: 1" with USABLE. The post must quote:
  - `identity events …`, the cap WARNING if present, and `identity events without a placement-containers file: N`;
  - the dump-mode line status;
  - N > 0 lost or the cap reached = capture **incomplete** (D6).
- **E3 (HEAP rows):** 108 rows are per-run heap addresses, and the script matches only by (stage, guest), not by hash as the list header suggests. HEAP NOT-SEEN is not evidence of anything. The C9 hit list therefore reports:
  - STABLE rows by result;
  - the portal guests by result, as heap rows, informational only;
  - the count from the "identity events for guests NOT in the target list" section.

## Findings

- **SHOULD:** add lost > 0 and n_id ≥ 256 to `bad`, so that RESULT can't say USABLE for an incomplete capture. Until then, E2 covers it. Changing the script means a new sha and a re-rating.
- **NIT:** the list header says HEAP rows are matched by physical/container hash. The script doesn't do that. Fix the header or the script.
- **NIT:** the report prints `--targets` as given. Pass a WS-relative path if the report is ever posted.
- **NIT:** p1-scan.txt: please give the actual path (it is not at build/agent16/scratch/p1-scan.txt).
