# COMMIT-CHECK: committed perf/opt trees vs the snap4b source (Agent 2, task #28)

> **Summary (hand-written by Agent 2 at 06:16; re-running `commit-check.py` regenerates this file and drops this note): PASS.**
>
> The committed trees, DimensionsRecomp b0bd3b4 and rexglue-sdk 5350b1d, equal the snap4b source (`build/agent2/snap1`) for every tracked file in scope: 773 game files and 1347 SDK files. They match in the working tree, in HEAD and in the index. The two commits change exactly the 16 files in `build/agent2/s4b/HASHES.txt`, plus the SDK gitlink.
>
> Expected items that are not differences:
>
> - **71 out-of-scope files:** tracked files under top-level dirs that snap1 never copied (installers, docs, .github, xexdump, the mod-manager CLI). They are untouched by the commits and clean.
> - **plume and simde:** these submodules have local edits. They are ignored per the task and listed in `build/agent2/PENDING-DIFFS.md`.
> - **snap1's `rexlego/legodimensions_manifest.toml`:** the machine-local XEX manifest, gitignored by design.

- Written 2026-11-23 06:06:42 by `build/agent2/commit-check.py` (sha256 EEB4A7AC6CBA9871, `--sub stat`), read-only: git only with `--no-optional-locks` (rev-parse, config --get, ls-files, ls-tree, diff-tree, status, cat-file --batch, check-ignore).
- Reference: `build/agent2/snap1/DimensionsRecomp`, the S4b + S4c source with C1 v3 that devoff4b-bin and native4b-bin were built from. Live: `DimensionsRecomp` and `DimensionsRecomp/rexglue-sdk`.
- Per tracked file (`git ls-files`; submodule gitlinks and `generated/` skipped): (1) working tree == snap1, byte for byte; (2) HEAD blob == snap1 file (byte-identical, or after CRLF -> LF, which is what `core.autocrlf=true` commits); (3) index blob == HEAD blob.
- snap1 copied only the build inputs (top level: `.gitattributes`, `.gitignore`, `.gitmodules`, `LICENSE`, `PROJECT-HANDOFF.md`, `README-dev.md`, `README.md`, `RELEASING.md`, `VERSION`, `research`, `rexglue-sdk`, `rexlego`, `thirdparty`, `tools`). Tracked files under top-level directories it never copied are out of scope: they must exist, be untouched by the S4b/S4c commits and be clean in git status.

**RESULT: PASS** (main check). Extended checks: PASS.

## Result per repo

| repo | HEAD | core.autocrlf | ls-files entries | gitlinks skipped | generated/ skipped | out of scope (not in snap1) | files compared | working tree == snap1 | HEAD blob == snap1 | index == HEAD | git status lines (tracked) | result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DimensionsRecomp | `b0bd3b4aba5f` | true | 848 | 4 | 0 | 71 | 773 | 773 / 773 | 773 (15 exact + 758 via CRLF->LF) | 844 / 844 | 2 | PASS |
| rexglue-sdk | `5350b1de9927` | true | 1372 | 25 | 0 | 0 | 1347 | 1347 / 1347 | 1347 (1347 exact + 0 via CRLF->LF) | 1347 / 1347 | 1 | PASS |

- DimensionsRecomp pins rexglue-sdk at `5350b1de9927` (gitlink) == the SDK HEAD `5350b1de9927`: PASS.
- Symlink entries (git mode 120000) among the compared files: DimensionsRecomp 0, rexglue-sdk 0.

## Differences (files in snap1 scope)

None: every compared file is identical in the working tree, HEAD and snap1.

## The S4b/S4c commits (`git diff-tree -r HEAD^ HEAD`)

- DimensionsRecomp: HEAD `b0bd3b4aba5f`, HEAD^ `1bd322ef2442`. `diff-tree HEAD^ HEAD` changes 4 path(s): M `rexglue-sdk`, M `rexlego/CMakeLists.txt`, M `rexlego/src/gpu_native/memory_watch.cpp`, A `rexlego/src/gpu_wait_backoff.cpp`.
  - Expected from HASHES.txt (+ the rexglue-sdk gitlink): 4 path(s); missing: none; extra: none.
