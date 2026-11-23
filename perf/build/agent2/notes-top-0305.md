# Agent 2: build pipeline - RESUME NOTE (session 3, task #1 from Agent 1; updated 03:05)

**Task #1 (session 3) steps 1-3 are DONE and staged: the B tool prep, build B (`devoffB-bin`) and S3 (`devoff3-bin`,
`native3-bin`). `@@done 1` was sent at about 03:05. Next: S3d = S3 + Agent 4's live draw.cpp write -> `native3d-bin`,
ONLY at Agent 1's explicit GO (tools ready and tested, see below). No builds or game runs from 08:30 (window 4 waits for
the user, who is asleep until about 10:00; questions go to Agent 1). Only Agent 2 builds (<= -j10). Nothing of mine is
running.**

**Staged bins** (in `build/agent2/`; file counts exclude MANIFEST.txt; MANIFEST = PASS/FAIL/NOTE counts, sha256)

| Dir | Staged | Files, size | MANIFEST | exe sha256 | Notes |
|---|---|---|---|---|---|
| `devoff1-bin` | 21:08 | 7, 214.2 MB | all PASS, 1E81AA5E... | D95273C9... | S1 OFF |
| `native-bin` | 21:48 | 8, 363.5 MB | 48/48, 91F2F817... | 3B329E95... | S1 native, fingerprint `befeb1184e6c7abc` |
| `devoff2-bin` | 23:18:53 | 7, 214.3 MB | 49/49, B87DC2D2CA22379F... | 7F0B1C1C84BC66FF... | S2 OFF; map 3A7BEEF03A527FC4... |
| `native2-bin` | 23:22:38 | 8, 363.7 MB | 72/72, D6E7F14F23373FA7... | 5D1B2DC655616027... | S2 native, fingerprint `b7cc74f980e016c3`; map 1FFB7EA997DFCBE7... |
| `devoffB-bin` | 02:40:30 | 7, 198.3 MB | 74/0/19, 8709476FF4778768... | C3F8686EBDD83340... | B = S2 + batch-nolr, OFF; map 44332E6C8E68508B... |
| `devoff3-bin` | 02:44:18 | 7, 214.2 MB | 73/0/47, B9C5175DA1904235... | 2522D43605D8A9BF... | S3 OFF; map CE2836A0574BDB56... |
| `native3-bin` | 02:46:01 | 8, 363.7 MB | 96/0/33, B50FE8D4A16565DA... | 7F7F8586D219465C... | S3 native, fingerprint `8f849b69907d4006`; map F96136D0A323980E... |

- rexruntime.dll / rexgpu-xenos.dll: S1 FDB315DC... / BFE1DF8B...; S2 and B 1C45C86977EC594C... / 77A5300B885C5274...;
  S3 D1D66AC3716835AC... / EE0A661FB0C30FCB... (the S3 SDK rebuild relinked xenos too). No staged bin has PDBs.
- Boots (Agent 8): devoffB and devoff3 PASS (`runs/0247-devoffB`, `runs/0254-devoff3`); native3 was booting at 02:58.

**Build B (DONE)**
- `b-chain.ps1 -Jobs 10`, 02:21:07-02:40:31, 1164 s (build 1060 s): verify S2 PASS; prep-b gen-check 870/870; pins
  SHA256SUMS 24CE1493FB8DAE37... / config E60EAF1CEB575572...; gate 432 PASS; stage 0 FAIL.
- snapB = snap1 at S2 + `build/agent9/install/batch-nolr` (never `install/batch`); its `rexlego/generated` is a real
  dir and every write stays under snapB; `codegen-frozen2.exe`. CompareBin vs devoff2: exe differs, map NOTE, the
  other 5 identical.
- Agent 9: review ok (02:25); static check PASS (`build/agent9/logs/mapcmp-AB.txt`: same 164,786 sub_ functions and
  27 hooked aliases; .text 159.3 -> 142.6 MB, -10.52%; 19 warnings, as snap1). Rollback copies are in
  `build/agent9/repin/`, for use only after a gate FAIL and Agent 1's GO.

