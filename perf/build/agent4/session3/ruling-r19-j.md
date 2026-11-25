# Ruling r19-j (Overseer, 2026-11-25 09:39)

Row r19j (async ON, split 16 KB, --row j --n 16). Run: build\agent3\runs\20261125-093349-r19j-async-16. Base: r19r11 (20261125-085516-r19r11-s4b11-split16).

M3 flagged the largest scene-id drift so far. At its marks, r19j sits on menu/title ids (220/534 at both after-a3 and down-1), while the base r19r11 had gone one screen ahead into gameplay.

**Check (Overseer, perf.csv load profile, whole run):**

| run | frames | draw_calls median | p90 | max | frames >1500 dc | vertices p90 |
|---|---|---|---|---|---|---|
| r19j | 10140 | 226 | 4385 | 16015 | 21% | 821397 |
| r19r11 | 9727 | 226 | 4379 | 12970 | 26% | 1082825 |

**Reading:**
- The run reached the same heavy-scene load class as the base: the same median and p90 draw calls, and a higher max.
- The mark drift is a sampling artifact of the fixed-sleep route (see ruling-r19-d). It is not missing coverage.
- The split/async evidence comes from real load: chunks 67826 and full_waits 1126 > 0 (J1).

**Ruling:** r19j is **PASS?** under ruling-r19-d. r19-ok-j stands. The drift ids are stated in M3's report and M12's entry.
