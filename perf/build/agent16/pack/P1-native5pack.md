# P1: native5pack candidate pack + bin (M16, S5): for M10 rating before any build

**Goal:** build a **candidate** native bin from the combined plan `plan-20261126-053448.txt` (0D10FF36: 143 containers, input
`pack-input-combined-20261126-053440`, SHA256SUMS FA99EB7D). The output goes to a NEW dir, `build\agent16\pack\native5pack-bin`.
- No promotion and no repin.
- No LATEST-pack.txt or LATEST-bin.txt write.
- No defaults change and no game launch.

Promotion stays the user's Phase 4 call.

## 1. Scripts (new files, all under build\agent16\pack)

| file | sha256 | what |
|---|---|---|
| `native5pack.py` | `7DDFB8B9DD53E0BF47980D2D4F41577D73A9987953DA4ABEDE3DEEF34184C461` | native4bp.py 37FD3989 plus 4 changes (diff below) |
| `native5pack.ps1` | `22245C44E4E94942212E898C0623C844B0C917CE4D3D50EA53382FAE0DED11D0` | native4bp.ps1 83A8B01F; only the script name and comments change (Idle, affinity 0x3, devshell -Jobs 1) |
| `native5pack.diff` | `F5BBAEBE3FBD9927B35972F5ED381E97E54F26C8B8BF40607D562A68CA67919C` | `git diff --no-index native4bp.py native5pack.py` (+14 / -13) |
| `native5pack_check.py` | `F57713CE9EDBBCD8D7A6E88B9F064A15ACAAB1D6D2A936618CE770C86DE4F6B5` | read-only post-checks (section 4) |

native4bp.py and native4bp.ps1 stay as they are, so the native4bp-bin MANIFEST note (sha 37FD3989) remains true.

