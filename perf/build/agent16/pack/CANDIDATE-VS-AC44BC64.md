# Pack fix candidate: placement VS 0xAC44BC64 (prefix 0x5BB4C8029EB256F2)

Status: CANDIDATE only. No dump, no build, no repin (Overseer 02:16Z).

## Evidence

M3's gameplay run 20261125-195926 on native4bp (fingerprint 39129c4c059be5f0):

- game.log L1348: `placement vertex shader 0xAC44BC64 backing 0xED23CE20 prefix=0x5BB4C8029EB256F2 words=F0554003 00001200 C2000000 00001007 missing from AOT index`.
- trace: `shader_miss_cache_insert stage=6 guest=2890185828 physical=3978546720 span=16 prefix=6608126466837337842`.
- 155,649 `draw_missing_vertex_shader` events in 15,475 of 35,769 frames.
- The first miss is at frame 4771 (t 84.96 s), about 1 s after mark m03, on a 59-draw menu frame.

## Scope

Full trace pass (scratch miss_screens.py, 20:43):

- Phase A, menus m03-m09 plus the story-load/loading screens (t 85-257 s): 1 missing draw per frame, in bursts of ~155 frames (2.6 s) every ~5.8 s. That looks like a periodic animated UI element.
- In-between screens (vortex, o-01..o-12, p01-p02; t 267-437 s): 0.
- Phase B, the main menu and its sub-screens (p03-b → end, t 438-663 s, 157-183 draws per frame): 14-16 missing draws on almost every frame. p09-hold-a: 1 per frame, on a 9-draw screen.

- It is not one of the 2 excluded root dumps: memexport VS A58EBA123EFB541C and non-placement PS 93B9F93B535E7CCA.
- The window/attract-long route never draws it. All 5 window n4bp60 game.logs have 0 `missing from AOT index` lines.
- nat60 misses only the 2 prefixes that the pack fixed (C77B3ABB6F87ACD9, DCD4AD8441398283).

## Fix path (when approved)

1. Dump the VS on M3's route (Toypad/menu → story-load). This is the same 0.4a dump flow, with the backing container at physical 0xED23CE20, span 16.
2. Add it to the placement pack (0.4b tool), rebuild native4bp-bin → a new MANIFEST, and run verify-bins.
3. Repin every kit that pins the native4bp MANIFEST: currently C5181520…A690, used by natcmp, rows/ab and the window script. Each repin needs an M10 re-rate.
4. Validate: rerun M3's gameplay route → missing draws 0, and run the refonly smoke.
