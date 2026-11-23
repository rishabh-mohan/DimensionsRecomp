# S4b preflight (Agent 3 helper), 2026-11-22 20:17

Scope: read, stage and check only. Nothing was built or launched. s4b-queue.ps1, holdwatch.ps1 and postcheck.ps1 were parse-checked only, never run. Everything I wrote is under `build/agent3/s4b/preflight/`.

`build/agent3/s4b/s4b_check.py` is untouched (31770 B, 17:05:33, SHA256 starts DB473CC2ED2DF4AB). **CHK:n** = a line number in that original file.

Source abbreviations:
- The S4b staged tree is `build/agent2/s4b-check/o1-v3/src/`. Its SHA prefixes match Agent 2's snap1.
  - **CP** = `graphics/d3d12/command_processor.cpp`
  - **GSM** = `graphics/shared_memory.cpp`
  - **XM** = `system/xmemory.cpp`
  - **DCL** = `graphics/d3d12/deferred_command_list.cpp`
- **GWB** = `build/agent2/s4b-check/s4c-24-30/rexlego/src/gpu_wait_backoff.cpp`
- **PRV** = `DimensionsRecomp/rexglue-sdk/src/ui/d3d12/d3d12_provider.cpp`. This is the live file; it is not among the landed files.

## Proposed edits (not applied)

1. **s4b_check.py**: apply [s4b_check_proposed.diff](s4b_check_proposed.diff) (171 lines; [make_proposed.py](make_proposed.py) makes 16 exact-string replacements).
   - Simplest way: copy `preflight/s4b_check_proposed.py` over `s4b/s4b_check.py`, then delete its line 25: `sys.path.insert(1, ...'..', '..', 's4a')  # preflight copy only`.
   - To regenerate the copy, the diff, the synthetic runs and synth-compare.txt: `python -B build/agent3/s4b/preflight/make_proposed.py`.
2. **postcheck.ps1:50**. The verify lines are REXGPU_WARN `C1 verify K|F: ...` (GSM:733). A legitimate F line therefore shows up as logdiff NEW, which is a miss at CHK:284 and CHK:512-513. Replace
   ```
   '^s4b0[46]$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'C1 keep-watch') }
   ```
   with
   ```
   '^s4b04$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'C1 keep-watch|C1 verify') }
   '^s4b06$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'C1 keep-watch') }
   ```
   The other switch patterns don't overlap these. Row 24 has no `_verify` cvar, so its `C1 keep-watch` allow is enough.
3. **When rows 7/20/23 are added**: postcheck's default for them is `--base $b1` (scenario M) with no allow.
   - Row 7 needs `--allow-new 'C1 keep-watch|C1 verify'`.
   - Row 23 needs `'slow frame|memexport full-buffer'`.
   - All three need an L-route base, e.g. from the 19:43 route-exploration runs.
4. **QUEUE.md rows 3/8/12/17 (scenario A)**: "every step" can't hold at -Seconds 420.
   - attract-long.txt has 91 steps. RA reached 79/91; devoff3 needed 493 s for 91/91.
   - Fix one of two ways: write "≥ RA's 79/91" (the checker accepts ≥ base−2), or run those rows at -Seconds 540.

## A. Scripts

| check | result | evidence | fix |
|---|---|---|---|
| s4b-queue.ps1 parse | PASS | `Parser::ParseFile`: 0 errors, 1301 tokens | - |
| holdwatch.ps1 parse | PASS | 0 errors, 348 tokens | - |
| postcheck.ps1 parse | PASS | 0 errors, 766 tokens | - |
| s4b_check.py py_compile + --help | PASS | Python 3.11.9, rc 0. CLI: `--cand` (required), `--row`, `--base`/`--allow-new`/`--allow-gone` (repeatable), `--k-regex`, `--out-dir` (default build/agent3/s4b/checks); writes `<out-dir>/<cand>.txt/.json` | - |

## B. Dry runs: original checker in [checks/](checks), proposed copy in [checks-proposed/](checks-proposed)

