# final2 BIN-PINS (M2, 2026-11-25 16:12)

These bins were built from the **committed** source:

- rexglue-sdk perf/opt `a7e79c09135f160f63bfaf8634f4e3b9cb760a75`. This is 1ba3cdb (FINAL-DEFAULTS) followed by a7e79c0 (#33 nohunk5, 57CFA8AD).
- DimensionsRecomp perf/opt `2de88ce9d1992aea3d0daa721ef5ac6c62f7d568`. Its gitlink points to a7e79c0.

The tools were rated CONFORMS in `build/agent10/session3/final2-tools-rating.md` 366294FD. Rating conditions P1-P3 are covered below.

## Bins (pinned: do not modify)

### `build/agent2/devfinal2-bin` (Xenos ship; base devoff4b-bin)

| file | sha256 |
|---|---|
| MANIFEST.txt | 4A4A13EDFBFF6A5F32798837A4156256A5A58A2C44579F272B5147768E50982D |
| legodimensions.exe | 6C8E281156CCE828A217B870F273021202F953F7230C7C7BA6CC3E4EA7F45581 (b/xe) |
| legodimensions.map | 3F93A71469556D485142F40FF9FF742CC3E9F031A077774C9C24253C872477E6 (b/xe) |
| rexruntime.dll | 641BD22519921ACDD0D49E25E2A15AA8439DE1675B90734EF5B0D5ED7A498C70 (b/rt) |
| rexgpu-xenos.dll | 9A7CC3F4853A8E8B01501734B1E53ABB36962F05C22BAF46638217F27E90A4EC (b/gpu) |
| TracyClient.dll | 85044850B6C663B5CE8722285D13070381C33C9ABC49D06B3E59BA0277F8FF4E (devoff4b's) |
| FiraSans-Regular.ttf | C29556A2719BF613EF3D5E070E40D903A8965D9C081BECA1375DC1E6E0F93C23 |
| achievement_unlocked.wav | A707019154484B9DE0AD310826668C0B58C22B8A842227293421643901BC29A5 |

### `build/agent2/nativefinal2-bin` (native; base native4b-bin)

| file | sha256 |
|---|---|
| MANIFEST.txt | 4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163 |
| legodimensions.exe | 090A420BA16797A1A94FFAA0D07730734BEF906435A11081B5638C90C4856C25 (b/nat, fingerprint 1616ce65e973c583) |
| legodimensions.map | B669786E17B3B09E53840139A9B372FD66D15019C8B9AD4A59797134A1139D92 (b/nat) |
| rexruntime.dll | 641BD22519921ACDD0D49E25E2A15AA8439DE1675B90734EF5B0D5ED7A498C70 (b/rt, == devfinal2-bin) |
| rexgpu-xenos.dll | 9A7CC3F4853A8E8B01501734B1E53ABB36962F05C22BAF46638217F27E90A4EC (b/gpu, == devfinal2-bin) |
| TracyClient.dll | 85044850B6C663B5CE8722285D13070381C33C9ABC49D06B3E59BA0277F8FF4E (native4b's) |
| amd_fidelityfx_dx12.dll | 12A5081257EC95B0B53AD51B4A87FB3C03F97FE0BBB59F9496968F8D50EF93A6 |
| FiraSans-Regular.ttf | C29556A2719BF613EF3D5E070E40D903A8965D9C081BECA1375DC1E6E0F93C23 |
| achievement_unlocked.wav | A707019154484B9DE0AD310826668C0B58C22B8A842227293421643901BC29A5 |

## Overlay source = committed blobs (EOL form)

Each overlay file is written from `git cat-file blob` in the EOL form of the snap1 base file. Every form's sha256 equals the after column of the rated diffs. It also equals `final/work/new` for the FINAL files and `s33/sdk` for the #33 files. Source: b/prep.txt.

| path | blob sha256 (LF) | overlay form |
|---|---|---|
| rexlego/src/gpu_native/shaders.cpp | 88D8CC7F92CA8D8587B7C4A09B3B3D6C1F90FFB7E1DCCE75B31956E3AA0C0EF6 | **CRLF** 4B8250E976A384010915FA66C6E2279397C83A3DE05DCF2CFAC5FD452E85EEFD (the autocrlf=true checkout form; == nativefinal source; keeps fingerprint 1616ce65e973c583) |
| rexlego/src/gpu_wait_backoff.cpp | 74115EEA26C4AEB263275AED08CCD986682E27A29BE68990C873AEB0C527017F | LF = blob |
| rexglue-sdk/include/rex/graphics/d3d12/pipeline_cache.h | 0BAF28BE633759CD... | LF = blob |
| rexglue-sdk/src/graphics/{frame_stats.h, shared_memory.cpp, d3d12/command_processor.cpp, d3d12/pipeline_cache.cpp} | 9F3C4F9D / E2465A15 / 00EA93D3 / C4CB51CC | LF = blob |
| rexglue-sdk/src/{core/clock, core/timer_queue, kernel/xboxkrnl/xboxkrnl_rtl, kernel/xboxkrnl/xboxkrnl_threading, system/runtime, system/xmemory, system/xobject, system/xthread}.cpp | EAE926AC / EF70211E / CEB5529A / 7CA55716 / A997D005 / 3745C04A / 691A34BB / 3B50A95E | LF = blob |

## Defaults proof

**Committed source.** prep-final2 checks these as PASS default lines in b/prep.txt:

- `REXCVAR_DEFINE_BOOL(d3d12_pipeline_creation_no_wait, false, "GPU/D3D12", ...)` (pipeline_cache.cpp:70). **#33 is opt-in, default OFF.**
- `#define LEGO_GPU_WAIT_BACKOFF_DEFAULT_US 500` (gpu_wait_backoff.cpp). **q500 is ON by default.**
- The win3 SDK cvar defaults come from FINAL-DEFAULTS 955543F5, unchanged in 1ba3cdb. They are logged at runtime by `Final defaults:{}` / `Final defaults (GPU): {} {}`.
- The miss cache defaults to ON in shaders.cpp (4B8250E9 == the nativefinal source, rated before).

**Binary needles.** Each needle is in the ON output and absent from the reference (all PASS):

| leg | needles |
|---|---|
| rt | `Final defaults:{}` |
| gpu | `Final defaults (GPU): {} {}`, `d3d12_pipeline_creation_no_wait`, `dropped draws {} \| forced pipeline waits {:.1f} ({}x)` |
| xe | `GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=` (the env-off branch; q500 itself is proven by the source define and at runtime by check-defaults) |
| nat | `Native GPU: shader miss cache {} ({}{})`, `1616ce65e973c583`. ON lacks `9b40acbbef4c57b3` and the back-off string. |

The runtime proof is M8's smoke run, with check-defaults `--mode xenos` / `--mode native`.

## Gates (all PASS)

- **prep-final2 (real):** RESULT PASS. The dry run is saved as `prep-final2-dry.txt` (PASS).
- **fsyntax2:** 23/23 TUs (rt 8, gpu 10, xe 1, nat 4), 0 errors.
- **CTL (D1).** Each output is identical to its reference except 1 TimeDateStamp:
  - rt == devoff4b rexruntime A33801D1
  - gpu == devoff4b rexgpu-xenos E3CB99CF
  - xe == devoff4b exe + map (map equal except the Timestamp line)
  - nat == native4b exe + map
- **Include order:** the gpu -I `b/DimensionsRecomp/rexglue-sdk/include` is ahead of snap1's in all 10 commands. The nat -I `b/nat/gen-on` is ahead of `snap1-on/generated` in all 4.
- **Logs and paths:** no pch/error text in any compile log, and no overlay path bytes in any output.
- **Checks vs references:**
  - D5 pe-check: PASS on all 4 legs.
  - mapcheck: xe s4c (31) vs devoff4-bin PASS; nat `same` vs native4b PASS.
  - Shared DLL `snap1-sdk/install/bin/rexgpu-xenos.dll`: E3CB99CF before and after every step.
- **Staging order (P1):** devfinal2 was staged first, then nativefinal2.
  - The stage log has `PASS rexruntime.dll == devfinal2-bin copy` and `PASS rexgpu-xenos.dll == devfinal2-bin copy`. This check is hard: a missing devfinal2-bin counts as FAIL.
  - Both new DLLs differ from A33801D1/E3CB99CF, and each equals its b/<leg>/link-on output.
- **D6 verify-bins:** the new bin plus devoff4b (DE11A914), devoff4b-cg26 (917AE86E) and native4b (B63769FE) all show 0 FAIL, after each stage.
- No cache/ folder in either bin.
- Leg times: rt 12.2 s, gpu 21.3 s, xe 17.2 s, nat 35.3 s.

## Tools and logs (P2)

| file | sha256 |
|---|---|
| `prep-final2.py` | 4B20F22AB773A73610922A556191C06EC48CFDD82BB823DCCDED757F842DFFB8 |
| `fsyntax2.py` | 3FC03399AB003398DCC2A364376CCB1BDDA0583FF9DEE1A591C0ECDCDBB83D1D |
| `build-final2.py` | 80C11DCCD4B41D7C71C468CB707C4E16BD143B531C7421CB70AC4EBD86B45047 (rated DCE13E19 + the NIT "hard devfinal2 copy check" only) |
| `prep-final2.diff` | DEBC83124901A4BBD8B8ACD5C06D3216FADFC02F3288E5040DD0F7F031345E4A |
| `fsyntax2.diff` | C6724DBB4ED957F17DDE6F958A567A33468673FA7A38D1E508CE3E54844F1A51 |
| `build-final2.diff` | DA059ECAE3EBFB2FF4E6DD2E3D22CE60B33A6294F7BB1491A387B937AEE44579 |
| `prep-final2-dry.txt` | FC2078B60C4E2F8C6F88B2022163E654B123C7F6EF83DE88DBBCBB3950284D6B |
| `b/prep.txt` | BADB17BF7A71DF3395AE21289A0701B801A1C5A638F2F45369C64F773AE125CB |
| `b/fsyntax/fsyntax.txt` | 684E5ABA5A60178C34F51B65744B22D1D5A7F189563DD909054017E7E1803D59 |
| `b/rt/build-final.txt` | 8340F0894B0E83506DC387D8C4D760478CD7BC356AAB2699F5AED476C522D96A |
| `b/gpu/build-final.txt` | B3B499A1A0F28424C653D61C6A6EA4B822C934EE8C66749226BF4F185E1EBCD8 |
| `b/xe/build-final.txt` | 6A72F3995C2D0703C5FFCE14CB54EEE30D4DDE0B7ADD18473E58D763A3EDF740 |
| `b/nat/build-final.txt` | F701BE5D01CEE4A3E61C30C9C7DA9890C0D3FD9FE120F63F19A390E03F0C0411 |
| `b/xe/mapcheck.txt` | F5D375A10C71F17CD77F71760B36F4DB7BDEEE8716991097AB1824B306849506 |
| `b/nat/mapcheck.txt` | DE24D98EB06B9BC5A735F7EEC2E79510A27F88E1E2C3442762130D437284D984 |
| `b/nat/gen-on/native-gpu-build.txt` | BC37A606A3F28CAB7092BD130A71506ED358D5F1007A0AC6F743C717194A6214 ("LEGO Dimensions native GPU 1616ce65e973c583") |
| `b/stage-devfinal2/build-final.txt` | 577AE07B9A1BD825FE718D4743B20C7CB7412CC4AFDC62CB3A9AAE03AE4248EC |
| `b/stage-nativefinal2/build-final.txt` | C650784D86DEBC0FFF27E17B3C8B71BF60545106B06AFF9F1D1AB0DE96EEC428 |

These tools ran unchanged by path:

- recompile.py 855BCC79148E2DA8
- relink.py F3C6EEAF332AB213
- stage-variant.py D2BD1C6358FC19C1
- verify-bins.py 80FF4C5F581C4B1B
- final/pe-check.py F4368C32076AAA3E
- s4b/mapcheck-s4c.py F8CB7B495F74D978

Nothing under snap1*, snap1-sdk/install or any existing bin was written. cmake --install was never run, and no repo was touched.

## Smoke (M8; P3)

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\first-boot.ps1 -BinDir build\agent2\devfinal2-bin -Tag devfinal2-smoke -WatchSeconds 120
python build\agent2\final\check-defaults.py build\agent8\runs\<HHmm>-devfinal2-smoke\game.log --mode xenos
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\first-boot.ps1 -BinDir build\agent2\nativefinal2-bin -Tag nativefinal2-smoke -WatchSeconds 120
python build\agent2\final\check-defaults.py build\agent8\runs\<HHmm>-nativefinal2-smoke\game.log --mode native
```

Pass criteria:

- The game reaches first 3D.
- check-defaults PASS.
- The game.log has no `d3d12_pipeline_creation_no_wait` line.
- No WER and no dialogs.
- A clean exit.
