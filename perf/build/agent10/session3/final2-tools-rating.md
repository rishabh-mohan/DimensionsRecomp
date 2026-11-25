# final2 tool rating (prep-final2 / fsyntax2 / build-final2)

M10, 2026-11-25 ~16:10 local. Rates M2's three final2 tool diffs against the final/ tools I rated in final-build-rating 94CC9FA7. Source: the pushed commits rexglue-sdk a7e79c0 and DimensionsRecomp 2de88ce.

## Files

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent2/final2/prep-final2.diff | DEBC83124901A4BB | 22783 |
| build/agent2/final2/prep-final2.py | 4B20F22AB773A736 | 24459 |
| build/agent2/final2/fsyntax2.diff | C6724DBB4ED957F1 | 4003 |
| build/agent2/final2/fsyntax2.py | 3FC03399AB003398 | 6914 |
| build/agent2/final2/build-final2.diff | 1A8F4FB12FEA693A | 17723 |
| build/agent2/final2/build-final2.py | DCE13E196CCE36C8 | 22837 |
| build/agent2/final/prep-final.py (base) | 83F732CA9CEB301F | - |
| build/agent2/final/fsyntax.py (base) | 66C7D74022A068DA | - |
| build/agent2/final/build-final.py (base) | 5BE1F221800137BD | - |
| build/agent2/session3/commit-plan/COMMIT-PLAN.md (section 5) | D787291C9BB19AFA | - |
| build/agent10/session3/scratch-final/final2chk/blobs.py (mine, read-only git) | 609DC52934CA7185 | 2379 |

## Verdict

**CONFORMS.** All three diffs are faithful to the rated final/ method. The new parts are sound and I checked them independently: committed-blob overlay, EOL rule, 10-TU gpu leg with the include-first header, PCH reuse (B2), needles, and new DLLs in nativefinal2. Procedural conditions P1-P3 below; none needs a tool change.

## What I checked

### Diffs = tools

- `git diff --no-index --ignore-cr-at-eol final/X.py final2/X2.py` gives the same +/- lines as each submitted .diff (234 / 31 / 122 lines). So the rated diffs are the tools that will run.

### Overlay from committed blobs (prep-final2)