**S3 (DONE; Agent 1 approved step 3 at 02:47)**
- Inputs: game `001336f` + SDK `c5fe668` (from Agent 10's 4 hashes: 11DE333F rex_app.cpp, 4331A312 audio_system.cpp,
  4EC71328 settings_registry.cpp, 9CBE6DBF settings_preferences.cpp) + the pre-sprint plume/simde edits, as in
  S1/S2. Recorded in the PATCHES-S3.tsv / STATE-S3 header lines and in each MANIFEST (`S3-notes.txt`). Generated code
  = the pinned S1 output; batch-nolr only in B.
- Agent 10's `build/agent10/s3/S3-include.tsv` (A1E7C83F..., 28 INCLUDE / 0 EXCLUDE vs STATE-S2-2315) ->
  `S3-rules.txt` -> `snap-patch.py apply S3 ... --note-file=build\agent2\S3-notes.txt` at 02:41:38: COPY 28 (3 new),
  DELETE 0, HELD BACK 0, errors 0. PATCHES-S3.tsv 2DA2AB6C...; STATE-S3-0241.tsv 4F791C2E80594C03...; verify S3 PASS.
- devoff3: `run-s3.ps1 -Stage off`, 02:42:07-02:44:19 (SDK build + install + game 113.6 s, stage 16.1 s). native3:
  `run-s3.ps1 -Stage native` (with configure), 02:44:40-02:46:03 (build 51.8 s, stage 27.6 s). MANIFEST patch rows
  S1 2 / S2 18 / S3 28.
- Checks: both exes contain 'which can hang when the guest pauses'; native3 has the 3 LEGO_NATIVE_* toggles;
  rexruntime has audio_shutdown_detach_worker; native3's MANIFEST lists settings_registry A37337001EBDC277 ->
  4EC71328043FA6BA and settings_preferences C78112AA6E50F79D -> 9CBE6DBF9CEDA62D. The fingerprint changed because it
  hashes 271 inputs (`snap1-on/generate-native-gpu-fingerprint.cmake`), including both settings files and draw.cpp.
- snap1-off `compile_commands.json`: 477 entries, 0 gpu_native files, so draw.cpp is not in OFF builds and devoff3
  stays valid for S3d (reported 02:50). snap1-on: 533 entries, 39 gpu_native.
- Tool edits: snap-patch.py `--note/--note-file` (`patch-s3-tools.py snap-patch`; `s3-tools-test.py` PASS);
  stage-snap-bin.ps1 lists the PATCHES of S1..S<N> for S<N> (`patch-s3-tools.py stage`, 45F62362 -> A685B9D1).
- Downstream: Agent 11 `testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default`; Agent 8 boots; Agent 7
  `native3_boot_check.py`; Agents 5 and 4 use native3.

**S3d (next; ONLY at Agent 1's explicit GO, after Agent 4's live draw.cpp write; never from 08:30)**
- At 03:01 live draw.cpp == snap1 == 50AA3B1DEE615678... (306,221 B, mtime 11-21 21:24:30). Dry check at 03:01
  (`snap-patch.py plan CHK build\agent2\s3d-chk-rules.txt` -> `snap1/PLAN-CHK-0301.txt`): all 23843 live files equal
  snap1 (0 differing, 0 held back), so the S3d apply should copy exactly draw.cpp.