| check | result | evidence | fix |
|---|---|---|---|
| a: s4b01 r7 vs R1 (a2: R1+REF) | FAIL (false LOOK) | 1 BASE miss: attract scene 790/31625 missing (CHK:496-497) | D2 |
| b: s4b03 RA vs RA | PASS | expected PROOF MISS on RA's u-diag lines (s4_upload_hash 28809, slow_frame 28704). The negative path works | - |
| b2: s4b08 RA vs RA | PASS | expected misses: no memexport suffix, NO COUNTER | - |
| c: s4b03 051201-attract-devoff3 (91/91) vs RA | FAIL (false LOOK) | 3 misses: scene 766/110956; 28 idle-* marks; GONE 2 "S# upload hash" | D1-D3 |
| d: s4b03 052901-attract-devoff3-warm | UNKNOWN | the cand is a hang/STUCK-LOCK run, so unusable | don't reuse |
| joined-log path (RA = game.3, .2, .1, game.log in that order) | PASS | checks/joined/20261122-140637-s4a-udiag-attract (16.7 MB), nothing lost | - |
| proposed copy, run a | PASS? | checks-proposed/a-s4b01-r7-vs-R1.console.txt:13,21 (790/31625 is now a note) | - |
| proposed copy, run c | PASS? | checks-proposed/c-s4b03-devoff3-vs-RA.console.txt:8,13,14,20: GONE 36 (0 unexpected); 766/110956 a note; marks first-frame..after-a2 5, 0 differ; took 29 s | - |
| proposed copy, synthetic | PASS | [synth-compare.txt](synth-compare.txt): regex unit checks + 12 runs built from the exact C++ formats; "synthetic cases with an unexpected hint: 0" | - |

## C. Proof-line regexes vs the C++ format strings

| check | result | evidence | fix |
|---|---|---|---|
| C1 init on | PASS | XM:174 `C1 keep-watch: on (with physical_protect_hold_global_lock)` | - |
| C1 init blocked (native) | PASS | XM:169 `C1 keep-watch: on, but blocked for this process (native renderer)` | - |
| C1 init no-hold (WARN) | PASS | XM:171-172 | - |
| C1 first kept | PASS | XM:784 `C1 keep-watch: first kept protect at {:08X}, {} bytes` | - |
| C1 kept so far (KEPT, CHK:29) | PASS | XM:786 `C1 keep-watch: {} protects kept so far`. Printed at the first protect, at powers of 2 below 4096, then every 4096th | - |
| C1 blocked for this process (native renderer) | PASS | XM:794-795 (once) | - |
| K = K_DEFAULT (CHK:32): the default K | FAIL | GSM:733-735 REXGPU_WARN `C1 verify {}: page {:08X} changed since its upload ({} so far){}`. The first `{}` is K or F; only K gets the suffix `; protect keeps the normal path`. Up to 256 lines are logged, then every 4096th. The old default `(?i)(keep.?watch\|verify).*(mismatch\|differ\|changed)` also counts F lines | `K_DEFAULT = r'C1 verify K: page [0-9A-F]{8} changed since its upload \((\d+) so far\)'`. postcheck passes no `--k-regex`, so this default is what s4b04's K = 0 check (CHK:271) uses |
| C1 verify armed line | FAIL (missing family) | GSM:689-691 INFO, once: `C1 verify: on. Hashing CPU uploads; K checks keep-watch protects, F checks write faults` | add families `c1_verify_on` and `c1_verify_f`. s4b04 must require c1_verify_on ≥ 1, otherwise K = 0 proves nothing |
| #18 split init | PASS | CP:1204-1205 `d3d12_submit_split_kb: splitting submissions at {} KB of deferred commands` | - |
| #18 split stats | PASS | CP:4412-4417 `d3d12_submit_split: frame={} submission={} splits={} failed={} held_query={} held_scratch={} held_pipelines={}`. Counters are cumulative; the kv parse works | - |
| #18 s4b25 with zero split lines | FAIL | the stats line prints only while a split is due, at most every 10 s. CHK:303 counts 0 lines as a miss | for s4b25, 0 lines becomes a note |
| #20 deferred_counters count | PASS | DCL:668. Printed only by the CTR bin (`#if REX_D3D12_DEFERRED_COUNTERS`, DCL:659); per-command lines at DCL:673 | - |
| #20 deferred_counters fields | FAIL | DCL:668 `deferred_counters: {:.1f} s, {} lists, {} KB, {} barriers`. Values are per interval (reset at DCL:678). kv() at CHK:135-136 returns {} | `DC_HDR` regex + `kb_per_list`. s4b09 then prints the median KB per list and half of it, which is the candidate for Agent 7's <N> |
| P2 memexport (MEMEXPORT, CHK:28) | PASS | CP:296 `" \| memexport full-buffer {}x (total {})"`. It is a suffix of the slow-frame line (CP:290-304); the total is cumulative (CP:276-278). It prints only when slow_frame_log_ms ≠ 0 (CP:264), never on the first frame, and only for frames at or above the threshold (CP:285). Row 8 sets slow_frame_log_ms=1. The same cp.cpp goes into all 4 S4b composes (rexgpu-xenos.dll). Built DLLs were not string-checked because the build is running | - |
| #24 GPU wait init | PASS (weak check) | GWB:142-144 `GPU wait back-off: {} (quantum {} us, spin {} us); stats {}; GetData hook {}.`; the WARNs at GWB:135 and :138 share the prefix | s4b18: require ON x1, `quantum 250 us`, `GetData hook built` |
| #24 GPU wait stats | FAIL | GWB:237-248 `GPU wait stats (5 s): L1 waits {} polls {} moved {} ... \| L2 sum {:.2f} ms max {:.3f} ms` has no key=value pairs and is per 5 s (counters cleared). kv() at CHK:128 returns {}, so s4b17's 4 checks (CHK:321-322) always MISS and s4b18's sleep_fail check (CHK:327) passes vacuously | `GWS` regex + 27 `GWS_KEYS` |
| s4b17 back-off check | FAIL (no-op) | CHK:323 `... or True` | make it a note line |
| d3d12_debug InfoQueue logging | UNKNOWN (not testable headless) | PRV:220-229: EnableDebugLayer, WARN at :227 if it fails. PRV:231-241: INFO `DRED (Device Removed Extended Data) enabled` at :237, only when debug is on. PRV:361-399: the InfoQueue has only a filter and break-on-severity, no log callback, so messages go to the debugger, not game.log. The d3d12_msg family (CHK:64) can never match | add a `dred` family. s4b14/15 require DRED ≥ 1 and enable-failure 0. Row 15's "no message row 14 lacks" becomes a note |
| staged sources == snap1 | PASS | CP 027204B5, DCL 30FF5744, GSM A4A31038, d3d12/shared_memory 2A5ADF13, XM BCA5E1CF, GWB 01D9F8F3, memory_watch.cpp 70829846C4F321A9 | - |