- Source = `git -C <live repo> -c core.autocrlf=false cat-file blob <commit>:<path>` (raw, no filters). All queries are read-only: rev-parse, diff --name-only, merge-base --is-ancestor, ls-tree, cat-file. The overlay is written only under final2/b (refuses an existing one).
- Gates: commits resolve; base is an ancestor; the name set is exact for both repos; gitlink == sdk commit; every blob has no CR; snap1 base EOL is uniform; overlay bytes == after column == final/work/new (FINAL files) or s33/s33/sdk (#33 files); snap1 before-hash; DEFAULT_OFF and q500 source lines present exactly once.
- **My own reproduction (blobs.py, read-only git):**
  - a7e79c0 resolves to a7e79c09135f...; gitlink in 2de88ce = `160000 commit a7e79c09135f...` (match).
  - `git diff --name-only 5350b1d a7e79c0` = exactly the 13 SDK paths; `c9e215f 2de88ce` = exactly rexglue-sdk + the 2 rexlego files.
  - All 15 blobs: no CR; before_ok and after_ok True. 14 bases are LF (overlay = blob). shaders.cpp base is CRLF: blob 88D8CC7F, LF->CRLF form **4B8250E9** = after column = final/work/new. So the fingerprint input equals nativefinal's (1616ce65e973c583 is re-proved by the nat FP_NEW / FP_OLD needles).
- The EOL rule is right: blobs are LF-only, so `replace(b'\n', b'\r\n')` is exact (no CR doubling), and it reproduces the autocrlf=true checkout that snap1 and the rated final/ build used.

### gpu leg: 10 TUs, include-first, B2

- I ran `ninja -t deps` on snap1-sdk build-Release.ninja (read-only). Objects depending on d3d12/pipeline_cache.h or graphics/frame_stats.h = exactly the 10 planned rexgpu-xenos.dir/Release objects. graphics/shared_memory.cpp.obj is itself one of them, so the gset check holds.
- PCH `rexgpu-xenos.dir/Release/cmake_pch.hxx.pch` (#deps 353, VALID) includes neither header. **B2: PCH reuse SAFE**, same as the devoff4b-s33 precedent (r33-nohunk5-diagd B24EE8E2).
- prep also checks snap1-on and snap1-off: no game object depends on the #33 headers. So the class layout change in pipeline_cache.h does not cross into rexlego. FINAL's SDK part changes no header.
- Include resolution: the only header include of pipeline_cache.h in snap1's include tree is `include/rex/graphics/d3d12/command_processor.h:31 #include <rex/graphics/d3d12/pipeline_cache.h>` (angle form). The overlay -I placed first (`--include-first`, gated "ahead of snap1/dimensionsrecomp/rexglue-sdk/include" in every command) therefore wins. There is no same-directory quote include that could pick up the old copy.
- All 10 gpu TUs compile the overlay source (the `leg != 'gpu'` exception). So relative "frame_stats.h" / "../frame_stats.h" includes resolve to the #33 copy, and -fmacro-prefix-map keeps __FILE__ equal; OVERLAY_RE is updated to agent2/final2/b/.
- d3d12__<name>.obj naming avoids the shared_memory.cpp / command_processor.cpp basename clash, as in prep-s33. The uniqueness check now compares full obj-on paths.
- fsyntax2: gpu set gets the same --include-first; WANT_N 8/10/1/4 = 23; OFF sets removed. Consistent.

### Needles

- gpu want: `Final defaults (GPU): {} {}` (rated), `d3d12_pipeline_creation_no_wait`, `dropped draws {} | forced pipeline waits {:.1f} ({}x)`. The last two are literally present in the committed blobs: the cvar name 1x in command_processor.cpp and 6x in pipeline_cache.cpp; the slow-frame string 1x in command_processor.cpp. `REXCVAR_DEFINE_BOOL(d3d12_pipeline_creation_no_wait, false,` is present once (default OFF).
- The want-absent-in-reference rule still applies. If either new needle were already in E3CB99CF, the leg would STOP (a safe failure, not a false PASS).

### nativefinal2 stages NEW rexruntime / rexgpu (not N-A)

- This is correct for "built from the committed source": 2de88ce's gitlink is a7e79c0, so a source build of the native game links the new SDK.
- native4b-bin and devoff4b-bin carry byte-identical old DLLs (MANIFESTs: rexruntime A33801D1, rexgpu-xenos E3CB99CF). So the swap into native4b is the same swap as into devoff4b.
- ABI: pe-check runs on every leg and requires exports NEW == REF exactly (pe-check L106-108; the rt leg has no extra allowances, and the gpu leg only allows the 2 rated added imports). So every rexruntime / rexgpu import that resolved in native4b resolves against the new DLLs. The native exe imports rexruntime.dll only (no rexgpu-xenos.dll import).
- Stage checks: TracyClient == base; each new DLL == its b/<leg>/link-on output and != the old sha; nativefinal2 copy == devfinal2-bin copy (only if devfinal2-bin exists; see P1).

### --dry-run PASS 101/0

- Not reproduced as a whole: the dry run prints to stdout and writes nothing, and I have no saved copy. Its two key gate groups (git/blob/EOL and ninja deps/PCH) I reproduced above with my own read-only checks. All pass.

## Conditions (procedural)

- **P1:** stage devfinal2 before nativefinal2 (the COMMIT-PLAN order), and confirm that the nativefinal2 stage log contains "rexruntime.dll == devfinal2-bin copy" and "rexgpu-xenos.dll == devfinal2-bin copy". The check is silently skipped if devfinal2-bin is absent.
- **P2:** keep the real prep2 output (final2/b/prep.txt) and fsyntax2 / leg logs, and record their sha in final2/BIN-PINS.md together with the 3 tool shas above. The build-final2 "tools that ran" note must show 4B20F22A / 3FC03399 / DCE13E19.
- **P3:** smoke uses `check-defaults --mode native` (new SDK DLLs) for nativefinal2, not native-old; the default-OFF runtime proof is the absence of both no_wait log lines, as section 5 states.

## Findings

- NIT N1: the nativefinal2 "== devfinal2-bin copy" check could be a hard requirement instead of `if os.path.isdir(dev2)` (P1 covers it).
- NIT N2: the prep dry run leaves no file; a `-dry` log under final2/ (outside b/) would make "101/0" auditable.
- NIT N3: prep-final2 header comment says "cmake_pch.hxx"; the deps entry is cmake_pch.hxx.pch. The code's `'cmake_pch' in o` matches it; comment only.