Changes in native5pack.py:
1. The LATEST-pack.txt write is replaced by a log line. pack no longer writes any file outside `run-<stamp>\`.
2. The LATEST-bin.txt write is replaced by a log line.
3. bin needs `--pack-run`; there is no LATEST fallback. Without it, bin fails closed with "pack run has no pack-check.json".
4. The default `--bin-out` is `native5pack-bin`. The names in the log line, the MANIFEST title and the MANIFEST note change to "native5pack".

Everything else is unchanged:
- pins PINS_PACK/PINS_BIN, the watched-dir diff, the HOLD file refusal and the in_pack write guard;
- jobs ≤ 2, Idle/0x3 self-check, CTL reproduction gates, ON gates, stage-variant and verify-bins.

The derivation was done by `scratch\mk_native5.py`, which asserts that each of its replacements occurs exactly once.

**Static plan with the new script:** `build\agent16\pack\plan-20261126-060314.txt`
`161F7C5472770CA6358DE2F25B80ACDC465D583FC516BA0A3F11F7A68AD5CB94`.
- PLAN OK: 0 bad pins, 0 input failures, clang++ found.
- 143 selected (4 s35 + 139), 2 root dumps excluded, same as 0D10FF36.
- Bin staging target: `build\agent16\pack\native5pack-bin`.

## 2. Preflight (each heavy step; stop if any fails)

1. `Get-Process legodimensions` returns nothing.
2. The last line of `build\agent1\s5wait\status.txt` is an `END` line.
3. `perf-notes\WINDOW-HOLD.txt` is absent (the script also refuses with exit 9).
4. `build\agent16\pack\native5pack-bin` does not exist (bin also refuses).
5. No Overseer timed window is open.

## 3. Build commands (cwd = `<workspace>`)

```
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native5pack.ps1 pack --input build\agent16\dump\pack-input-combined-20261126-053440
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native5pack.ps1 bin --pack-run build\agent16\pack\run-<S1> --bin-out native5pack-bin
```

- `<S1>` is the stamp of the pack run that step 1 just created.
- Run step 2 only if step 1 printed `VERDICT PASS`.
- Both steps run at Idle priority with affinity 0x3, with child processes inheriting both, and jobs 2.
- Reference timings from native4bp: pack 8.1 s, bin 70.1 s. More containers should mean a longer prelink, so expect a few minutes.

### Expected outputs

**pack:** `build\agent16\pack\run-<S1>\`, about 15-20 MB (native4bp's run was 11 MB).
- `STAGED.tsv` lists 143 rows.
- `pack-log.txt` ends with `VERDICT PASS`.
- Both lookups print `PASS: 143 captured containers`.
- check_pack post reports 0 FAIL.
- `side-effects.txt` reads "none".
- Pins are unchanged afterwards.
- The log contains "LATEST-pack.txt not written".
- The index row count goes from 19116 to more than 19267.

**bin:** `build\agent16\pack\binwork-<S2>\`, about 750 MB plus some extra (native4bp's was 746 MB), and `build\agent16\pack\native5pack-bin\`, about 365 MB.

Gates that must pass:
- **CTL (proves the recipe still reproduces nativefinal2):**
  - prelink output = A479268E;
  - embed = snap1-on generated;
  - fingerprint = 1616ce65e973c583, with header and txt equal to final2 gen-on;
  - exe and map = nf2, except the TimeDateStamp and the map Timestamp line.
- **ON:**
  - new fingerprint present, 1616ce65 absent;
  - no overlay path bytes;
  - exe differs from nf2;
  - pe-check vs nf2 passes;
  - mapcheck `--mode same` passes.
- **Staging:** stage-variant exits 0; verify-bins reports `RESULT: 0 FAIL`.
- The log contains "LATEST-bin.txt not written".

## 4. New MANIFEST plan (native5pack-bin\MANIFEST.txt)

stage-variant.py writes it in the agent2 format, with the fixed header text "Agent 2 (board run 2 task #1)".

**Title:** `native5pack: nativefinal2 + AOT placement pack (143 containers), native GPU fingerprint <fp5>`.

**Notes:**
- the fp5 / cold-first-boot note;
- the pack run, runtime-cache.cpp and index shas, with the row counts;
- the runtime-linked cache and linked-bank.obj shas;
- "built by build/agent16/pack/native5pack.py bin (sha256 7DDFB8B9…)";
- all gates.

**Rows** (8, plus MANIFEST.txt itself):
- `legodimensions.exe` and `legodimensions.map`: new.
- These 6 are byte-identical copies of nativefinal2-bin: achievement_unlocked.wav, amd_fidelityfx_dx12.dll, FiraSans-Regular.ttf, rexgpu-xenos.dll, rexruntime.dll, TracyClient.dll.

**fp5** must differ from both 1616ce65e973c583 (nf2) and 39129c4c059be5f0 (native4bp). The PSO recipe and seed caches are keyed by the fingerprint, so the **first boot is cold**.

The new MANIFEST sha is reported after the build. It is not written into any pin, LATEST file or default.

## 5. Post-checks: verify-bins and pe-check (read-only, after bin PASS, same preflight)

```
python build\agent16\pack\native5pack_check.py
```

The script sets Idle/0x3 on itself and writes ONLY `build\agent16\pack\native5pack-check-<stamp>\`. It refuses a missing bin or an existing out dir (exit 2), and checks that its tools are pinned: verify-bins.py 80FF4C5F, pe-check.py F4368C32.

| check | what it verifies |
|---|---|
| C1 | `verify-bins.py native5pack-bin` reports 0 FAIL. |
| C2 | `verify-bins.py native4bp-bin nativefinal2-bin` reports 0 FAIL, i.e. the pinned bins are untouched. |
| C3 | native4bp MANIFEST C5181520, exe FA761654, nf2 MANIFEST 4E5E2620, LATEST-pack AC7B9053 and LATEST-bin 76D0EFB9 are unchanged. |
| C4 | `pe-check.py --new native5pack exe --ref <nf2 exe>` and `--ref <native4bp exe>` both report RESULT PASS (exports and imports equal). |
| C5 | The MANIFEST fp5 is new; the exe contains fp5 and contains neither 1616ce65 nor 39129c4c. |
| C6 | The file set equals nf2's; the 6 support files are identical to nf2; exe and map differ from both nf2 and native4bp. |

The result is `native5pack-check.txt`, ending in `RESULT: PASS`.

**Fixture test** (pointed at native4bp-bin as a stand-in candidate, output in scratch `n5check-test-20261126-060436`, report F7C96C8F): C1-C4 and the C6 support files PASS. Exactly the 4 expected FAILs fire: fingerprint not new, exe contains 39129c4c, and exe and map equal native4bp. RESULT FAIL(4) with exit 1. The refusal test (no native5pack-bin) gave exit 2.

## 6. Failure handling and rollback

- Any FAIL stops the sequence. I report it to the Overseer and do not retry or patch without a new GO, since a script change means a new sha and a re-rate.
- **Rollback:** delete `build\agent16\pack\run-<S1>`, `binwork-<S2>`, `native5pack-bin` and `native5pack-check-<stamp>`. Nothing else changes:
  - no pin, LATEST file or default;
  - no other agent's dirs;
  - no repo or perf-notes file (the watched-dir diff and C2/C3 prove this).
- native5pack.py, .ps1 and _check.py can stay or be deleted.
- nativefinal2-bin and native4bp-bin remain the pins.

## 7. Not in this package

- No game run. The miss-count proof run on native5pack-bin is drafted separately for a later GO.
  - It is meant to settle the 22 no-identity guests and VS A7FA6EA0 (formerly A7FA6E00).
  - Expectation: the 60 story identities become hits.
  - The 22 no-identity draws (5.3%) are expected to **stay** misses, because none of them is in the pack. The run measures that rather than fixing it.
- The visual-change risk from native4bp's README still applies: draws that now hit may render differently. That needs the user's eye before any promotion.
- None of M10's D1 strings appear in any command here.
