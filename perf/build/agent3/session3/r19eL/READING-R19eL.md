# r19eL: reading steps (draft, NOT installed)

Spec: M10 `build/agent10/session3/r19prep-rating.md` (F426CEA0, 09:14 addendum, "Follow-up row r19eL").
Order: after the #19 chain and the #33 rows, only on the Overseer's order (the order creates `build\agent3\session3\go-r19eL`).

## Install (on order)
1. Check the pins: `build\agent2\devoff4b-r19-bin` (READY-R19 OK via `r19_path.py bin`), route `build\agent3\toypad\routes\level-l.txt` = 6F9E6009, ready-N present.
2. Back up queue.jsonl as `queue.jsonl.bak-r19eL`. Append the one line from `queue-r19eL.jsonl`. Parse-check every line of the live queue with `python -c "import json,sys;[json.loads(l) for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]" build\agent3\s4b\queue.jsonl`.
3. Create `go-r19eL`, with the Overseer's order quoted in its text.
4. Optional ref (M10: for s4b_check NEW/MORE): the same row with `devoff4b-bin` and without `d3d12_async_submit=true`. Leave it out unless the Overseer asks for it.

## PASS conditions (all required; any miss = HOLD for the Overseer, hang = FAIL)
| # | check | how |
|---|---|---|
| C1 | clean run: exit 0, no WER, dialogs or dumps; wm_close and "Title terminated" once each; steps 119/119; stopped_by_script | the queue DONE line, plus run.json (`steps_done`, `steps_total`, `stopped_by`), plus `Select-String game*.log 'Title terminated'` (count 1) |
| C2 | timeouts only on the level-l by-design wait lines (final_gate v3 map, ≤ 31); 0 of final_gate's 10 bad strings; no hang | `final_gate` (73F946E7) on the run dir with the fx7 args. The 590 s elapsed floor is miscalibrated; ruling-fx2.md covers an elapsed-only miss on a complete route |
| C3 | `r19_gate --row e --n <N> --bin build\agent2\devoff4b-r19-bin` PASS on the joined, rotated logs | `python -B build\agent7\session3\r19_gate.py <run dir> --row e --n <N> --bin ... --json build\agent3\s4b\r19\checks\r19eL.r19.json`. Pass the **run dir**, not game.log: r19_gate (CA5C036C) then reads game.log plus the rotated game.N.log (`sc.log_files`) |
| C4 | the run-dir toml has `d3d12_readback_memexport = true` and `readback_memexport_fast/batched/on_demand = false` | `Select-String <run>\legodimensions.toml 'readback_memexport'`; run.json cvars include `d3d12_readback_memexport=true` |
| C5 | summed `memexport syncs` > 0 and KB > 0 over all slow-frame lines | `python build\agent3\session3\r19eL\memexport_sum.py <run dir>`: exit 0 = met; exit 3 = zero → **HOLD, ask, do not PASS**; exit 2 = no slow-frame lines → HOLD |
| C6 | `memexport full-buffer` is **not** a criterion | ignore it (it reads 0x in every line of the f10 runs) |

Coverage note: slow_frame_log_ms=1 also turns on the NoteMemexportRange bookkeeping, so the timing in this run is meaningless (functional only). PASS lifts S1' (async + memexport readback directly covered).

## Report (to the Overseer, verbatim for M12)
--bin path (WS-relative), run dir, .r19.json path, C1-C6 one line each with numbers, the memexport_sum summary line, and the result (PASS / HOLD / FAIL).

## Tool check
`memexport_sum.py` on f10a3 (`20261125-023326-f10a3-m1-sfl-level`, rotated logs) gives 18249 slow-frame lines, 3987 frames > 0, sum 29070, 1020444 KB, exit 0. That matches M10's table (3987 frames). On r19r25 (no slow_frame_log_ms) it gives 0 lines, exit 2.
