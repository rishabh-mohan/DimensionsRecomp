# S4c package: #24 GPU-wait back-off + #30's CMake option (Agent 9, task #22, 2026-11-22)

An incremental S4c on top of Agent 2's S4b. Both items default OFF. Nothing was built to make it: only stage.py,
git apply and GNU patch on scratch copies, clang -fsyntax-only, and a map read.

## Files (full sha256 in HASHES.txt)

| File | sha256 (16) | What |
|---|---|---|
| `s4c-24-30.diff` **primary** | DC02104EA76E0BF6 | -p1 from `DimensionsRecomp/`: `rexlego/CMakeLists.txt` +22 lines (#30 block after base :155, #24 block after base :167) and the new `rexlego/src/gpu_wait_backoff.cpp` (+395). +417/-0 |
| `s4c-24-only.diff` fallback | A279DC71D6CD4FAA | the same without the #30 block (CMake +9 after base :167). +404/-0 |
| `base/rexlego/CMakeLists.txt` | 3690D5D76AA9FBED | live = snap1 (S4a) = snapB, 885 CRLF lines |
| `new/rexlego/CMakeLists.txt` | 1BF46D7878BA9A25 | primary result, 907 CRLF lines |
| `new-24only/rexlego/CMakeLists.txt` | 9A4606A7031375F7 | fallback result, 894 CRLF lines |
| `new/rexlego/src/gpu_wait_backoff.cpp` | 01D9F8F3464C8614 | = the rated draft (b2r row 33, N1-N4 fixed), 395 LF lines |
| `apply-check.txt`, `syntax-20261122-155218.txt`, `expected-map.txt` | | the three checks below |
| `stage.py` (`stage` / `verify` / `hashes`), `syntax_check_s4c.ps1`, `maplines.py` | | how they were made; stage.py is deterministic |

## Apply (Agent 2, after S4b)

1. Check that `rexlego/CMakeLists.txt` is 3690D5D7... (no S4b item touches it).
2. From `DimensionsRecomp/`: `git -c core.autocrlf=false apply -p1 --check <diff>`, then the same without
   `--check` (or GNU `patch -p1 --binary`). Undo: `git apply -R`.
   Or copy the `new/` files over and set their mtime to now: copies keep old mtimes, which the native fingerprint
   and ninja miss. git apply and patch write new mtimes anyway.
3. EOL: the CMake hunks are CRLF and the new file is LF. A git apply inside the live repo (`core.autocrlf=true`,
   `* text=auto`) writes the TU as CRLF instead (HASHES.txt "info" row). The text is the same either way.

## What each item does

- **#24**, inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)`, so Xenos (devoff) builds only. It adds the TU with a
  source-scoped `LEGO_GPU_WAIT_HOOK_GETDATA=1`, so no other TU recompiles. Hooks: H0 sub_83FBF7D0, H1 sub_83FAF180,
  H2 sub_83FB09E8, H3 sub_83FC0C10 (counts only with STATS). OFF at run time: with `LEGO_GPU_WAIT_BACKOFF_US`
  unset, every hook calls `__imp__` straight away. Switches: `LEGO_GPU_WAIT_BACKOFF_US` (Q),
  `LEGO_GPU_WAIT_SPIN_US`, `LEGO_GPU_WAIT_STATS=1`.
- **#30**, `option(LEGODIMENSIONS_SCENE_WALK_PROBE ... OFF)`. OFF adds nothing. ON stops the configure with a
  FATAL_ERROR until `src/scene_walk_probe.cpp` exists; the probe sources and the `#ifdef` lines are not drafted
  (spec: agent9-codegen.md S4.2.4). The option is not tied to NATIVE_GPU: the spec has a devoff2-probe and a
  native3d-probe, and S4-DRAFT plans native3d-probe. Probe builds are separate and never timed.

## Build effects

- Both trees re-run CMake (7-25 s each). Devoff: +1 TU (gpu_wait_backoff.cpp.obj) and a relink. Native: nothing
  new compiles.
- **Native fingerprint:** CMakeLists.txt is its first input (:582-583, which becomes :604-605 after the edit), so
  S4c changes it once, as C1 does in S4b. For a single native re-pin, run the native pin build (native5) after
  S4c, or fold this diff into S4b's apply (no file overlap with C1/M1/P2c/r1r2/#26). That is Agent 1's call
  (S4-DRAFT L100, L413).

## Map gate (Agent 2: batch-nolr build, skip_lr off; gate G3)

Today, on the devoff4 map (DCC51E2B...), there are 27 hooked aliases and all 4 targets are unhooked. The S4c devoff
bin must have exactly 4 more than the S4b devoff bin (devoff4: 27 -> **31**):

    sub_83FBF7D0 -> gpu_wait_backoff.cpp.obj   (__imp__ stays in legodimensions_recomp.248.cpp.obj)
    sub_83FAF180 -> gpu_wait_backoff.cpp.obj   (__imp__ stays in legodimensions_recomp.107.cpp.obj)
    sub_83FB09E8 -> gpu_wait_backoff.cpp.obj   (__imp__ stays in legodimensions_recomp.422.cpp.obj)
    sub_83FC0C10 -> gpu_wait_backoff.cpp.obj   (__imp__ stays in legodimensions_recomp.232.cpp.obj)

Without the define it is 29 (H0/H1 only). The other 27, and the sub_ and __imp__ name sets, don't change. Native
maps don't change. The 31-name list is in expected-map.txt.

## Before ON (b2r section 26, steps 1-4)

1. P1 controls: l1_waits, l1_polls, l2_tries and kicks all > 0.
2. A functional Q=250 vs OFF pair: logdiff NEW 0 / MORE 0 / flags 0 apart from the back-off line, same exit codes,
   no new STUCK-LOCK.
3. The sweep.
4. Agent 6's loaded arm with sleep_fail == 0, menus and attract only.

## Checks run

- `apply-check.txt` PASS for both diffs: git apply --check / apply / -R --check and GNU patch dry-run / apply, on
  scratch copies. The results match new/ by sha256 with no stray files; the CMake hunks keep CRLF and the new
  file LF.
- `syntax-20261122-155218.txt` PASS: clang 23.1.6 `-fsyntax-only` with the S4a devoff4 flags (snap1-off
  compile_commands; 1 thread, BelowNormal). The control (native_lock_elide.cpp) and the TU with and without the
  define all exit 0. The only warnings are the expected getenv deprecations (3 in the TU, 1 in the control). `-E`
  finds 4 hooks with the define and 2 without.
- `expected-map.txt` PASS: 27 hooked today, all 4 targets unhooked.
