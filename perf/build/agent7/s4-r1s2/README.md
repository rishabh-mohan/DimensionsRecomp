# S4 #19: R1 stage 2, `d3d12_async_submit` (OFF by default, kInitOnly) - staging index (Agent 7)

Asked by Agent 1 (~22:29): staged diff, RATE-REQUEST.md for Agent 10, functional rows, 10-min soak plan and W7's arms.
The project pauses from Nov 23 ~13:00, so Agent 10 rates it after the break (no rating is requested before). Staging
only: no build, compile, game run or git write has been done. Base: the S4b SDK = snap1
(`build/agent2/snap1/DimensionsRecomp/rexglue-sdk/`).

| file | what | state |
|---|---|---|
| [NOTE.md](NOTE.md) | design: switch, per-file changes, threading model, queue-op table, drains, lifetimes, shutdown/failure, conditions S2-1..S2-7, log lines, risks 1-6 | done 23:20; corrected 11-23 09:04, 09:39 and 09:59 (task #33) |
| [s4-r1s2.diff](s4-r1s2.diff) | +320/-1 over 5 files (cp.cpp, cp.h, deferred_command_list.h, shared_memory.cpp, texture_cache.cpp); sha256 `06B0D371...` | done 23:10 |
| [SHA256SUMS.txt](SHA256SUMS.txt) | orig/ and new/ hashes (deferred_command_list.cpp copied for reference, unchanged) and the diff | done 23:10 |
| orig/sdk/, new/sdk/ | byte copies of the S4b files / the after files | done 23:10 |
| [make_s4r1s2.py](make_s4r1s2.py) → [PROOFS.txt](PROOFS.txt) | generator with exact-once edits E1-E16; proofs P1-P10 | ALL PASS 23:10 |
| [CHECKS.txt](CHECKS.txt) | `git apply --check`: forward on orig 0, `-R` on new 0, forward on new 1 (negative) | done 23:13; L24 warning added 11-23 09:04, scoped to snap1 09:39, tags fixed 09:59 (task #33) |
| [FUNCTIONAL-ROWS.md](FUNCTIONAL-ROWS.md) + [queue-s4r1s2.jsonl](queue-s4r1s2.jsonl) | 9 rows for Agent 3 (about 41 min), references = Agent 3's S4b rows on devoff4b-bin | first draft 23:33; row e corrected 11-23 09:04 and 09:39 (task #33) |
| [SOAK.md](SOAK.md) | 10-min soak = row e (level route, 600 s) + row j (16 KB stress); pass rules | first draft 23:35; corrected 11-23 09:04 and 09:39 (task #33) |
| [matrix-w7-draft.json](matrix-w7-draft.json) | W7: s0 / s18 / s19 (+ optional s19h at `<N/2>`) on one bin; keys checked against run-matrix.ps1 L49-55 | draft 23:29 (Agent 8 owns the final); 2 cites corrected 11-23 09:04 (task #33) |
| [RATE-REQUEST.md](RATE-REQUEST.md) | for Agent 10, b2r style: asks (a)-(c), files and apply, switch, changes, OFF = S4b, threads and ownership, failure modes, P1-P10 map, what is not proven, code reads, rows, W7 | done Nov 23 08:12 (task #32); rev 1 08:40 fixes an independent read's 3 errors, 2 gaps and 8 nits; task #33 updated its pointers (09:04) and corrected the presenter paint and cites (09:39: §6, §9, §11.1, §13; 09:59: header, §6, §15); Agent 10 rates it after the break, none requested now |

Open dependencies:
- `<N>` (the #18 split size) comes from Agent 3's `ready-N` gate (s4b10/s4b16 counters). Rows a, b and j do not need it.
- A syntax check (clang -fsyntax-only, as for s4-r1r2) is still needed once compiles are allowed.
- CHECKS.txt L22-23's apply form (`git -C <sdk root> apply`) skips all 5 files on snap1 and exits 0, because git uses
  the parent repo (CHECKS.txt L24 now says so). Copy new/sdk/ or use the `--directory` form in RATE-REQUEST.md §2.
- Rows and soak: re-check the busy and slow-state commands and the minutes; the soak's counter-line checker is not
  written yet (RATE-REQUEST.md §10, §15).
- Corrected 11-23 09:04 (task #33): the independent read's errors that also sat in FUNCTIONAL-ROWS.md (row e), SOAK.md
  (the soak bullet) and NOTE.md (the presenter paragraph, RetireOnDemandMemexport's wait, S2-2, S2-4) now match
  RATE-REQUEST.md rev 1 (§6, §9, §13; list in §15). Not owned by #33: queue-s4r1s2.jsonl row e's note still says
  "tile-mapping flushes".
- Corrected 11-23 09:39 (task #33): the task #33 read found that presenter paint runs on GPU Commands in the default
  paint mode (not only on the UI thread) and a second early return of the refresher; fixing them turned up a second
  harmless exception (a blank paint when the guest output turns inactive). RATE-REQUEST.md (§6, §9, §11.1) and NOTE.md
  are fixed, row e's query drains also cite cp.cpp:6055, and the CHECKS.txt L24 warning is scoped to snap1.
- Corrected 11-23 09:59 (task #33): the 09:39 item's attribution (above); RATE-REQUEST.md §6's paint row
  (d3d12_presenter.cpp:1173-1202) and "Presenter" cites (presenter:565-567, ui/presenter.cpp:522); NOTE.md's 09:04
  note, restored as written; CHECKS.txt L24's tags, one per time. List in RATE-REQUEST.md §15.