## D. Other checker issues (all fixed in the proposed diff)

| check | result | evidence | fix |
|---|---|---|---|
| D1 GONE_OK (CHK:34) | FAIL | logdiff keys print digits as '#' (`S# upload hash: frame # calls # ...`), so `S4 upload hash` never matches | `S[#\d] upload hash` |
| D2 scenes (CHK:496-497) | FAIL | attract/idle scenes after the route depend on timing (790/31625, 766/110956) | for scenario A, M or I*: missing non-FRONT_END scenes become a note |
| D3 marks (CHK:501) | FAIL | scenario A has no `up-2`, so every mark is compared, including idle-* and end | the prefix excludes idle-* and end |
| D4 s4b15 debug check (CHK:314) | FAIL (can't be tested as worded) | see d3d12_debug in section C | DRED check + note |
| D5 postcheck.ps1:50 s4b04 allow | FAIL | F lines are WARN, so they become NEW, which is a miss at CHK:284 and CHK:512-513 | edit 2 |

## E. Environment and status

| check | result | evidence | fix |
|---|---|---|---|
| d3d12SDKLayers.dll | PASS | `Test-Path C:\Windows\System32\d3d12SDKLayers.dll` = True | - |
| S4b bins | PASS | perf-notes/agent2-baseline.md:587-594: devoff4b-bin, native4b-bin, devoff4b-ctr-bin, devoff4b-cg26-bin, same as queue.jsonl | - |
| ETA | INFO | off build started 19:51:02. devoff4b ~20:25-20:30, native4b ~21:00, CTR about 10 min later, CG26 last. Agent 3's queue runs to ~22:50-23:00; RUN-NIGHT ~23:45 | - |
| new switches | INFO | all default OFF: physical_protect_keep_watch(_verify), shared_memory_upload_nontemporal_copy, d3d12_submit_split_kb, env LEGO_GPU_WAIT_BACKOFF_US / SPIN_US / STATS | - |
| Agent 2 G1-G3 | INFO | G1: hash-checked diffs. G2: the #26 tool with the option OFF regenerates the pinned set byte-identical. G3: 31 aliases (29 if built without LEGO_GPU_WAIT_HOOK_GETDATA); SESSION2 19:47 expects 31 | the proposed s4b18 check requires `GetData hook built` |
| Agent 10 | PASS | folded S4b+S4c compose PASS/SAFE (19:47). #26 is SAFE OFF; ON gives identical output and is SAFE to test (b2r row 37 §36) | - |
| Agent 12 P2 check | INFO | `python build/agent12/p2c-check/p2c_check.py <run dir \| logs oldest first> [--json OUT] [--bin PATH]` or `--selftest`. Exit 0 PASS / 1 FAIL / 3 NO DATA / 2 usage; 13/13 selftests passed at 19:42 | run it on row 8 alongside s4b_check |
| Agent 5 G4 (ready-m1, rows 19/20) | UNKNOWN | agent5-uploads.md:1023-1029 only shows `m1_copybench.exe --check-only` exiting 0 in 7.9 s; there is no explicit "G4 PASS". The W6-GATES G4 (P2 fallback never runs) is still pending | confirm with Agent 5 |
| Agent 7 <N> | UNKNOWN (not posted) | QUEUE.md:91-92: about half the median KB per list from row 9; 64 if row 9 can't run; stress value 16 | the proposed s4b09 note prints the median and half of it |
| scenario A length | NOTE | attract-long.txt has 91 steps. RA got 79/91 in 420 s; devoff3 needed 493 s for 91/91. The checker accepts ≥ base−2. RA is uncapped and has u-diag cvars, so it is not a clean base | edit 4. Rows 8/12/17 switch to s4b03 as their base once it has run (postcheck's `B 's4b03' $RA` already does this) |

## F. Queue diff ([queue-diff.txt](queue-diff.txt): queue.jsonl vs build/agent7/s4b-queue/QUEUE.md + queue-s4b.jsonl)

- **Matches:** both have the same 22 ids. After substituting <S4B-OFF>/<S4B-NAT>/<S4B-CTR>/<S4B-CG26>, args and est are identical, and bins, cvars and scenarios match the QUEUE.md table.
- **Only `needs` differs.** A7 stores it as a string, A3 as a list. A3 adds:
  - `ready-s4b-off`: s4b10, 12, 13, 25
  - `ready-s4b-off` + `ready-dbg`: s4b15
  - `ready-dbg`: s4b14
  - `ready-s4b-ctr`: s4b16
  - `ready-m1`: s4b19
- **Not in queue.jsonl** (all rows run on devoff4b):

| row | cvars | scenario | user |
|---|---|---|---|
| 7 | physical_protect_hold_global_lock=true;physical_protect_keep_watch=true;physical_protect_keep_watch_verify=true | L (~600 s) | yes |
| 20 | shared_memory_upload_nontemporal_copy=true | L | yes |
| 23 | shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true;slow_frame_log_ms=1 | L | yes |
| 26 (optional; only after rows 4-24 pass) | row 24's cvars + d3d12_submit_split_kb=<N>;shared_memory_upload_nontemporal_copy=true, plus -Env LEGO_GPU_WAIT_BACKOFF_US=250 | M (265) | no |

queue_diff.py can't parse row 26's "row 24's cvars + ..." text, so it is described by hand above.

## G. Side effects outside preflight/

- `build/agent3/s4b/__pycache__/` was created by py_compile.
- `build/agent3/s4a/__pycache__/s4a_check*.pyc` may have been written by my first `--help` run, before I switched to `python -B`.
- Both are harmless; delete them if unwanted.

## Files in preflight/

- make_proposed.py, s4b_check_proposed.py, s4b_check_proposed.diff
- synth-compare.txt, synth/, synth-out/
- checks/ (original dry runs + joined/)
- checks-proposed/
- queue_diff.py, queue-diff.txt
