# CG26 check kit (Agent 9, run-2 task #18)

`cg26_check.py` is an independent, read-only static check of Agent 2's **CG26** regen and its staged bin (#26,
`db16cyc_pause` ON, arm A). Agent 10 can use it for the static gates of b2r row 37 (S36). It uses only the Python
standard library and one thread. It reads both trees (~1 GB) and writes only under `--out`.

## Command for CG26 (after Agent 2's regen, recompile, relink and staging)

Run it from the workspace root, at below-normal priority, while no window is running (one line, PowerShell):

```
if (Test-Path perf-notes\WINDOW-HOLD.txt) { 'HOLD'; exit 1 }; (Get-Process -Id $PID).PriorityClass = 'BelowNormal'; python build\agent9\cg26-check\cg26_check.py --arm A --gen build\agent2\cg26\DimensionsRecomp\rexlego\generated --ref build\agent2\snap1\DimensionsRecomp\rexlego\generated --config build\agent2\cg26\DimensionsRecomp\rexlego\legodimensions_config.toml --tool build\agent2\cg26\tool\rexglue.exe --tool-sha 9145166CDBEF5500E6E2607ED80AA6FC94CA1772DE2D3E87FF9E13BEAD87D586 --bin build\agent2\devoff4b-cg26-bin --out build\agent10\cg26-check; "exit $LASTEXITCODE"
```

- The shell drops itself to Below Normal, and python inherits that (0x4000, tested 22:54). Don't wrap the command in
  `cmd /c start "" /belownormal /wait /b`, because that always reports exit 0 (tested 22:54). The `RESULT` line and
  report.txt are right either way.
- `--out` can be any new dir. The example uses one under build/agent10 for Agent 10's run.
- `--tool-sha` pins the tool Agent 2 staged in `cg26/tool` (22:15). If that tool is replaced on purpose, drop `--tool-sha`. The
  marker check still makes sure the tool has the option.
- The bin path, the MANIFEST format and the relink method are from Agent 2 (22:28). The bin is the devoff4b-bin base
  with the exe and map from the relink: `recompile.py` builds cg26/tu, then `relink.py --replace-file cg26/replace-on.txt`.
- Time: about 2.5 min cold and about 10 s warm on this laptop under build load (the tests below).

**Exit codes:**

| Exit | RESULT line | Meaning |
|---|---|---|
| 0 | `RESULT: PASS` | All gates pass. |
| 1 | `RESULT: FAIL (n)` | n checks failed. |
| 2 | `RESULT: INCOMPLETE (n skipped)` | `--tool` or `--bin` was not given, or a usage error. |
| 3 | `HOLD: ...` | The stop file exists or appeared during the run. Nothing is written; run it again after the window. |

- The stop file is `--hold`. The default is `perf-notes/WINDOW-HOLD.txt` in this workspace, resolved from the
  script's own path. It is checked on every file read and on every MiB hashed. `--hold none` turns it off.

**Outputs in `--out`:**
- `report.txt`: every check as PASS, FAIL, NOTE or SKIP, in the sections `== (a)` to `== (d)`, then the `RESULT` line.
- `diff-summary.md`, the generated-diff summary for Agent 10:
  - a per-TU table (pauses expected and inserted, db16cyc sites without a pause, whether the rest is identical, line
    counts, ref and gen sha256);
  - a per-site table (TU, function, label, gen line, the ref line of the db16cyc comment, placement);
  - the context of each pause (3 lines before it, 1 after);
  - the other differing files, and the first unexpected hunk of each file that differs in other ways.
- `sites.tsv`: the per-site table as TSV.

## Gates

**(a) The toml line and the new codegen tool are in the same build:**
- the config toml has exactly one root-level `db16cyc_pause = true` (before the first `[table]`);
- without that line, the toml is the arm-A base toml `7F775847…`. A NOTE says whether it equals the staged new-A toml
  `11707872…`;
- `codegen.d` names a `*_config.toml` with the same content;
- `codegen.stamp` is a version-1 stamp with a 32-hex fingerprint, and `codegen.build.stamp` == that fingerprint (one
  regen wrote both);
- the fingerprint differs from the reference's;
- the stamp lists the same outputs as the reference, and every output exists;
- `codegen.stamp` is newer than the toml (the regen ran after the line landed);
- the tool contains the option strings `db16cyc_pause` and `\tsimde_mm_pause();`. With `--tool-sha`, the tool sha256
  must match too. A tool newer than the stamp is only a NOTE;
- the regen emitted all 20 pauses. With 0, an ADVICE NOTE says to force one regen: delete `codegen.stamp` (or pass
  `--ignore-stamp`), then regen with the new tool. Touching the toml does not force a regen. The fingerprint hashes the
  contents of the inputs (XEX, manifest, tomls, templates), not their paths or mtimes (Agent 2, `output_stamp.cpp:67-99`).
  So a bare touch of the toml after the regen also fails the "newer than the toml" check above. If that happens,
  compare the toml sha256 with the MANIFEST note;
- the staged `legodimensions.exe` is newer than the newest of the 10 regenerated TUs;
- a NOTE says whether the bin MANIFEST names the tool sha256, the toml sha256 and the 10 ON TU sha256s.

