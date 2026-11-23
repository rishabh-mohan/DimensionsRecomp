# Re-pinned build-B tools for a rollback build (recipe step 9)

Written by `build/agent9/make-repin.py` at 02:39:12. Agent 2 owns `prep-b.py` and `run-b.ps1`; these copies are a
proposal for after a B failure and Agent 1's GO. They were made from `build/agent2/prep-b.py` sha256 `C0067F18` and
`build/agent2/run-b.ps1` sha256 `0D159651`. If either has changed since, rerun the script (it stops on any pin it
cannot match exactly once).

| Tree | Recipe step | Drops | `SHA256SUMS.txt` sha256 | Entries | Config sha256 | TUs (last) | Gate |
|---|---|---|---|---|---|---|---|
| `batch-nolr` (B, current) | - | - | `24CE1493FB8DAE37E00B556EB8871D633921E44378D960DE4359B104B16CDB8E` | 872 | `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` | 430 (`legodimensions_recomp.429.cpp`) | 432 |
| `rb1-nolocal` | 9.1 | ctr_as_local, xer_as_local, reserved_as_local, cr_as_local, cr_compare_so_zero | `A966CF18E3EC736F5685CA413A93C7E97B436547560E285894D43D4E1A9ED917` | 880 | `AE9F8F967FBB264919A63463CA4958F856C18A0405A4895440D6C36A31084EEC` | 434 (`legodimensions_recomp.433.cpp`) | 436 |
| `rb2-nomusttail` | 9.2 | musttail_calls | `8BDE87171405EC9611B89CD75BADC400DD93BC371CFBA3634B7B446FCF9D7B14` | 870 | `FC034D495DAC395F45CDC0AC0DC7BFD88C8D2046A09590B88563B63BE1C82924` | 429 (`legodimensions_recomp.428.cpp`) | 431 |

Each tree passed prep-b.py's step-1 checks again (this script): END line parsed, every file hash-matches
`SHA256SUMS.txt`, config == `configs/<tree>.toml` == END line, `rexglue.cmake` and `codegen.d` == baseline's,
and the `sources.cmake` TU count matches.

## What changes

- `prep-b.py`: `VARIANT`, `SUMS_SHA`, `CFG_SHA`, the entry count (2 places) and the `--install` help text.
- `run-b.ps1`: the `-Install` default, `$nolr`, the two pins (and their STOP messages), `$what` and `$cgNote`.
- Not changed: `-Out` (default `devoffB-bin`, the name in Agent 8's matrices). To keep the failed B, pass
  another `-Out` and change `b-chain.ps1`'s `devoffB-bin` hash lines to match.

## Use (Agent 2, after Agent 1's GO)

1. Review `build/agent9/repin/<tree>/prep-b.py.diff` and `run-b.ps1.diff`, then copy the two files over
   `build/agent2/` (or apply the same edits by hand).
2. `python build\agent2\prep-b.py --skip-copy`: keeps the snapB copy, re-checks it and redoes step 4.
   Step 4's robocopy /MIR also deletes TUs the tree no longer has (rb2 has no `.429.cpp`).
3. Run `run-b.ps1` as for B, with its fresh OFF configure: the TU count changes, and almost every TU
   recompiles anyway. The gate is then TUs + 2 (table above).

| Tree | `prep-b.py` copy sha256 | `run-b.ps1` copy sha256 |
|---|---|---|
| `rb1-nolocal` | `392748EA2A1D969E` | `68A9BEF7D0F1F1C8` |
| `rb2-nomusttail` | `AE352887A3968096` | `DC03630FBA10347B` |
