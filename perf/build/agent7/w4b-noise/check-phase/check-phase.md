# Checker 1: independent recompute of raw / T / A2 / summaries / L-ls (noise_methods.py)

## W4b: <workspace>\build\agent8\matrix\20261122-1541
- report: <workspace>\build\agent7\w4b-noise\report.json (params roll 201 heavy_ms 5.0 roll_guard_s 0.5 light_ms None all False)
- mine: ref d0, order ['d0', 'B', 'd3', 'd11t']; kept 15; left out: 1541-cold-d0 (scored False valid True excluded False n 9776), 1551-B-r2 (scored True valid False excluded False n 11723)
- sources: ['perf']; light_ms: [4.5]
- mine hT_ref 0.531229 (report 0.531229), h2_ref 0.165781 (report 0.165781)
- max |ls_T - frames.json share_lt_light| = 4.72e-05 (share_lt_light has 4 decimals); report ls_check_max_abs 4.718331149855537e-05
- item 0 selection: OK (4 comparisons; max rel 0 at -; max abs pp 0 at -)
- item 1 raw: OK (68 comparisons; max rel 2.01e-16 at 1600-d3-r3 raw.low1_fps; max abs pp 0 at -)
- item 2 T split: OK (239 comparisons; max rel 5.26e-16 at 1602-d11t-r3 t_std.low1_fps; max abs pp 0 at -)
- item 3 A2: OK (239 comparisons; max rel 3.74e-16 at 1556-d11t-r2 a2_std.low1_fps; max abs pp 0 at -)
- item 4 summaries: OK (1504 comparisons; max rel 7.21e-14 at T-light/low1_fps sd_ln; max abs pp 1.12e-13 at raw/low1_fps d3 ci_hi)
- item 5 L-ls: OK (220 comparisons; max rel 2.13e-15 at L-ls/low1_fps b; max abs pp 8.88e-14 at L-ls/low1_fps B gm_delta_pct)

## W5: <workspace>\build\agent8\matrix\20261122-1756
- report: <workspace>\build\agent7\w4b-noise\report-w5.json (params roll 201 heavy_ms 5.0 roll_guard_s 0.5 light_ms None all False)
- mine: ref base, order ['base', 's0', 'd11', 'd11t', 'd11p']; kept 15; left out: 1756-cold-base (scored False valid True excluded False n 11875)
- sources: ['perf']; light_ms: [4.5]
- mine hT_ref 0.212886 (report 0.212886), h2_ref 0.001070 (report 0.001070)
- max |ls_T - frames.json share_lt_light| = 4.44e-05 (share_lt_light has 4 decimals); report ls_check_max_abs 4.444444444440254e-05
- item 0 selection: OK (4 comparisons; max rel 0 at -; max abs pp 0 at -)
- item 1 raw: OK (64 comparisons; max rel 2.41e-16 at 1815-d11p-r2 raw.low1_fps; max abs pp 0 at -)
- item 2 T split: OK (225 comparisons; max rel 1.13e-15 at 1757-base-r1 t_std.low1_fps; max abs pp 0 at -)
- item 3 A2: OK (225 comparisons; max rel 4.9e-16 at 1804-d11t-r1 a2_std.low1_fps; max abs pp 0 at -)
- item 4 summaries: OK (1484 comparisons; max rel 5.22e-14 at T-light/low1_fps sd_ln; max abs pp 3.98e-13 at A2-heavy/low1_fps s0 ci_hi)
- item 5 L-ls: OK (248 comparisons; max rel 1.84e-14 at L-ls/fps sd_ln; max abs pp 1.22e-13 at L-ls/fps s0 ci_lo)

