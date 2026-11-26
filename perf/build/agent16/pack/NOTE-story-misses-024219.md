# Story-route shader misses on native4bp (M3 RUN-MANUAL 20261126-024219), static analysis

M16, 2026-11-26 ~03:15 local. This is a read-only analysis. The source is the post `build\agent3\gameplay\post\gameplay-manual-20261126-024219.txt` (786379D9). The data comes from the run `runs\20261126-024219-gpman-native` and the trace `trace-native-20261126-024214\events.tsv`, which is 314 MB; the trace started at 02:42:23.449. The scripts are in M16 scratch: `miss_story.py` and `miss_story2.py`.

## Bin

M3's bin is native4bp itself, not just a nativefinal2-style build: the run dir MANIFEST.txt sha256 = C5181520…A690, and the exe is FA761654. So the 83-container placement pack was present.

## The two hashes the Overseer named

| guest (dec) | hex | stage | container | events | frames | first seen | note |
|---|---|---|---|---|---|---|---|
| 2890185828 | 0xAC44BC64 | VS | placement, backing 0xED23CE20, span 16, prefix 5BB4C8029EB256F2 | 51832 | 7718 | t 205.0 s (02:45:48, menus) | this is the existing candidate, `CANDIDATE-VS-AC44BC64.md`; the prefix has 0 index rows |
| 2820545584 | 0xA81E1C30 | PS | full container, physical 0xED61EAC0, span 2024, prefix C77B3ABB6F87ACD9 | 25882 | 1128 | t 768.6 s (~02:55:12, story) | new; always paired with PS 0xA81E6820 (same 1128 frames, same first frame); 0 frames shared with the VS candidate |

## Two phases

- **Menus**, t 205-624 s: only VS 0xAC44BC64. This is the same pattern as M3's 20261125-195926 run.
- **Story**, from t 588.7 s, which is 02:52:12.1:
  - It matches the post's front-end state `0@02:52:12.0` (the story load).
  - From there, 34 unique shaders enter the miss cache, and 46 guests have draw misses.
  - 19 of those guests (28,063 events) have no insert event of their own. They are probably deduplicated by physical address; this is not resolved.
- **Share of the 194,277 events:**
  - the VS candidate: 51,832 (26.7%);
  - story content: 142,445 (73.3%).

## Prefix C77B3ABB6F87ACD9 is a generic header, not an identity

- 29 of the 34 story inserts carry prefix C77B3ABB6F87ACD9:
  - 18 PS guests (span 2024), 52,479 events;
  - 11 VS guests (span 1900), 53,153 events.
- The merged index (`pack\run-20261125-173813\lego-microcode-index.cpp`) already has 7,911 C77B3ABB rows out of 19,267, 66 of them added by the pack. A row is (prefix, hash, hash, size, …).
- So the story shaders are new content behind a common header. The pack only covers what the attract and menu routes drew.
- Other new containers:

| shader | type | span | prefix | index rows | draw-miss events |
|---|---|---|---|---|---|
| PS 0xAC49B8F8 | placement | 16 | E5F38732B2606C55 | 0 | 8,049 |
| VS 0xAC471F18 | container | 384 | 98D43959C65B882A | 24 | 701 |
| PS 0xAC5AB10C | container | 180 | 9C456B3426F7D1E5 | 2 | 0 |
| PS 0xA7B649D0 | container | 1540 | 951B26B697EDCC20 | 2 | 0 |

- Top draw-miss guests with no insert event:

| guest | events | frames | first seen |
|---|---|---|---|
| VS 0xA7B657D0 | 13,942 | 225 | t 891.9 s |
| VS 0xA7B9AA50 | 3,282 | — | — |
| VS 0xA7B62220 | 1,641 | — | — |
| VS 0xA7B56C00 | 1,116 | — | — |
| PS 0xA777E1F0 | 2,751 | — | — |
| PS 0xA7906070 | 1,432 | — | — |

## What this means for the pack decision

- **A fix for AC44BC64 alone** clears the menus, which is 27% of the events. It does nothing for story content.
- **Story content needs a dump pass on M3's story route** (the 0.4a flow over all misses): at least 34 containers, including a second placement shader, PS 0xAC49B8F8. The 19 guests with no insert also need checking.
- **Recommendation: don't repin twice.** Fold AC44BC64 into a single gameplay pack rebuild after a story-route dump. That gives one MANIFEST change and one repin plus M10 re-rate of every kit that pins C5181520: natcmp, rows/ab, the window script and RUN-DTIME.
- **No effect on timing results:** the window and attract-long routes draw none of these, with 0 `missing from AOT index` lines in the n4bp60 logs. The misses only matter for gameplay correctness (missing draws).
