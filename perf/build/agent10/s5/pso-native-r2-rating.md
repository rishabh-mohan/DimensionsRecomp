# M16 PSO diffs, r2 (2.3 revised) and psobin: rating

M10, 2026-11-25 17:57. Read-only review. E10.2 did the structural re-check (notes: `build/agent10/s5/scratch-m16/NOTES.md`); I checked its results myself.
This file adds to `pso-native-rating.md` (E22DE772). Where they differ, this file wins.

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent16/pso/pso-unlocked-aux-save.diff (2.3 r2) | 52341EDF86CEEA02 | 12541 |
| build/agent16/pso/pso-prepare-merged.diff (2.2, unchanged) | 36ED6E02EAE588C7 | 6158 |
| build/agent16/pso/README.md | 4C4F33C09D9BF2F0 | 13438 |
| build/agent16/psobin/psobin.ps1 | 3B3DC537BDE8ABE9 | 1122 |
| build/agent16/psobin/psobin.py | A4AE67DDE2D2E721 | 32234 |
| both-applied pipeline_library.cpp (M16 scratch) | 4247ECB9 (sha8) | - |

Base: DimensionsRecomp a8e8dc8. HEAD:rexlego/src/gpu_native/pipeline_library.cpp is blob 44840383. Bin base: build/agent16/pack/native4bp-bin (MANIFEST C5181520).

## Verdict

- **2.2 pso-prepare-merged: SAFE.** Unchanged from E22DE772.
- **2.3 pso-unlocked-aux-save r2: SAFE.** A1 is met and S1, N3 and N4 are fixed. With both envs unset, the code is HEAD except for the stricter Stop() claim.
- **psobin: SAFE-IF P-C1 and P-C2.** It builds a separate bin with no game run, no registry access and no writes to pinned bins.
- **Fingerprint claim: ACCEPTED (option a).** The fingerprint stays 39129c4c059be5f0. Condition B2 of E22DE772 is replaced below.

## What I checked

- **A1 (aux compile gate):**
  - The new env is LEGO_NATIVE_PSO_AUX_UNLOCKED. It is read with its own getenv, and unset or "0" means off.
  - It is latched once in Open() on the success path, before g_library is published.
  - Auxiliary() keeps the HEAD body. The only addition is one early-return line before the lock_guard, so with the env unset the lock is held across load, compile and Store, as at HEAD.
  - AuxiliaryUnlocked does the load and the hit/miss stats under mutex_, the compile without the lock, and Store under a new lock.
- **S1 (concurrent Save after Stop):**
  - Stop() now claims saving_ with a CAS loop and never releases it.
  - At HEAD (L325-337), Frame() does a CAS, then Save(), then store(false). Save() never touches saving_, so the wait always ends. After Stop, Frame's CAS fails and no second Save/Serialize can start.
  - The library is leaked after Stop, so leaving saving_ claimed is correct.
- **N3:** the "gave up" line is now REXLOG_WARN. **N4:** the duplicate-PSO case is documented in a code comment.
- **SnapshotUnlocked:** I re-read it. It is bounded at 6 passes, give_up frees the buffer, and a copy is accepted only if Serialize succeeded and the size is unchanged. An HRESULT other than E_INVALIDARG gives up immediately, and every give-up falls back to the locked path. The unsaved_ accounting subtracts only what was counted at the query. The verdict on SAVE_UNLOCKED's driver behaviour still rests on NVIDIA evidence only (B4 stays).
- **Apply:** E10.2 ran `git apply --check` against a8e8dc8: 2.3 r2 exit 0, 2.2 exit 0. M16's applytest log shows both orders giving the same file (4247ECB9).
- **Fingerprint:**
  - rexlego/CMakeLists.txt L604-786 at a8e8dc8 lists the native GPU fingerprint inputs explicitly. pipeline_library.cpp is not among them. The GLOB_RECURSE at L753 only adds `src/gpu_native/*.h`, and both diffs change only the .cpp.
  - CachePath() (HEAD L99-105) is `<exe dir>/cache/native-pso.bin`; the recipes and seed sit next to it. Each bin dir therefore has its own cache files.
- **psobin** (E10.2 read it in full; I spot-checked):
  - Every write goes through in_out(), which is limited to build/agent16/psobin (L123).
  - The only kill is `taskkill /T /F` of its own child tree on timeout (L223).
  - It never starts the game and never touches the registry.
  - It refuses to run if WINDOW-HOLD.txt is present (L30), if a pin fails, or if the out bin already exists.
  - The CTL gate (relinking the HEAD file must reproduce the native4bp exe) and the pe-check are both gating. stage-variant writes to `.tmp`, then renames. verify-bins is gating.

## Conditions

- **B2 (replaces E22DE772 B2): the fingerprint is unchanged.**
  - A cache, recipe file or seed made by native4bp is therefore valid for the PSO bin, and the PSO bin's first boot is cold only because its bin dir has no cache yet.
  - For any A/B, both arms must start from the same cache state: both cold (delete `cache/native-pso.bin`, `cache/native-pso-recipes.bin` and `native-pso-seed.bin` in both bin dirs) or both seeded with the same files. Compare warm with warm.
  - M16 should correct README L125-127 and L155, which still say the fingerprint changes.
- **B1, B3 and B4 still apply.** B1: separate bin, final2 method, pe-check, MANIFEST, no pinned bins touched. B3: all envs default off until the functional row passes. B4: SAVE_UNLOCKED is backed by NVIDIA evidence only.
- **P-C1 (reference arm):** psobin builds on native4bp-bin, not on nativefinal2-bin. Any PSO A/B must use native4bp-bin as its reference arm (the matrix's n4bp60 arm, not nat60), or the native4bp changes are mixed into the result.
- **P-C2 (tie the src file to the diffs):**
  - psobin pins `--src` by sha only. The diffs are only recorded in the MANIFEST, and the stage title always says "2.2+2.3" (L507).
  - Before the bin is used, the operator must confirm that `--src` is the both-applied file 4247ECB9 (git blob 8583c5c), or change the MANIFEST title to match the src actually used.
  - The best fix is a gate in psobin: the LF-normalised src must hash to the expected blob.

## Findings

- **NIT A-n1:** "env unset = HEAD" really means "HEAD except Stop()". The Stop() claim is always on. It is harmless and README L96 already says so.
- **NIT P1:** psobin.ps1 L14 hard-codes the absolute workspace path. psobin.py already derives it from its own location.
- **NIT P2:** the side-effect listing covers only the top level of each watched dir. relink.py's out-dir check and recompile.py's explicit object paths make up for this in practice.
- **Open:**
  - No byte interdiff against the old 2.3 (5CFD12E8): that file is gone. The hunks were compared by structure only.
  - I did not rate native4bp itself here.