- Steps:
  1. `python build\agent2\prep-s3d.py <Agent 4's sha256> --go HH:MM`: 9 checks (S3 is snap1's state, live = the given
     hash and != snap1, no gpu_native in snap1-off, SDK DLLs == native3-bin); writes `S3d-rules.txt` + `S3d-notes.txt`.
  2. `python build\agent2\snap-patch.py plan S3d build\agent2\S3d-rules.txt --note-file=build\agent2\S3d-notes.txt`
     (expect COPY 1, errors 0), then `apply` with the same args (`cmd /c` redirect to `s3d-apply.txt`); check
     PATCHES-S3d.tsv (1 row) and STATE-S3d-HHMM.tsv; `verify S3d` PASS.
  3. Background task: `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s3d.ps1` (guards, then
     configure + native game build, tag snap3d, then stage `native3d-bin` with `-CompareBin native3-bin`; ~2 min).
  4. Check `snap3d-stage-native.log` (0 FAIL; exe differs, map NOTE, the other 6 identical) and the MANIFEST rows
     (S1 2 / S2 18 / S3 28 / S3d 1); post exe/map/MANIFEST/fingerprint to Agent 1 (and Agents 8, 4, 7, 5).
- If Agent 4's write touches more than draw.cpp, or a hash mismatches, ask Agent 1.
- Tool edits (03:00): `patch-s3d-tools.py`: stage-snap-bin.ps1 A685B9D1 -> D68B4533 (S<N><suffix> lists S1..S<N>,
  then its own; `-CompareWhy`; diff `S3d-diffs/stage-snap-bin.ps1.S3d.diff`, 174C04CF); `patch-stop-s3d.py`:
  stop-snap.ps1 414DF411 -> B9AECC6A (also kills run-s3d.ps1). `s3d-tools-test.ps1`: all PASS. `prep-s3d.py`
  refuses as expected (live == snap1; wrong hash; bad hash or --go).

**Live tree edit (my only one)**
- 21:57:57: live `DimensionsRecomp/thirdparty/plume/plume_d3d12.cpp` B88E4E86... -> 564568D4... (S1+p2, Agent 1's
  step 1); backup `build/agent2/live-backup/plume_d3d12.cpp.B88E4E86`. No other live edit since.

**Other**
- (b), the FFX-headers rexruntime for native: not picked (S3 took fix (a)); my build plan stays in section (b) of
  `perf-notes/agent7-s3-proposal.md`.
- The relaunch checkpoint (01:22-01:27) and the batch 1/2 details are further down in this file.

**Scripts** (all in `build/agent2/`)
- `snap.py`; `snap-patch.py` (plan/apply/verify/revert, `--note`/`--note-file`); `make-rules-from-tsv.py`;
  `build-snap.ps1` (-Phase sdk|game|all, -Native, -Tag, -Jobs, -PrelinkJobs, -SkipConfigure, -KeepGoing, plus the B
  options); `gen-check.py`; `snap-gate.py`; `codegen-frozen/` (frozen and frozen2 stand-ins); `stage-snap-bin.ps1`
  (-Variant, -SnapTag, -BuildTag, -OutDir, -CompareBin, -CompareWhy, -ManifestNotesFile, ...); `run-s2.ps1`;
  `run-s3.ps1 -Stage off|native`; `run-s3d.ps1`; `prep-s3d.py`; `prep-b.py`, `run-b.ps1`, `b-chain.ps1`;
  `patch-b-tools.py`, `patch-s3-tools.py`, `patch-s3d-tools.py`, `patch-stop-s3d.py` (each run once; they refuse once
  their backups exist); `s3-tools-test.py`, `s3d-tools-test.ps1`; `stop-snap.ps1`; `splice-notes-top.py`.
- If Agent 1 opens a window mid-build, run `powershell -NoProfile -ExecutionPolicy Bypass -File
  build\agent2\stop-snap.ps1` within about 2 min, then re-run the same stage later; ninja resumes.
- Keep every intermediate (snap1, snap1-sdk, snap1-off, snap1-on, snapB, snapB-off, the backups, the staged bins and
  every `*.pre-B`, `*.pre-nolr`, `*.pre-S3`, `*.pre-S3d`) until Agent 1 says otherwise. Free C: 254.4 GB at 02:47.
- agy-grid delivers only the `@@to` line itself, so every message is ONE line; the
  details live in this file.
