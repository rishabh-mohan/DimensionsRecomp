# zpd-log: occlusion-query (ZPD) diag counters for the nops smoke (S1)

Staged, NOT built, NOT applied. Base: rexglue-sdk a7e79c0 `src/graphics/d3d12/command_processor.cpp`
(== the final2 gpu-leg overlay file). Diff: `zpd-log.diff` (+84/-0, 10 hunks). Static check: `check.py` -> `check.txt` PASS.
`check.py --compile` (fsyntax + -c, final2 gpu-leg command) is deferred until the freeze lifts.

## Purpose
M10's S1: in default mode, a draw dropped while its pipeline is pending inside a guest occlusion query
under-counts samples. The opt-in (`d3d12_async_depth_only_pipelines`) extends that drop to depth-only draws.
This diff proves per arm whether the game issues ZPD queries and whether any draw was dropped inside one.

## Cvar
`d3d12_log_occlusion_queries` (bool, default false, GPU/D3D12). Counters are always kept (plain integer
increments on the command-processor thread); only the logging is gated. With the cvar off, behaviour is HEAD.

## Log line (REXGPU_INFO)
`d3d12_occlusion_queries (<when>): frame= zpd= zpd_no_host= begun= resolved= fallback= disabled= reason='' ended_by_submission= draws_in_query= dropped_in_query_ps= dropped_in_query_no_ps=`
- when = first (first ZPD packet), disabled (right after host queries get disabled), periodic (>= 10 s), shutdown.
- dropped_in_query_no_ps > 0 = the S1 hazard was hit (depth-only draw dropped inside a query).
- dropped_in_query_ps > 0 = HEAD behaviour (async PS pipelines already drop draws in default mode).

## HEAD facts (a7e79c0)
- ZPD handler cp:436-500; Begin/EndGuestOcclusionQuery cp:5837/:5864.
- End resolves blocking: EndSubmission(false) then CheckSubmissionFence waits, so real counts are written
  and an under-count reaches the guest.
- DisableHostOcclusionQueries (cp:5819) is permanent and silent; later ZPDs get the fake 1000 samples.
- A mid-query EndSubmission ends the host query early (cp:4296); the next ZPD end finds it invalid,
  which disables host queries for the rest of the run. Pre-existing; may explain S4's held_query stuck at 1.

## Evidence so far (static, existing logs)
- Menus: ZPD proven. agent3 S4 split runs on b-gate-menus-long (`20261125-085516-r19r11-s4b11-split16`,
  `20261125-093349-r19j-async-16`) show held_query 0->1 near frames ~5000-5600, then 1 to the end.
- Title (`20261125-030425-s4b-N4-title-split4`) and level soak (`20261125-094615-r19e-level-soak-async-n`): 0.
- Attract: unproven (no split/held_query logging was ever on in attract-long). held_query is a lower bound only.

## Bin implication
A test bin with zpd-log changes 2 gpu-leg TUs (stacked pipeline_cache.cpp + this command_processor.cpp);
it needs its own M10 rating. If rejected, run the kit with `nozpd` (single-TU nops bin).