**(b) The 20 pause sites:**
- the reference has exactly the R2.17 db16cyc sites (8, 2, 2, 2 and six 1s in the 10 arm-A TUs) and no `_mm_pause`
  text;
- gen has the same db16cyc comment lines per TU;
- there are exactly 20 lines that are exactly `\tsimde_mm_pause();`, and no other `_mm_pause` text anywhere in gen;
- no pause is outside the 10 TUs, and each is in its expected function and TU;
- each pause directly follows a `\t// db16cyc ` line;
- the per-function counts match R2.17;
- per TU, a lockstep walk shows that only pause lines were inserted, that each TU minus its pauses is byte-identical
  to the reference, and that no db16cyc site lacks a pause.

**(c) `codegen.partition.json` is unchanged:**
- same file list as the reference;
- no file differs except the 10 TUs, `codegen.stamp`, `codegen.build.stamp` and `codegen.d`;
- the partition sha256 equals the reference's and starts with the arm-A sidecar prefix `22C9D89BEA8E8C6E`;
- `sources.cmake`, `legodimensions_funcs.h`, the init/register/pch files and every `.h` file are unchanged.

**(d) The MANIFEST hashes match:**
- the MANIFEST (`MANIFEST*` in `--bin`, or `--manifest`) has hash rows. It accepts the `stage-variant.py` /
  nativeB-bin rows (`name<TAB>size<TAB>mtime<TAB>sha256<TAB>source`), sha256sum lines, or one hash plus one staged
  file name per line;
- each listed file is re-hashed, and its sha256 and size must match;
- unlisted staged files are a NOTE. The MANIFEST `source` of the exe and the map is printed as a NOTE.

**The expected sites (R2.17, arm A):**

| TU | function | pauses |
|---|---|---|
| 107 | sub_83FAF180 | 8 |
| 116 | sub_83F99F80 | 2 |
| 205 | sub_83FCB608 | 2 |
| 321 | sub_83F9A5B0 | 2 |
| 125 | sub_83E64900 | 1 |
| 153 | sub_83EA90D0 | 1 |
| 169 | sub_83E66CD8 | 1 |
| 284 | sub_83E70320 | 1 |
| 304 | sub_83E96348 | 1 |
| 432 | sub_83E63F38 | 1 |

Arm B is built in too (`--arm B`: TUs 383, 107, 354, 389, 162, 265, 281, 329, 378, 394; partition prefix
`9DADABCC6F543432`; base toml `E60EAF1C…`).

**Not covered here:** the control relink (`cg26/link-ctl`, the 10 pinned TUs relinked and compared with snap1-off's
exe and map, identical except timestamps). Agent 2 keeps it as evidence.

## Tests (no regen, no build, no game run)

```
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'; python build\agent9\cg26-check\test_cg26_check.py [--keep-mock] [--reuse-mock] [--only P0,F4]; "exit $LASTEXITCODE"
```

`test_cg26_check.py` builds `mock/` in this folder:
- a copy of the pinned A tree, with `\tsimde_mm_pause();` inserted after each db16cyc line of the 10 TUs, which is what
  the staged `build_db16cyc` does;
- a mock stamp, build stamp and `codegen.d`;
- the staged new-A toml;
- a 3-file mock bin with a MANIFEST in the stage-variant format.

Then it runs the checker once per case:

| Case | What it does | Expected exit | Expected failing gates |
|---|---|---|---|
| P0 | the mock as built | 0 | none |
| F1 | Agent 2's real cg26 tree before the regen, with the real nativeB-bin MANIFEST | 1 | ab |
| F2 | TU116 missing a pause | 1 | ab |
| F3 | an extra pause in TU108 | 1 | abc |
| F4 | the TU125 pause moved down one line | 1 | b |
| F5 | one byte appended to the partition | 1 | c |
| F6 | one exe byte flipped | 1 | d |
| F7 | the old tool | 1 | a |
| F8 | the base-A toml | 1 | a |
| F9 | the stamp older than the toml | 1 | a |
| F10 | a non-pause edit in TU205 | 1 | b |
| F11 | a wrong build stamp | 1 | a |
| I1 | no `--bin` | 2 | none |
| H1 | a stop file present | 3 | none, and no report |

- Mutations change content only (each keeps the file's mtime), and each is restored after its case.
- The test checks the real stop file before and during the mock build, before every case, and every second while a
  case runs. If it appears, the test kills the checker, restores the mutation, keeps the mock and exits 3. Resume
  with `--reuse-mock --only <ids>`.
- Logs: `test-<tag>.txt`, with per-case reports in `test-<tag>/<id>/`.

**Results:**
- **Run 2** (22:37, checker `A179EB13`, test `40339E02`): **ALL OK, 14 of 14**. The mock built in 68.0 s and P0
  passed in 15.1 s. Log: `test-20261122-223737.txt`, with per-case reports in `test-20261122-223737/<id>/`.
- **Run 1** (22:26) found a test artifact in F4, now fixed: mutations keep the file's mtime.
- Both runs are in perf-notes/agent9-codegen.md R2.18.3. `mock/` was deleted after run 2; the test rebuilds it.
