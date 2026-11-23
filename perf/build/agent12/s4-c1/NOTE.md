# S4 C1: `physical_protect_keep_watch` (Agent 12, task #31, taking over Agent 5's #28)

Staged 2026-11-22 07:45-07:55. Not applied, not built. Design, hashes, checks, the §21 -> patch map, OFF identity, residuals, gates and test plan: `perf-notes/agent12-io-memory.md` section **S4.12**.

- `keep-watch.diff` (SDK, apply in `DimensionsRecomp/rexglue-sdk`): 1B2BA4E30BC05A1E7157B50DBC90BC819C93E4B16B419BAFE7E62CCF11A4AB70
- `keep-watch-rexlego.diff` (game, apply in `DimensionsRecomp`): 4D0C10794188CF450046D42B249C9C46D009EE9F4F1B82116954857FA70838BD
- `chain-live-to-c1.diff` (reference: diag + P2 + fix (i) + C1 as one diff on the live SDK): 1D2CC1F3A3845A3F8FA22BC9ABB5F2B77203E89A734D06884278BB75B0C07616
- Apply order: `build/agent12/s4-diag/upload-hash-log.diff` -> `build/agent12/s4-p2/single-hold-rearm.diff` -> `build/agent12/s4-fixi/protect-hold-g.diff` -> `keep-watch.diff`; then `keep-watch-rexlego.diff`.
- All switches default OFF. C1 engages only with fix (i) on (`--physical_protect_hold_global_lock=true --physical_protect_keep_watch=true`). Verify mode: `--physical_protect_keep_watch_verify=true`, set at launch.
- Re-run the checks: `python build\agent12\s4-c1\c1_mkdiff.py` (bases, diffs, apply checks, 4-step chain; rewrites `HASHES.txt`), then `cmd /c start "" /belownormal /wait /b powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent12\s4c1_syntax.ps1`.
- Results at staging: RESULT PASS for both (`HASHES.txt` 07:51, `syntax-20261122-075428.txt`).
- `make_c1.py` regenerates `new/` from `orig/`. If any base moves, re-stage with it; don't hand-edit `new/`.
- Builds only by Agent 2, after the user OKs the S4 plan. Agent 10 rates it in S4.
