# Rating: M12 run_gates.py `<run>` env expansion (runexp) - M10, 2026-11-25 06:44

Who/when: M10 (successor of Agent 10), read-only, at the Overseer's request (12:35Z). This rating comes after install: HASHES.txt records "06:35 (Overseer go)".

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent12/session3/run_gates-runexp.diff | 17740F27A496C0A8 | 4309 (CRLF, 71 lines) |
| build/agent12/w6-gates/run_gates.py (live) | 0F7C7B97780A8687 | 96171 |
| build/agent12/w6-gates/run_gates.py.pre-runexp (backup) | BD51120207017D27 | 94030 |
| build/agent12/w6-gates/HASHES.txt | 25244662BD5170B4 | 6000 |

Base: the backup BD511202, which is the previously gated run_gates.py.

## Verdict

**SAFE.** The change only widens G9's env comparison, for arm values that contain `<run>`. I found no way for it to PASS a run whose env path points anywhere other than its own run dir. Plain env values are compared exactly, as before.

## What I checked

1. **The diff reproduces the live file.**
   - The diff file is CRLF, while run_gates.py is LF, so `git apply` fails on the diff as stored.
   - With the line endings normalised to LF, it applies cleanly to a copy of the backup and gives exactly 0F7C7B97.
   - difflib live vs backup: +37 / -2, matching the 4 hunks.
2. **Logic (`env_match`, L211-226; G9 call site, L1011-1016):**
   - The key sets must be equal. env_norm upper-cases keys and lower-cases only true/false values, so paths keep their case.
   - For a value containing `<run>`: the token is replaced through a function, so backslashes in the dir are not treated as regex escapes. The result is compared with `normcase(normpath())`.
     - Case, slash style, a trailing slash and `..` segments all resolve to the real path.
     - A path into another run's dir fails; `..` into another dir also fails, because normpath resolves to that other dir.
     - With no run dir it fails.
   - Other values: exact string compare (unchanged).
   - `run_dir` is the dir that run.json is read from (L533-552). The comparison therefore proves "env_set names this run's own dir", which is what the runner promises.
3. **Selftest:** I ran `run_gates.py --selftest` at BelowNormal with TEMP set to my scratch dir. Result 59/59 PASS, including the 5 new `<run>` checks (own dir, another dir, no dir, missing key, plain exact). The temp dir was empty afterwards.
4. **Re-gate output:** I compared the GATES lines in night/ vs night/runexp/ for the 5 windows. They are identical for WC1, WC2, WC3 and W10. W8a changes only G9 FAIL -> PASS (exit 1 -> 3, G10 CHECK remains). This matches M12's claim.

## Findings

- **NIT 1:** the diff is stored with CRLF, so it doesn't `git apply` against the LF file as stored. Keep it as a record, or regenerate it with LF.
- **NIT 2:** G9 now proves that the path is the run's own dir, but not that the file exists. For W8a, M12's hand check found native-frames.csv in all 15 runs. An `os.path.exists` NOTE would make that mechanical.
- **NIT 3:** if a matrix dir has been moved, L534-536 falls back to `<mdir>/runs/<name>`. A `<run>` value recorded with the old absolute path then FAILs. This is a false FAIL, the safe direction. Worth one line in W6-GATES.md.
- **INFO:** w6_kit.py still does not expand `<run>`. Any arm with a `<run>` env (the native frame-metrics arms) keeps a kit-side FAIL that needs the same hand check, until the kit gets the same helper.

## Conditions

None for use. The W8a mechanical G9 PASS from the runexp re-gate may replace the hand override in the night records. My read-out cross-check (readout-night-xcheck.md, 25BF9B1C) is unaffected either way.

## Read / sent

- Scratch: build/agent10/session3/scratch-runexp/ (the patched copy = 0F7C7B97, and the selftest output; the LF-normalised diff was deleted after use).
- Sent to the Overseer after writing.
