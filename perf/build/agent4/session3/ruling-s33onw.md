# Ruling s33onw (Overseer, 2026-11-25 10:42)

Row 5, s33onw: no_wait ON, seeded from offsf. Run build\agent3\runs\20261125-103108-s33-onwarm. Base: s33offw, build\agent3\runs\20261125-102000-s33-offwarm.

**The literal hit:** READING-S33 L53 says "Drops long after boot -> STOP". onwarm drops 30 draws in 2 frames (#7689 and #7713), ~150 s after boot.

**Check (Overseer, s33fields reports in build\agent3\s4b\logs\):**
- s33offw (cvar OFF): `dropped draws 30 in 2 frames, last at frame 8098; late drops 0`.
- s33onw (cvar ON): `dropped draws 30 in 2 frames, last at frame 7713; late drops 0`.
- M3's frame table: 9 + 21 drops at the same route point in both arms, ~161 s vs ~150 s; that is the usual H0 drift. New pipelines are 3+8 (OFF) and 2+8 (ON). Forced waits are 0 in both.

**Reading:**
- The drops are the same in count, frame pairs and route point with the cvar OFF.
- So they come from pipelines that are not in the offsf seed, and the bin drops them regardless of no_wait. They are not no_wait pop-in.
- The purpose of L53 is to catch drops that no_wait adds late in the run. no_wait adds 0 here.
- TESTPLAN row 5's PASS wording ("same as offwarm apart from at most a few dropped draws right after the storage load") is met: the ON arm is identical to offwarm.

**Ruling:** s33onw is **PASS?**. L53 is read as "drops long after boot *beyond the OFF arm*". This must be fixed in READING-S33 after the sprint (doc only).

**Side finding for the write-up:** with a warm seed, frames >= 100 ms go from 89 (OFF) to 37 (ON), with the same 30 drops in both. The 30 drops happen whether or not no_wait is on. The row 3 eye review still gates any recommendation.
