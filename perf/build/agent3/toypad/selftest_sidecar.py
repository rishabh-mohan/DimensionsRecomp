#!/usr/bin/env python3
"""selftest_sidecar.py - offline test of toypad_sidecar.py WITHOUT the game (Agent 3, run-2 task 2).

Replays a real game.log (default: S4a r1, devoff4) into a fake run dir under
build/agent3/toypad/selftest/simruns/ in two halves, with fake_listener.py standing in for the
game's listener. The sidecar must find the run dir, see the listener line, trigger on the
"pad 3 lit white" line, LOAD the three starter tags (fake listener decodes ids 1/2/3, path len 0),
count three simulated "Toypad listener: LOAD ->" lines, and stop on summary.json.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ldtag  # noqa: E402
from fake_listener import FakeListener  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC_LOG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    REPO, "build", "agent3", "runs", "20261122-133333-s4a-r1-off-devoff4", "game.log")


def main():
    root = os.path.join(HERE, "selftest", "simruns")
    shutil.rmtree(root, ignore_errors=True)
    fl = FakeListener(0)
    t0 = time.time()
    p = subprocess.Popen([sys.executable, os.path.join(HERE, "toypad_sidecar.py"), "--runs-root", root, "--tag", "simtest",
                          "--not-before", str(t0), "--timeout", "30", "--port", str(fl.port), "--delay", "1", "--gap", "0.2"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(1.0)
    run = os.path.join(root, "20261122-000000-simtest")
    os.makedirs(run)
    with open(SRC_LOG, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines(True)
    k = len(lines) // 2
    with open(os.path.join(run, "game.log"), "w", encoding="utf-8") as f:
        f.writelines(lines[:k])
        f.flush()
        time.sleep(3)
        f.writelines(lines[k:])
        f.flush()
        time.sleep(4)
        for name, pad, idx in ldtag.STARTER:
            f.write("[2026-11-22 00:00:00.000] [info] [core] [t1] Toypad listener: LOAD -> pad=%d index=%d (path len 0)\n" % (pad, idx))
        f.flush()
    time.sleep(2)
    with open(os.path.join(run, "summary.json"), "w") as f:
        f.write("{}")
    out, _ = p.communicate(timeout=60)
    print(out.rstrip())
    loads = [e for e in fl.events if e[0] == "load"]
    print("fake listener loads:", loads)
    exp = [(pad, idx, ldtag.CHARACTERS[n], 0) for n, pad, idx in ldtag.STARTER]
    ok = (p.returncode == 0 and [(e[1], e[2], e[3], e[4]) for e in loads] == exp
          and os.path.exists(os.path.join(run, "toypad-events.csv")))
    fl.close()
    print("RESULT: %s (sidecar exit %d, %d loads)" % ("PASS" if ok else "FAIL", p.returncode, len(loads)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
