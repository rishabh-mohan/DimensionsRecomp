# BUILD-PLANS (M2, session 3, S3T-2)

Limits (Overseer LOAD GO 11-25 01:26): one build at a time, max 2 threads, Idle priority for every compiler / linker /
codegen process, no game runs. All commands run from the WS root in PowerShell with the shell itself at Idle:

```
if (Test-Path perf-notes\WINDOW-HOLD.txt) { 'HOLD'; exit 9 }; (Get-Process -Id $PID).PriorityClass = 'Idle'; <cmd>; "exit $LASTEXITCODE"
```

Script changes (backups `*.pre-S3`): `recompile.py`, `relink.py`, `holdrun.py` start children at Idle by default
(`--priority`); `relink.py --link-flag "-Xlinker /threads:2"` (lld otherwise uses every core); `recompile.py
--include-first DIR` (overlay headers); `cg26/cg26-check.py` accepts a depfile whose prerequisite ORDER differs (set
compare, logged as a NOTE in the report).

## (a) CG26 -> build/agent2/devoff4b-cg26-bin

1. Delete `build/agent2/cg26/DimensionsRecomp/rexlego/generated/default/codegen.stamp`.
2. `python build\agent2\holdrun.py --priority idle --cwd build\agent2\cg26\DimensionsRecomp\rexlego --log build\agent2\cg26\codegen.log -- <R>\build\agent2\cg26\tool\rexglue.exe codegen legodimensions_manifest.toml` (single thread; 142 s).
3. `python build\agent2\cg26\cg26-check.py --out build\agent2\cg26\checks\gates-<HHMM>.txt --stage`
4. `python build\agent2\recompile.py --ccdb build\agent2\snap1-off\compile_commands.json --list build\agent2\cg26\list-ctl.tsv --jobs 2 --log-dir build\agent2\cg26\log-ctl`, then `list-on.tsv` / `log-on`.
5. `python build\agent2\relink.py --ninja build\agent2\snap1-off\build.ninja --target legodimensions.exe --out-dir build\agent2\cg26\link-ctl --replace-file build\agent2\cg26\replace-ctl.txt --link-flag "-Xlinker /threads:2" --compare build\agent2\snap1-off\legodimensions.exe --compare-map build\agent2\snap1-off\legodimensions.map`, then `replace-on.txt` / `link-on` without the compares.
6. `python build\agent2\s4b\mapcheck-s4c.py --map build\agent2\cg26\link-on\legodimensions.map --ref build\agent2\devoff4b-bin\legodimensions.map --mode same --out build\agent2\cg26\checks\mapcheck-cg26.txt`
7. `python build\agent2\cg26\stage-cg26.py --dry-run`, then without `--dry-run`.
8. Agent 9's static kit (no game run): `build\agent9\cg26-check\README.md` L12 command, `--out build\agent2\cg26\checks\kit18`.

## (b) CTR -> build/agent2/devoff4b-ctr-bin

1. `python build\agent2\recompile.py --ccdb build\agent2\snap1-sdk\compile_commands.json --list build\agent2\ctr\list-ctl.tsv --obj-filter /Release/ --jobs 2 --log-dir build\agent2\ctr\log-ctl`; then `list-on.tsv --define REX_D3D12_DEFERRED_COUNTERS=1 --log-dir build\agent2\ctr\log-on`.
2. `python build\agent2\relink.py --ninja build\agent2\snap1-sdk\build-Release.ninja --target <R>/build/agent2/snap1/DimensionsRecomp/rexglue-sdk/out/win-amd64/Release/rexgpu-xenos.dll --out-dir build\agent2\ctr\link-ctl --replace src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/d3d12/deferred_command_list.cpp.obj=build\agent2\ctr\obj-ctl\deferred_command_list.cpp.obj --link-flag "-Xlinker /threads:2" --compare build\agent2\devoff4b-bin\rexgpu-xenos.dll`; then `obj-on` / `link-on` without `--compare`.
3. String check: ON DLL contains `deferred_counters:`, control does not.
4. `python build\agent2\stage-variant.py --base build\agent2\devoff4b-bin --out build\agent2\devoff4b-ctr-bin --replace rexgpu-xenos.dll=build\agent2\ctr\link-on\rexgpu-xenos.dll --title "..."` (dry run first).

## (c) #33 first test bin (no hunk #5) -> build/agent2/devoff4b-s33-bin

Only `rexgpu-xenos.dll` changes (`session3/deps-s33.txt`: the game includes no rex/graphics headers). snap1 and
snap1-sdk are not modified: the patch goes into an overlay copy.

1. `python build\agent2\session3\prep-s33.py --patch <patch> --sha <sha256> --tag <tag>` -> `build/agent2/s33/<tag>/`
   (overlay `sdk/` = snap1 `src/graphics` + the patched include headers; `git -c core.autocrlf=false apply`; 10
   affected objects from `ninja -t deps`; list/replace files).
2. Recompile CTL (snap1 sources) and ON (overlay sources + `--include-first build\agent2\s33\<tag>\sdk\include`), both with snap1-sdk's ccdb, `--obj-filter /Release/ --jobs 2`.
3. Relink CTL with `--replace-file replace-ctl.txt --compare build\agent2\devoff4b-bin\rexgpu-xenos.dll` (must be equal except timestamps: proves the overlay method), then ON.
4. String check: ON DLL contains `d3d12_pipeline_creation_no_wait`, control does not.
5. `stage-variant.py --base build\agent2\devoff4b-bin --out build\agent2\devoff4b-s33-bin --replace rexgpu-xenos.dll=...link-on\rexgpu-xenos.dll` (cvar default false, kRequiresRestart).

## Not planned yet

- #19: waits for M10's rating.