- rexglue-sdk: HEAD `5350b1de9927`, HEAD^ `3bb65bbd151a`. `diff-tree HEAD^ HEAD` changes 13 path(s): M `rexglue-sdk/include/rex/codegen/config.h`, M `rexglue-sdk/include/rex/graphics/d3d12/command_processor.h`, M `rexglue-sdk/include/rex/graphics/d3d12/deferred_command_list.h`, M `rexglue-sdk/include/rex/graphics/shared_memory.h`, M `rexglue-sdk/include/rex/system/xmemory.h`, M `rexglue-sdk/src/codegen/builders/system.cpp`, M `rexglue-sdk/src/codegen/config.cpp`, M `rexglue-sdk/src/graphics/d3d12/command_processor.cpp`, M `rexglue-sdk/src/graphics/d3d12/deferred_command_list.cpp`, M `rexglue-sdk/src/graphics/d3d12/shared_memory.cpp`, M `rexglue-sdk/src/graphics/primitive_processor.cpp`, M `rexglue-sdk/src/graphics/shared_memory.cpp`, M `rexglue-sdk/src/system/xmemory.cpp`.
  - Expected from HASHES.txt: 13 path(s); missing: none; extra: none.

## The 16 S4b input files (build/agent2/s4b/HASHES.txt, copied into live and committed at 05:40)

A blob matches a sha256 as stored or after LF -> CRLF (the working-tree form under core.autocrlf=true).

