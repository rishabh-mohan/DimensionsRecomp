# zpd-log v2 delta (M10 finding S1 SHOULD: count every disable path)

v1: zpd-log.diff 2FB24916EA354EC0 (+84/-0, 10 hunks), ov DF84086FFD101A4B (rated SAFE, zpd-log-rating.md 68813034).
v2: zpd-log.diff 5CAD04BBCDF20ED3 (+86/-0, 12 hunks), ov 6DE509E3FB683A2E. check.py static PASS (18:34, before quiet mode).

## Changes (ov = a7e79c0 + diff, LF)
1. `++occlusion_query_log.disabled;` removed from the three ZPD-handler sites ("no sample count memory",
   "begin at another address while one is active", "end at another address" / "end without an active query").
   Those sites still set `occlusion_query_log.disable_reason` just before calling DisableHostOcclusionQueries().
2. `DisableHostOcclusionQueries()` now counts at the top of its body (no header change, same signature):
   ```
   // Every disable path counts here; the caller sets disable_reason first.
   if (occlusion_query_resources_available_) {
     ++occlusion_query_log.disabled;
   }
   ```
   The guard counts only a real disable (resources were available); host queries can't come back on, so this is at most once per run.
   ShutdownOcclusionQueryResources() also calls it, but that is after the "shutdown" log line, so the logged counts are unaffected.
3. BeginGuestOcclusionQuery's "begin while another query is active" path (ov L5928-5931, after the existing REXGPU_WARN) now sets
   `occlusion_query_log.disable_reason = "begin while another query is active";` before its DisableHostOcclusionQueries() call.
   It is called from the ZPD handler, so OcclusionQueryPacketScope sees `disabled` change and logs the "disabled" line.
4. Struct comment: `disabled` = "host queries disabled (DisableHostOcclusionQueries)".

## Behaviour
Still add-only. With the cvar off, the only difference from v1 is where one uint64 increment happens, plus one const-char* store on the
begin-while-active path. Query, draw and submission semantics are unchanged.

## Post (nops_smoke_post.py) changes for Z4/Z5
- Z4: "shutdown line once" is now a gate (was a note). No "first" line means the verdict "no ZPD on this route: proves nothing".
- Z5 verdict:
  - `S1 CONFIRMED` if dropped_in_query_no_ps > 0;
  - `valid 0` only if begun > 0, resolved > 0, the first disable came at or after half the ZPDs (or never), and the host fraction
    (zpd - zpd_no_host)/zpd is at least 0.5;
  - otherwise `0 NOT valid`.
  - PS-only drops are appended as "HEAD behaviour".
- The pair report prints each arm's S1 verdict.
- synth_post.py has new Z4/Z5 cases. They have NOT been run yet: quiet mode, no python.
