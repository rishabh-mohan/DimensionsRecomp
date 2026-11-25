# LAUNCH-R19.md: #19 functional chain on M3's queue (M7, 2026-11-25 ~06:50)

For M3. Rows: [queue-r19-live.jsonl](queue-r19-live.jsonl), 16 lines in M3's live format (pure JSON lines, same keys as
`queue-postwin-live.jsonl`, plus `unless`, which `s4b-queue.ps1` L133-135 already supports). Rules:
`build/agent10/session3/r19-rows-mp-rating.md` (F8ECBC2E) C1-C4. Row detail: `../ROWS-R19.md` (still valid, except
that the bin is no longer a placeholder, N = 4 and there are two 16 KB substitutes). All commands run from WS at Below
Normal.

## 1. Before the append (M3, ~2 min, any time before 07:35)

1. `python -B build\agent7\session3\r19prep\r19_path.py bin`: this must print `READY-R19 OK` (MANIFEST 1EBF1163,
   rexgpu 5DCDD8CB with the 3 #19 needles, devoff4b-bin E3CB99CF without them; checked at 06:49). Then write
   `build\agent3\s4b\ready-r19`.
2. `type build\agent3\s4b\ready-N` must print `4` (it has since 03:09). `<N>` stays a placeholder in the args; the
   queue fills it in from ready-N (r19-rating (b) 6).
3. `python -B build\agent7\session3\check_queue_r19.py build\agent7\session3\r19prep\queue-r19-live.jsonl --expect-n 4`
   must print ALL CHECKS PASS (226).
4. Append only after the post-window rows are done (or dropped). The 5 ref rows can launch as soon as they are
   appended (ready-s4b-off, ready-N and go-quiet all exist), so an early append would slot them into the #33 marker gaps.
   Back up `queue.jsonl` first.

## 2. Markers (M3 writes every one by hand, each only on its rule)

| marker (`build\agent3\...`) | written when |
|---|---|
| `s4b\ready-r19` | step 1.1 prints READY-R19 OK |
| `session3\r19-pathN` / `session3\r19-path16` | **after r19r10**: `r19_path.py path` on r19r10's r19_gate json (section 4). Write exactly one of them. If both exist, every path row is dropped and the chain stops, which is the safe way to fail. STOP: write neither and report |
| `session3\go-r19on` | the Overseer's RUN GO for ON rows. Only after `r19-ok-i`. Ask the Overseer to pre-authorize it so it costs no wait |
| `session3\r19-ok-<slot>` | the row of that slot is PASS (section 3). Slots are M10's a, b, i, c, g, j, d, f, e. **i16 PASS writes `r19-ok-i`** and **g16 PASS writes `r19-ok-g`**. Put the row id in the file text |
| `session3\r19-ok-c`, `r19-ok-f` as `held no-op (C2, path16)` | path 16 only: write r19-ok-c right after r19-ok-i, and r19-ok-f right after r19-ok-d. The rows c and f are dropped by their `unless` |
| `session3\r19-ok-d` as `no-op (N=4)` | only if M10 C1 holds: `r19_path.py noop` prints NO-OP OK, and s4b_check is clean. This is not expected: s4bN4 split on the title |

**Stop at the first FAIL:** each #19 row needs the previous slot's ok marker, so the queue enforces it.
- After any FAIL, INCOMPLETE (other than the C1/C2 shapes above), FLAG, hang, timeout or crash: write no marker and
  report to the Overseer. Later rows just wait; the queue passes over them.
- **Row e INCOMPLETE ends the chain** (C3).
- W7 needs j and e PASS with real splits (`chunks > 0` in the last async line). No-op rows don't count.

## 3. Order, proofs and gates

`<run>` is the row's run dir from `queue-state.jsonl`. Every gate also writes
`--json build\agent3\s4b\r19\checks\<id>.r19.json` (r19_gate now creates the folder). s4b_check always gets
`--out-dir build\agent3\s4b\r19\checks`. PASS means s4b_check has no FAIL, r19_gate exits 0, and the run is valid
(ON rows: `bench/agent11/timerq_slowstate.ps1`, ROWS-R19 section 2, run 3).
B19 = `build\agent2\devoff4b-r19-bin`, B4 = `build\agent2\devoff4b-bin`.
Bases: s4b01 = `20261122-205356-s4b-01-off`, s4bL0 = `20261122-210059-s4b-L0-off-level`,
s4bN16 = `20261125-014239-s4b-N16-title-split16`, and r19rXX = that ref's run.

| # | id | proves | s4b_check `--row` / `--base` / `--allow-new` | r19_gate | on PASS | real min |
|---|---|---|---|---|---|---|
| 1 | r19r11 | base for j and i16: OFF #18 at 16 KB on devoff4b | s4b11 / s4b01 / `d3d12_submit_split` | `--row i --n 16 --bin B4` | (none) | 4.0 |
| 2 | r19r10 | base for i and c; **path decision** | s4b10 / s4b01 / `d3d12_submit_split` | `--row i --n 4 --bin B4`, then `r19_path.py path` | pathN or path16 | 4.0 |
| 3 | r19r13 | base for f | s4b13 / s4b01 / `d3d12_submit_split` | `--row i --n 4 --bin B4` (info) | (none) | 4.0 |
| 4 | r19r15 | base for g and g16 (debug layer) | s4b15 / s4b01 / `d3d12_submit_split` | `--row i --n 4 --bin B4` (info) | (none) | 4.0 |
| 5 | r19r25 | base for d (title, uncapped) | s4b25 / s4bN16 / (none; N2: the init key may show) | `--row i --n 4 --bin B4` (info) | (none) | 3.1 |
| 6 | r19a | #19 bin, everything off: identical to s4b01. **Bin identity** | (none) / s4b01 / (none) | `--row a --bin B19` | r19-ok-a | 4.0 |
| 7 | r19b | async without split stays off: exactly 1 WARN | (none) / s4b01 / `d3d12_async_submit: needs` | `--row b --bin B19` | r19-ok-b | 1.6 |
| 8 | r19i | path N: OFF split at 4 KB on the #19 bin | s4b10 / r19r10 / (none) | `--row i --n 4 --bin B19` | r19-ok-i | 4.0 |
| 8' | r19i16 | path 16: the same at 16 KB (C2) | s4b11 / r19r11 / (none) | `--row i --n 16 --bin B19` | r19-ok-i | 4.0 |
| 9 | r19c | path N: first ON row, async + split 4 | s4b10 / r19r10 / `d3d12_async_submit: ` | `--row c --n 4 --bin B19` | r19-ok-c | 4.0 |
| 10 | r19g | path N: ON under the debug layer (S1: before j/d/f/e) | s4b15 / r19r15 / `d3d12_async_submit: ` | `--row g --n 4 --bin B19` | r19-ok-g | 4.0 |
| 10' | r19g16 | path 16: the same at 16 KB (C2) | s4b15 / r19r15 / `d3d12_(async_submit\|submit_split)` | `--row j --n 16 --j1-info --bin B19` | r19-ok-g | 4.0 |
| 11 | r19j | stress at 16 KB: FIFO fills, queued_max ≤ 3 | s4b11 / r19r11 / `d3d12_async_submit: ` | `--row j --n 16 --bin B19` | r19-ok-j | 4.0 |
| 12 | r19d | W7 s19 arm, functional: real splits on the title | s4b25 / r19r25 / `d3d12_async_submit: ` | `--row d --n 4 --bin B19` | r19-ok-d | 3.1 |
| 13 | r19f | path N: memexport readback drain with async | s4b13 / r19r13 / `d3d12_async_submit: ` | `--row f --n 4 --bin B19` | r19-ok-f | 4.0 |
| 14 | r19e | 10-min level soak: queries held, clean close | (none) / s4bL0 / `d3d12_(async_submit\|submit_split)` | `--row e --n 4 --bin B19` | r19-ok-e (end) | 7-10 |

- Rows 8 and 8' are alternatives, and so are 10 and 10'. The `unless` drops the unused one.
- Ref rows: the r19_gate `--bin B4` check is the N1 bin proof for refs. The r19_gate verdict of refs 3-5 is info only;
  their gate is s4b_check. Ref 1 should PASS: it is the early 16 KB split evidence j needs.
- Row j full_waits = 0 gives INCOMPLETE: stop, the Overseer decides (ROWS-R19 section 2).
- Every hang or timeout is a FAIL. Triage starts from the GPU Commands / D3D12 Submit stacks.
- **S1 (M10 r19prep-rating):** no ON use (W7 included) may set `d3d12_readback_memexport=true` until row f has
  PASSed with real splits (`chunks > 0`). On path 16, f is a held no-op, so this restriction stays in force after the
  chain ends.

## 4. The two decisions by machine

```
python -B build\agent7\session3\r19_gate.py build\agent3\runs\<r19r10 run> --row i --n 4 --bin build\agent2\devoff4b-bin --json build\agent3\s4b\r19\checks\r19r10.r19.json
python -B build\agent7\session3\r19prep\r19_path.py path build\agent3\s4b\r19\checks\r19r10.r19.json
python -B build\agent7\session3\r19prep\r19_path.py noop build\agent3\s4b\r19\checks\r19d.r19.json build\agent3\runs\<r19r25 run>
```
Exit 0 = write the printed marker. Exit 1 = STOP. Offline controls (06:48): s4bN4 → `r19-pathN`, s4bN16 at 16 →
`r19-path16`, real s4bN16 as row d → STOP, s4bN16 plus 1 synthetic async-init line → `NO-OP OK` (= M10 check 3).

## 5. Duration (real row times from queue-state.jsonl: menus 420 s ≈ 220-270 s, title 180 s ≈ 185 s, level 600 s ≈ 400-610 s, launch gap ≈ 11 s)

| part | path N (expected) | path 16 |
|---|---|---|
| 5 refs | 19 min | 19 min |
| #19 rows | 38 min (a b i c g j d f e) | 30 min (a b i16 g16 j d e) |
| gaps between launches | 3 min | 3 min |
| M3 gate and marker wait, ~2 min × 8 chained rows | 16 min | 12 min |
| **total** | **~76 min** (best case ~60 min with instant markers) | **~64 min** |

From ~07:35, path N ends at ~08:50. Add any wait for go-r19on if it isn't pre-authorized. A FAIL stops the chain
earlier.