| owner | path under DimensionsRecomp/ | item | before sha256 | HEAD^ blob | after sha256 | HEAD blob | live | snap1 | result |
|---|---|---|---|---|---|---|---|---|---|
| A12 | `rexglue-sdk/include/rex/graphics/shared_memory.h` | C1 v3 keep-watch (#4) | 4D861738A94B556B | == | 82A66445ED98B091 | == | == | == | PASS |
| A12 | `rexglue-sdk/include/rex/system/xmemory.h` | C1 v3 keep-watch (#4) | 80100865A654AF04 | == | 5A70782EF00F0FB6 | == | == | == | PASS |
| A12 | `rexglue-sdk/src/graphics/primitive_processor.cpp` | C1 v3 keep-watch (#4) | E07F690223B564AE | == | 470BA4BED73B2ABF | == | == | == | PASS |
| A12 | `rexglue-sdk/src/graphics/shared_memory.cpp` | C1 v3 keep-watch (#4) | 0BE4BADCAC666BEE | == | A4A31038ABDFF94A | == | == | == | PASS |
| A12 | `rexglue-sdk/src/system/xmemory.cpp` | C1 v3 keep-watch (#4) | 141FB1A947D59156 | == | BCA5E1CF63686E73 | == | == | == | PASS |
| A5 | `rexglue-sdk/src/graphics/d3d12/shared_memory.cpp` | M1 non-temporal upload copy | BB0838CE3909E18A | == | 2A5ADF13B5E433F1 | == | == | == | PASS |
| A12+A7 | `rexglue-sdk/src/graphics/d3d12/command_processor.cpp` | P2 counter (memexport full-buffer counter) + #18/#20 r1r2 | 3AB3AA5360D4E987 | == | 027204B53A271D69 | == | == | == | PASS |
| A7 | `rexglue-sdk/include/rex/graphics/d3d12/command_processor.h` | #18/#20 r1r2 | 41F32B80BABA213C | == | 67F4E8380C879377 | == | == | == | PASS |
| A7 | `rexglue-sdk/include/rex/graphics/d3d12/deferred_command_list.h` | #18/#20 r1r2 | DA2F58B6CE3D7F6A | == | 9F6CC70A6922232D | == | == | == | PASS |
| A7 | `rexglue-sdk/src/graphics/d3d12/deferred_command_list.cpp` | #18/#20 r1r2 | FFDF7FB66EC81715 | == | 30FF57446EFB5D76 | == | == | == | PASS |
| A9 | `rexglue-sdk/include/rex/codegen/config.h` | #26 db16cyc_pause codegen option | D07C575FF2904B87 | == | CD39B0E110D3E0FD | == | == | == | PASS |
| A9 | `rexglue-sdk/src/codegen/config.cpp` | #26 db16cyc_pause codegen option | 0ED529B7E5F0F4E7 | == | 4706A7F22C3859D6 | == | == | == | PASS |
| A9 | `rexglue-sdk/src/codegen/builders/system.cpp` | #26 db16cyc_pause codegen option | D1269273636B5A1A | == | FAD4372074D32D69 | == | == | == | PASS |
| A12 | `rexlego/src/gpu_native/memory_watch.cpp` | C1 v3 keep-watch, rexlego file (native builds only) | 19AE1606C6DB7273 | == | 70829846C4F321A9 | == | == | == | PASS |
| A9 | `rexlego/CMakeLists.txt` | S4c 24-30 (#24 GPU wait back-off, OFF builds only; #30 option) | 3690D5D76AA9FBED | == | 1BF46D7878BA9A25 | == | == | == | PASS |
| A9 | `rexlego/src/gpu_wait_backoff.cpp` | S4c 24-30 (#24 GPU wait back-off, OFF builds only; #30 option) | ABSENT | absent | 01D9F8F3464C8614 | == | == | == | PASS |

16 of 16 rows PASS.

## Out of scope: tracked files under top-level directories snap1 never copied

71 file(s), all present in the working tree, none changed by the S4b/S4c commits (see above), and git status shows no tracked-file change: `.github/` 3, `DimensionsModManager-CLI/` 3, `docs/` 5, `native-gpu-installer/` 3, `rexlego-installer/` 54, `xexdump/` 3.

## git status (tracked files only, `--untracked-files=no`)

- DimensionsRecomp: ` M` `rexglue-sdk`: the SDK HEAD == the gitlink, so this is "modified content" inside the SDK. The SDK's own tracked status is ` M` `thirdparty/simde` (ignored per the task). Porcelain v1 shows a submodule as ` M` for new commits, modified content or (recursively) a dirty nested submodule.
- DimensionsRecomp: ` M` `thirdparty/plume`: submodule, ignored per the task (its HEAD != the gitlink; 3 tracked change(s) inside it).
- rexglue-sdk: ` M` `thirdparty/simde`: submodule, ignored per the task (its HEAD == the gitlink; 1 tracked change(s) inside it).

## Extended: submodules (live checkout vs the snap1 copy; plume/simde for information only)

`--sub stat`: equal size and mtime (within 2 s) counts as same by stat; equal size with a different mtime is byte-compared. `--sub bytes` byte-compares every file.

| submodule | gitlink | live HEAD | tracked changes | files | same (stat) | same (bytes) | differ | result |
|---|---|---|---|---|---|---|---|---|
| DimensionsRecomp:`DimensionsModManager` | 3c6f899b403a | not checked out in live (empty directory) | | snap1: absent | | | | n/a |
| DimensionsRecomp:`DimensionsSaveConverter` | 888615869ff6 | not checked out in live (empty directory) | | snap1: absent | | | | n/a |
| DimensionsRecomp:`thirdparty/plume` | ceaeeee0f7e9 | HEAD e0c8871b930d | 3 | 132 entries, 2.1 MB, 4 nested gitlinks skipped | 132 | 0 | 0 | ignored (info) |
| rexglue-sdk:`thirdparty/FFmpeg` | 0604b464c7cb | HEAD == gitlink | 0 | 7501 entries, 69.4 MB | 7501 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/FidelityFX-SDK` | eee08db1688a | HEAD == gitlink | 0 | 1785 entries, 427.1 MB | 1785 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/catch2` | 88abf9bf325c | HEAD == gitlink | 0 | 573 entries, 8.7 MB | 573 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/cli11` | bfffd37e1f80 | HEAD == gitlink | 0 | 296 entries, 1.8 MB | 296 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/fmt` | 407c905e45ad | HEAD == gitlink | 0 | 128 entries, 3.0 MB | 128 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/glslang` | f4f1d8a352ca | HEAD == gitlink | 0 | 2393 entries, 32.4 MB | 2393 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/imgui` | 6d910d5487d1 | HEAD == gitlink | 0 | 268 entries, 7.3 MB | 268 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/inja` | 7d1b4600b685 | HEAD == gitlink | 0 | 102 entries, 2.2 MB | 102 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/libmspack` | 305907723a4e | HEAD == gitlink | 0 | 319 entries, 1.2 MB, 15 symlink entries: 15 plain file with the target content in snap1 | 304 | 0 | 0 | PASS (note) |
| rexglue-sdk:`thirdparty/libusb` | a61afe5f75d9 | HEAD == gitlink | 0 | 152 entries, 1.7 MB, 1 symlink entries: 1 plain file with the target content in snap1 | 151 | 0 | 0 | PASS (note) |
| rexglue-sdk:`thirdparty/moltenvk` | db445ff2042d | HEAD == gitlink | 0 | 273 entries, 4.6 MB, 10 symlink entries: 8 absent in snap1, 2 plain file with the target content in snap1 | 263 | 0 | 0 | PASS (note) |
| rexglue-sdk:`thirdparty/o1heap` | 388a73fd9007 | HEAD == gitlink | 0 | 29 entries, 1.1 MB, 1 symlink entries: 1 plain file with the target content in snap1 | 28 | 0 | 0 | PASS (note) |
| rexglue-sdk:`thirdparty/sdl3` | 8bf3b7215ad9 | HEAD == gitlink | 0 | 2200 entries, 49.4 MB | 2200 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/simde` | 71fd833d9666 | HEAD == gitlink | 1 | 1332 entries, 53.5 MB, 1 nested gitlinks skipped | 1332 | 0 | 0 | ignored (info) |
| rexglue-sdk:`thirdparty/snapdragon-gsr` | d926f074bcb9 | not checked out in live (empty directory) | | snap1: absent | | | | n/a |
| rexglue-sdk:`thirdparty/spdlog` | 79524ddd08a4 | HEAD == gitlink | 0 | 177 entries, 1.2 MB | 177 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/spirv-headers` | 29981f652416 | HEAD == gitlink | 0 | 120 entries, 4.0 MB | 120 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/spirv-tools` | 9a49b0883b9b | HEAD == gitlink | 0 | 1743 entries, 25.8 MB | 1743 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/tomlplusplus` | 30172438cee6 | HEAD == gitlink | 0 | 212 entries, 4.4 MB | 212 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/tracy` | 05cceee0df3b | HEAD == gitlink | 0 | 413 entries, 19.1 MB | 413 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/utfcpp` | 63d64de49fd6 | HEAD == gitlink | 0 | 29 entries, 0.2 MB | 29 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/vulkan-headers` | e3b1eec08173 | HEAD == gitlink | 0 | 89 entries, 40.3 MB | 89 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/vulkan-loader` | 5f157b62e333 | HEAD == gitlink | 0 | 287 entries, 9.3 MB | 287 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/vulkan-memory-allocator` | 1d8f600fd424 | HEAD == gitlink | 0 | 266 entries, 4.0 MB | 266 | 0 | 0 | PASS |
| rexglue-sdk:`thirdparty/xxHash` | e626a72bc232 | HEAD == gitlink | 0 | 87 entries, 5.2 MB | 87 | 0 | 0 | PASS |

- Note: DimensionsRecomp:`thirdparty/plume`, ignored per the task (compared for information only): HEAD e0c8871b930d (gitlink ceaeeee0f7e9); 3 tracked change(s) in the live checkout (` M` `plume_d3d12.cpp`, ` M` `plume_d3d12.h`, ` M` `plume_vulkan.cpp`); live vs snap1: 0 of 132 entries differ.
- Note: rexglue-sdk:`thirdparty/libmspack` has 15 symlink entries (git mode 120000; real symlinks in live, core.symlinks=true): 15 plain file with the target content in snap1. The snap1 copy did not reproduce symlinks; no regular file differs.
- Note: rexglue-sdk:`thirdparty/libusb` has 1 symlink entries (git mode 120000; real symlinks in live, core.symlinks=true): 1 plain file with the target content in snap1. The snap1 copy did not reproduce symlinks; no regular file differs.
- Note: rexglue-sdk:`thirdparty/moltenvk` has 10 symlink entries (git mode 120000; real symlinks in live, core.symlinks=true): 8 absent in snap1, 2 plain file with the target content in snap1. The snap1 copy did not reproduce symlinks; no regular file differs.
- Note: rexglue-sdk:`thirdparty/o1heap` has 1 symlink entries (git mode 120000; real symlinks in live, core.symlinks=true): 1 plain file with the target content in snap1. The snap1 copy did not reproduce symlinks; no regular file differs.
- Note: rexglue-sdk:`thirdparty/simde`, ignored per the task (compared for information only): HEAD == gitlink (gitlink 71fd833d9666); 1 tracked change(s) in the live checkout (` M` `simde/x86/sse.h`); live vs snap1: 0 of 1332 entries differ.
- Not checked out in live: DimensionsRecomp:`DimensionsModManager`, DimensionsRecomp:`DimensionsSaveConverter`, rexglue-sdk:`thirdparty/snapdragon-gsr`. snap1 has no content there either (see the rows), so the S4b/S4c builds from snap1 did not use them.

## Extended: files in snap1 that live git does not track

Walk of snap1 (pruned: .git/ 1, generated/ 1, submodule checkouts 25). 74 file(s) are not tracked; 74 of them are ignored by live `.gitignore` rules (by directory: `research/dxc-1.9.2609` 33, `rexglue-sdk/out` 21, `rexlego/out` 17, `rexglue-sdk/bin` 2, `rexlego` 1).

None are neither tracked nor ignored.

RESULT: PASS; EXTENDED: PASS  (376.5 s)
