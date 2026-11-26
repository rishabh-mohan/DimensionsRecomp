# Title-gate candidate: evidence (M3)

Diff: build/agent3/gameplay/kit.dump-to-titlegate.diff (base = dump kit, ps1 D97C9228)

## FE state 12 (title) -> START accepted (state 13)

| Run | Input | Delay after fe(12) | Result |
|---|---|---|---|
| EXPLORE2 031601 | route pad START | +3.8 s (03:20:08) | ignored |
| EXPLORE2 031601 | probe pad START | +1067 s (03:37:52) | accepted |
| 195931 | route pad START | +176 s | accepted |
| manual 204323 | keyboard Enter (key=13) | +28.6 s | accepted |
| manual 024219 | keyboard Enter (key=13) | +53 s | accepted |

- 03:20-03:37 (EXPLORE2): pad_active_reads keeps rising through the window, so the vpad is
  being polled while the title ignores START. The only other inputs sent were A/B/stick, which
  the title ignores (gen L82).
- game.log between fe(12) and acceptance has only pipeline-cache saves and upload-pool stats.
  No attract/intro end, save/profile or storage-device event, so there is nothing to gate on.
  Hence a bounded retry loop.

## Button behaviour by state

- START on the Updates panel (state 0): no effect (195931 20:07:07).
- B at 13 -> 35/8/11/17/0 (EXPLORE2 03:37:58); A at 13 takes the same path.
- B on the Updates panel before the Store notice: no effect (204323 20:48:19).
- A/B at the title: no effect.
- START at 13: UNKNOWN. The B converge step after the loop makes the route correct either way.

## Gate design (M10 requirements)

- sleep 12, then fixed N=6 tries of: press START + wait_log "current=13 pending=4294967295" 10.
- Then press B (converge to the Updates panel), sleep 4, press A,
  wait_log "current=5 pending=0" 20  # TITLE GATE CHECK: TIMEOUT = the title never took START.
- Worst-case bound ~80 s. Pad input only (vpad), as now.
- Fail-hard limit: vpadhost.cs has no branching or conditional stop; a wait_log timeout moves on.
  The gate check is a >=20 s long wait, so its TIMEOUT shows up as a FAIL in the post, with the
  marks title / press-start / updates-panel. A true early abort needs a harness change (not M3's file).
