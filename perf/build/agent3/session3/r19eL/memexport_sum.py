"""r19eL PASS condition 5: sum `memexport syncs N (K KB)` over every slow-frame
line in all game*.log files of a run dir (rotated logs included).

usage: python memexport_sum.py <run_dir>
exit 0 = syncs > 0 and KB > 0 (condition 5 met); 3 = zero (HOLD, ask); 2 = no logs / no slow-frame lines.
"""
import glob
import os
import re
import sys

SLOW = re.compile(r"slow frame #\d+:")
SYNC = re.compile(r"memexport syncs (\d+) \((\d+) KB\)")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = sys.argv[1]
    logs = sorted(glob.glob(os.path.join(run, "game*.log")))
    if not logs:
        print(f"NO LOGS in {run}")
        return 2
    lines = frames = syncs = kb = nosync = 0
    for p in logs:
        n = 0
        with open(p, encoding="utf-8", errors="replace") as f:
            for ln in f:
                if not SLOW.search(ln):
                    continue
                n += 1
                m = SYNC.search(ln)
                if not m:
                    nosync += 1
                    continue
                c, k = int(m.group(1)), int(m.group(2))
                if c > 0:
                    frames += 1
                syncs += c
                kb += k
        lines += n
        print(f"log {os.path.basename(p)}: {n} slow-frame lines")
    print(f"slow-frame lines {lines}; lines without a syncs field {nosync}")
    print(f"memexport syncs: frames>0 {frames}, sum {syncs}, KB {kb}")
    if lines == 0:
        print("RESULT: NO SLOW-FRAME LINES (slow_frame_log_ms not in effect?)")
        return 2
    if syncs > 0 and kb > 0:
        print("RESULT: C5 MET (syncs > 0 and KB > 0)")
        return 0
    print("RESULT: C5 ZERO -> HOLD (route did not export); ask the Overseer")
    return 3


if __name__ == "__main__":
    sys.exit(main())
