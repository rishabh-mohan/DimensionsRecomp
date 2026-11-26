# P1: native6pack candidate pack + bin (M16, S5, PLAN-dump6 v2 §6 Step D): for M10 rating before any build

**Goal:** build a second **candidate** native bin, `build\agent16\pack\native6pack-bin`. It packs the native5pack inputs plus the NEW placement containers from dump run B, so the 6 post-zone shaders (VS A7F7A100 / AB80F350 / AB64C0E0, PS A7F79ED0 / AB77B580 / ABB3F110, key prefix 0xC77B3ABB6F87ACD9) become AOT hits.
- No promotion, no repin, no LATEST-pack.txt or LATEST-bin.txt write, no defaults change, no game launch (N4: the user's Phase 4 call).
- **Build gate:** the build waits until dump6_post (7887B90A) on dump run B says **COVERED**, or **PARTIAL with ≥ 1 new container**, and until stage6_inputs reports `RESULT PASS` with ≥ 1 NEW. If the post says NOT-COVERED, NOT-REACHED or INCONCLUSIVE, or stage6 says NOTHING-NEW, nothing below runs.
- Nothing here has been run on real inputs yet. Only the static checks and synthetic self-tests in §1.3 were done.

## 1. Scripts (all under build\agent16\pack; native5pack.py/.ps1/_check.py/.diff stay frozen and untouched, N6)

| file | sha256 | what |
|---|---|---|
| `native6pack.py` | `2B755B55E07C8C12BD3ABF54D771DB92CC6737000EF4047B8135541D8E8A4552` | native5pack.py 7DDFB8B9 plus the changes in §1.1 |
| `native6pack.ps1` | `7C97F0DE9658260DB205DEA07A065CB31E7325007BC770E3001AB326C7E29AB5` | native5pack.ps1 22245C44: names, plus N3 |
| `native6pack_check.py` | `A9D12AA1D7A37484ADF208823F721BC53A544A5900DB5FAC6A4C6D5DE91308A0` | native5pack_check.py F57713CE, with native5pack-bin added as a pinned bin (§5) |
| `native6pack.diff` | `FF10A3C036A951CA07A1B3A4C304FA12B1DB20EB2821C83A31E67A4ED9E0F09F` | `git diff --no-index` of the 3 pairs, relative paths, **LF** (0 CR bytes), +72 / -42 |
| `stage6_inputs.py` | `11E42639C5878E683DE83E6C60E5A0F513ABBACA121105C10896E183D3AC4294` | NEW: stages pack-input-zone and pack-input-combined6 from the dump dir (§2) |
| `selftest6\selftest_stage6.py` | `EB58C376AC374B293DF8AD888BBC44C2C434C52D05A4F1B5F7EE639C4A6A5CA8` | synthetic self-test of stage6_inputs.py |
| `selftest6\selftest-stage6.log` | `51BA103E222FD39999F10A0E05A30AAB0807D09D11B4719DD3EF3056C09B5A55` | ALL PASS, 7 cases (run dir `selftest6\run-20261126-083015`) |

The derivation was done by `scratch\mk_native6.py`. It checks the sha of each frozen source, refuses CR bytes, and asserts the exact count of every replacement (9 / 9 / 14 renames, then each edit exactly once).

### 1.1 Changes in native6pack.py (all visible in native6pack.diff)

1. **Names.** `native5pack` → `native6pack` in the log line, the MANIFEST title, the MANIFEST note ("built by build/agent16/pack/native6pack.py bin (sha256 …)") and the two "LATEST-… not written (native6pack)" lines. The default `--bin-out` is `native6pack-bin`.
2. **S1, bin side effects.** bin snapshots the top-level listing of the same 20 WATCH dirs that pack uses, after the pre-build checks and before the first build step. After stage-variant and verify-bins it then:
   - diffs the listing and writes `binwork-<S2>\side-effects.txt` (same format as pack's);
   - re-runs `check_pins(PINS_BIN)`;
   - adds two gates: `bin side effects: top level of all 20 watched dirs unchanged` and `bin pins unchanged after stage + verify-bins (0 bad)`;
   - on a FAIL raises, so the run ends `VERDICT FAIL`, before the STAGED / "LATEST-bin.txt not written" lines.

   Evidence that this should pass: no top-level entry of any WATCH dir has an mtime inside the native5pack bin window (06:09:50-06:11:05) or the native4bp bin window (17:38:25-17:39:45), checked with `scratch\watch_mtime.py`. Caveat: another agent writing into a watched dir (`build\agent2`, `build\agent9`, `build\agent16\dump`, …) during the bin would fail this gate. That is the reason the build runs alone (N1).
3. **Fingerprint vs native5pack.** `FP_N5 = 'a349d5292f67b127'`. Two new ON gates:
   - `ON fingerprint <fp6> != native5pack a349d5292f67b127`;
   - `ON exe lacks the native5pack fingerprint a349d5292f67b127`.

   Like every gate, both are checked before stage (the existing `gate(s) failed` raise).
4. **N1, header.** The pack outputs line now reads `SHA256SUMS.txt (no pack\LATEST-pack.txt write)`. The bin flow line names the S1 step. The header says it is a copy of native5pack.py 7DDFB8B9.
5. The plan-mode text names the S1 step.

Everything else is native5pack.py unchanged:
- PINS_PACK / PINS_BIN, WATCH, the HOLD refusal, the in_pack write guard, TMP/TEMP inside the run dir;
- DEFAULT_EXCLUDE (the 2 root dumps), jobs ≤ 2, the Idle/0x3 self-check, `--pack-run` required;
- all CTL gates (prelink A479268E, embed = snap1-on, fp 1616ce65 with header and txt = final2 gen-on, exe and map = nf2 except TimeDateStamp);
- the other ON gates, stage-variant on nativefinal2-bin, verify-bins.

### 1.2 Changes in the .ps1 and the check

- **native6pack.ps1:** the names change, and **N3**: `$W = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path` replaces the hard-coded workspace path. The .py already derives W from its own location.
- **native6pack_check.py:** NEW = native6pack-bin, with the out dir `native6pack-check-<stamp>` and the report `native6pack-check.txt`. Added:
  - native5pack-bin MANIFEST 787CD694 and exe 90BF6B45 in C3;
  - native5pack-bin in the C2 verify-bins;
  - a C4 pe-check vs the native5pack exe;
  - `a349d5292f67b127` in the C5 old fingerprints;
  - in C6, exe and map must also differ from native5pack.

### 1.3 Static checks done (no build, no pack)

- `ast.parse` / `compile` pass on both .py files, and pyflakes is clean on native6pack.py, native6pack_check.py, stage6_inputs.py and selftest_stage6.py (it is clean on native5pack's pair too).
- The PowerShell parser reports 0 errors on native6pack.ps1.
- All lines over 120 characters in native6pack.py were already in native5pack.py.
- **N2:** the diff has 0 CR bytes. On fresh copies of the 3 frozen files in `scratch\applytest6`, `git -c core.autocrlf=false apply native6pack.diff` exits 0 and produces byte-identical files (2B755B55 / 7C97F0DE / A9D12AA1). With the global `core.autocrlf=true`, the files come out CRLF but are equal after LF normalization.
- **stage6 self-test** (synthetic, `selftest6\run-20261126-083015`), ALL PASS:

  | case | result |
  |---|---|
  | pass | 2 NEW, 1 same, 1 same-bytes-other-name; the root file in the base is dropped, the dump-root file and placement-raw are never read; LF SUMS; combined 5 |
  | dry | writes nothing |
  | collision | FAIL (same name, different bytes) |
  | nothing-new | exit 3, no dirs |
  | bad-base-sums | FAIL |
  | bad-name | FAIL |
  | refuse-nodir | exit 2 |

- **Not yet run, light, proposed for after the dump-run END:**
  - `native6pack.ps1 plan --input <combined6>`, which writes only `pack\plan-<stamp>.txt`;
  - a check-script fixture run against native5pack-bin as a stand-in (scratch copy `scratch\n6check_test.py`). Expected: exactly 4 FAILs (fp not new, exe contains a349d529, exe and map equal native5pack), RESULT FAIL(4), exit 1;
  - the refusal test: `native6pack_check.py` with no native6pack-bin gives exit 2 and writes nothing.

## 2. Pack inputs (stage6_inputs.py; only after dump6_post on dump run B)

```
python -B build\agent16\pack\stage6_inputs.py --dump-dir build\agent3\gameplay\<kit dump dir of run B> --dry
python -B build\agent16\pack\stage6_inputs.py --dump-dir build\agent3\gameplay\<kit dump dir of run B>
```

- It reads only `<dump-dir>\placement-containers\{vs,ps}-<16 hex>.bin`. Root create-path dumps and placement-raw are never read (D-C2), and any other name in that subdir is a FAIL.
- **NEW** = the name is not in the base `pack-input-combined-20261126-053440` (SUMS FA99EB7D, verified with every file's sha) and the bytes are not either.
- A dump container with a base name but different bytes is a **FAIL** (name collision).
- It writes `build\agent16\dump\pack-input-zone-<S0>\` (NEW only) and `build\agent16\dump\pack-input-combined6-<S0>\`, plus `build\agent16\dump\stage6-<S0>.txt`. Every copy is re-verified, and existing dirs are refused.
  - combined6 = the base minus its 2 **root** rows (vs-A58EBA12, ps-93B9F93B; D-C2, never packed; native5pack excluded them via DEFAULT_EXCLUDE) + NEW = 139 + k files.
- **Cross-check before the GO is used:** I compare the NEW list with dump6_post's identity table, i.e. which of the 6 targets each NEW container covers. NEW containers that match no target are other new variants seen on the route. They are packed too (harmless; same placement flow) and listed in the report.

## 3. Preflight (before each heavy step; stop if any fails)

1. `Get-Process legodimensions` returns nothing.
2. The last line of `build\agent1\s5wait\status.txt` is an `END` line.
3. `perf-notes\WINDOW-HOLD.txt` is absent (the script also refuses, exit 9).
4. `build\agent16\pack\native6pack-bin` does not exist (bin also refuses).
5. No Overseer timed or exclusive window is open, and the build runs alone (N1).

## 4. Build commands (cwd = the workspace root)

```
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native6pack.ps1 plan --input build\agent16\dump\pack-input-combined6-<S0>
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native6pack.ps1 pack --input build\agent16\dump\pack-input-combined6-<S0>
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native6pack.ps1 bin --pack-run build\agent16\pack\run-<S1> --bin-out native6pack-bin
python build\agent16\pack\native6pack_check.py
```

- `<S1>` is the pack run that step 2 just created. Each step runs only after the previous one shows `PLAN OK` / `VERDICT PASS` / `VERDICT PASS`. On any FAIL: stop, report, no retry (N5).
- Everything runs at Idle priority with affinity 0x3 (children inherit), jobs 2. Reference from native5pack: pack 12.9 s, bin 68.0 s.
- Output names: the scripts write `pack\run-<S1>` and `pack\binwork-<S2>`. PLAN-dump6 §6's "native6pack-run-<stamp>" means this run dir; the scripts are not changed for the name.

### Expected outputs

**plan:** `PLAN OK`; 0 bad pins, 0 input failures, clang++ found; **143 + k** selected (4 s35 + 139 + k); **0 excluded** (the roots are not in combined6); bin target native6pack-bin.

**pack** (`run-<S1>\`, about 20 MB):
- `STAGED.tsv` has 143 + k rows;
- both lookups print `PASS: <143+k> captured containers`, and check_pack post reports 0 FAIL;
- `side-effects.txt` reads "none", and the pins are unchanged after;
- the log has "LATEST-pack.txt not written (native6pack)";
- the index goes from 19116 to more than 19384 (native5pack's new_rows);
- the log ends `VERDICT PASS`.

**bin** (`binwork-<S2>\`, about 750 MB, and `native6pack-bin\`, about 365 MB). All gates must pass:
- **CTL:** prelink = A479268E; embed = snap1-on; fp = 1616ce65e973c583 with header and txt = final2 gen-on; exe and map = nf2 except TimeDateStamp.
- **ON:**
  - fp6 cmake = python;
  - fp6 ≠ 1616ce65 and **≠ a349d529**;
  - exe contains fp6 and lacks 1616ce65 and **a349d529**;
  - no overlay path bytes;
  - exe ≠ nf2;
  - pe-check vs nf2;
  - mapcheck `--mode same`.
- **Staging:** stage-variant exit 0; verify-bins 0 FAIL.
- **S1 (new):** `binwork-<S2>\side-effects.txt` reads "none"; the PINS_BIN re-check reports 0 bad.
- The log has "LATEST-bin.txt not written (native6pack)" and ends `VERDICT PASS`.

## 5. New MANIFEST plan (native6pack-bin\MANIFEST.txt)

stage-variant.py writes it in the agent2 format.
- **Title:** `native6pack: nativefinal2 + AOT placement pack (<143+k> containers), native GPU fingerprint <fp6>`.
- **Notes:**
  - fp6 / cold first boot;
  - pack run, runtime-cache.cpp and index shas, with the row counts;
  - runtime-linked cache and linked-bank.obj shas;
  - "built by build/agent16/pack/native6pack.py bin (sha256 2B755B55…)";
  - all gates, including the S1 and FP_N5 ones.
- **Rows** (8 plus MANIFEST): exe and map are new; the 6 support files are byte-identical to nativefinal2-bin.
- **fp6** ≠ 1616ce65e973c583 (nf2), 39129c4c059be5f0 (native4bp) and a349d5292f67b127 (native5pack). The recipe and seed caches are keyed by it, so the **first boot is cold**.
- The MANIFEST sha is reported after the build and not written into any pin, LATEST file or default.

## 6. Post-checks (read-only, after bin PASS, same preflight): `python build\agent16\pack\native6pack_check.py`

It sets Idle/0x3, writes ONLY `build\agent16\pack\native6pack-check-<stamp>\`, refuses a missing bin or an existing out dir (exit 2), and checks its tool pins: verify-bins.py 80FF4C5F, pe-check.py F4368C32.

| check | what it verifies |
|---|---|
| C1 | `verify-bins.py native6pack-bin` reports 0 FAIL |
| C2 | `verify-bins.py native4bp-bin nativefinal2-bin native5pack-bin` reports 0 FAIL |
| C3 | these are unchanged: native4bp MANIFEST C5181520 / exe FA761654, **native5pack MANIFEST 787CD694 / exe 90BF6B45**, nf2 MANIFEST 4E5E2620, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 |
| C4 | pe-check of the native6pack exe vs the nf2, native4bp and **native5pack** exes |
| C5 | fp6 is new (not 1616ce65 / 39129c4c / a349d529); the exe contains fp6 and none of the 3 old ones |
| C6 | the file set = nf2; the 6 support files = nf2; exe and map differ from nf2, native4bp and **native5pack** |

The result is `native6pack-check.txt`, ending in `RESULT: PASS`.

## 7. Reporting (as N3 for native5pack)

- **stage6:** log sha, the NEW list, combined6 SUMS sha, and the target cross-check.
- **plan:** plan sha, PLAN line, count.
- **pack:** log sha + VERDICT, side-effects.txt, the "LATEST-pack.txt not written" line, the STAGED row count, index old/new.
- **bin:** log sha + VERDICT, all CTL/ON/S1 gate lines, MANIFEST and exe shas, fp6, the "LATEST-bin.txt not written" line.
- **check:** native6pack-check.txt sha + RESULT.

## 8. Failure handling and rollback

- Any FAIL stops the sequence. I report it, with no retry or patch without a new GO; a script change means a new sha and a re-rate.
- **Rollback:** delete these, and nothing else changes (no pin, LATEST file, default, other agent's dir, repo or perf-notes file; the pack/bin side-effect diffs and C2/C3 prove it):
  - `build\agent16\pack\run-<S1>`, `binwork-<S2>`, `native6pack-bin`, `native6pack-check-<stamp>`, `plan-<stamp>.txt`;
  - `build\agent16\dump\pack-input-zone-<S0>`, `pack-input-combined6-<S0>`, `stage6-<S0>.txt`.
- nativefinal2-bin, native4bp-bin and native5pack-bin stay as they are.

## 9. Not in this package

- No game run. The proof run is Step E with its own rating: `RUN-GAMEPLAY.cmd nativeonly cand6 zone`, not dump; M3 adds the cand6 word pinned to the new MANIFEST. The post is proof5_post v3 B2B920DC with base 073150, criteria in PLAN-dump6 v2 §7.
- FIXED holds for the route only (C5-S2). The visual-change risk applies as for native5pack: draws that now hit may render differently, which needs the user's eye before any promotion.
- None of M10's D1 strings appear in any command here.
