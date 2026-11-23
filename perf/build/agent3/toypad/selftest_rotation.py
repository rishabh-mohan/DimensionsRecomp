#!/usr/bin/env python3
"""selftest_rotation.py - offline test of toypad_sidecar.py across game.log rotation, WITHOUT the game
(Agent 3, run-2 task 2, 11-22 22:50).

w6gB (11-22 22:23) ran with an empty pad: slow_frame_log_ms=1 rotated game.log (spdlog: game.log ->
game.1.log -> game.2.log) before the "pad 3 lit white" trigger, and the old tail kept reading the new
game.log at the old offset. This replays that, with fake_listener.py standing in for the game's listener:
  A. unit checks of Tail: file ids (os.stat vs os.fstat) agree; lines appended to the old file just before
     the rename come out of game.1.log; a double rotation between two reads gives game.2.log, game.1.log,
     game.log in order; an in-place truncation restarts at 0;
  B. the sidecar end to end in a fake run dir: listener line + ~300 KB filler; 2 Toypad lines appended and
     the file rotated at once; the trigger only in the new, shorter game.log (the w6gB case); after the 3
     LOADs, 1 confirm line, a second rotation (game.1.log -> game.2.log), then 2 confirm lines; summary.json.
PASS (B) = sidecar exit 0, the fake listener got Batman 2/0, Gandalf 1/1, Wyldstyle 3/2 with path len 0, the
result line says load-confirms=3/3, and toypad-events.csv has 2 log-rotated rows and both pre-rotation
Toypad lines. --sidecar PATH tests another copy; with --expect-fail (for toypad_sidecar.py.bak-2245, the
pre-fix copy) the exit code is 0 only if B FAILS.
"""
import argparse
import csv
import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ldtag  # noqa: E402
from fake_listener import FakeListener  # noqa: E402

TS = "[2026-11-22 22:24:%02d.000] [info] [core] [t1] "


def rotate(log_path, keep=3):
    """spdlog-style: game.(k-1).log -> game.k.log ... game.log -> game.1.log, retrying a sharing clash."""
    root, ext = os.path.splitext(log_path)
    names = [log_path] + ["%s.%d%s" % (root, i, ext) for i in range(1, keep + 1)]
    for i in range(keep, 0, -1):
        src, dst = names[i - 1], names[i]
        if not os.path.exists(src):
            continue
        for _ in range(100):
            try:
                os.replace(src, dst)
                break
            except PermissionError:
                time.sleep(0.01)
        else:
            raise RuntimeError("rename %s failed" % src)


def append(path, lines):
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.writelines(s + "\n" for s in lines)


def load_module(path):
    loader = importlib.machinery.SourceFileLoader("sidecar_under_test", path)
    spec = importlib.util.spec_from_loader("sidecar_under_test", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def unit(mod, tmp):
    Tail = mod.Tail
    if not hasattr(Tail, "_fid"):
        print("A: skipped (this copy has no rotation support)")
        return None
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    ok = True

    def check(name, got, exp):
        nonlocal ok
        good = got == exp
        ok = ok and good
        print("  A %s %s: got %r%s" % ("ok  " if good else "FAIL", name, got, "" if good else ", expected %r" % (exp,)))

    p = os.path.join(tmp, "game.log")
    append(p, ["a1", "a2"])
    with open(p, "rb") as f:
        st = os.fstat(f.fileno())
    check("file id os.stat == os.fstat", Tail._fid(p), (st.st_dev, st.st_ino))
    rots = []
    t = Tail(p, on_rotate=rots.append)
    check("first read", t.lines(), ["a1", "a2"])
    append(p, ["a3"])
    check("append", t.lines(), ["a3"])
    append(p, ["b1", "b2"])
    rotate(p)
    append(p, ["c1"])
    check("lines appended just before a rotation, then the new file", t.lines(), ["b1", "b2", "c1"])
    append(p, ["d1"])
    rotate(p)
    append(p, ["e1"])
    rotate(p)
    append(p, ["f1"])
    check("two rotations between reads (game.2.log, game.1.log, game.log)", t.lines(), ["d1", "e1", "f1"])
    append(p, ["g1-a-longer-line-so-the-truncated-file-is-shorter"])
    check("append after rotations", t.lines(), ["g1-a-longer-line-so-the-truncated-file-is-shorter"])
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("h1\n")
    check("in-place truncation restarts at 0", t.lines(), ["h1"])
    check("on_rotate calls", rots, [1, 2, 3])
    check("nothing new", t.lines(), [])
    return ok


def e2e(sidecar, root):
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    fl = FakeListener(0)
    t0 = time.time()
    p = subprocess.Popen([sys.executable, sidecar, "--runs-root", root, "--tag", "simrot", "--not-before", str(t0),
                          "--timeout", "45", "--port", str(fl.port), "--delay", "1", "--gap", "0.2"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(1.0)
    run = os.path.join(root, "20261122-222313-simrot")
    os.makedirs(run)
    gl = os.path.join(run, "game.log")
    filler = [TS % 0 + "slow frame #%d: 3.1 ms (draws 594, memexport syncs 0, 0 B)" % i for i in range(5000)]
    append(gl, [TS % 0 + "Toypad listener active on 127.0.0.1:%d" % fl.port] + filler)
    size1 = os.path.getsize(gl)
    time.sleep(1.5)  # the sidecar reads all of it: its offset is now ~size1
    pre = [TS % 1 + "Toypad: pad 1 mode 1 lit FF 6E 00", TS % 1 + "Toypad: pad 2 mode 1 lit FF 6E 00"]
    append(gl, pre)
    rotate(gl)  # at once: these 2 lines exist only in game.1.log
    time.sleep(1.0)
    append(gl, [TS % 2 + "Toypad: pad 3 mode 1 lit FF FF FF"])  # the trigger, in a file far shorter than the offset
    size2 = os.path.getsize(gl)
    t_end = time.time() + 15
    while time.time() < t_end and len([e for e in fl.events if e[0] == "load"]) < 3:
        time.sleep(0.1)
    confirms = [TS % 9 + "Toypad listener: LOAD -> pad=%d index=%d (path len 0)" % (pad, idx) for _n, pad, idx in ldtag.STARTER]
    append(gl, confirms[:1])
    rotate(gl)  # game.1.log -> game.2.log, game.log -> game.1.log
    append(gl, confirms[1:])
    time.sleep(1.5)
    with open(os.path.join(run, "summary.json"), "w") as f:
        f.write("{}")
    out, _ = p.communicate(timeout=90)
    fl.close()
    print(out.rstrip())
    loads = [e for e in fl.events if e[0] == "load"]
    exp = [(pad, idx, ldtag.CHARACTERS[n], 0) for n, pad, idx in ldtag.STARTER]
    got = [(e[1], e[2], e[3], e[4]) for e in loads]
    ev_path = os.path.join(run, "toypad-events.csv")
    rows = []
    if os.path.exists(ev_path):
        with open(ev_path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))[1:]
    kinds = [r[3] for r in rows if len(r) > 4]
    details = [r[4] for r in rows if len(r) > 4]
    n_rot = kinds.count("log-rotated")
    pre_seen = [any(d == s[s.find("Toypad"):] for d in details) for s in pre]
    first_rot = kinds.index("log-rotated") if "log-rotated" in kinds else None
    drained = first_rot is not None and all(
        any(d == s[s.find("Toypad"):] for d in details[first_rot + 1:]) for s in pre)
    result = [d for k, d in zip(kinds, details) if k == "result"]
    checks = [
        ("sidecar exit 0", p.returncode == 0, p.returncode),
        ("fake listener got the 3 LOADs in order", got == exp, got),
        ("result load-confirms=3/3", bool(result) and "load-confirms=3/3" in result[-1], result[-1] if result else None),
        ("2 log-rotated rows", n_rot == 2, n_rot),
        ("both pre-rotation Toypad lines logged", all(pre_seen), pre_seen),
    ]
    ok = True
    for name, good, val in checks:
        ok = ok and good
        print("  B %s %s: %r" % ("ok  " if good else "FAIL", name, val))
    print("  B note: offset before rotation %d B, new game.log %d B at the trigger; drain of game.1.log used: %s"
          % (size1, size2, "yes" if drained else "no (the sidecar read them before the rename)"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sidecar", default=os.path.join(HERE, "toypad_sidecar.py"))
    ap.add_argument("--expect-fail", action="store_true")
    a = ap.parse_args()
    sidecar = os.path.abspath(a.sidecar)
    print("sidecar under test: %s" % sidecar)
    okA = unit(load_module(sidecar), os.path.join(HERE, "selftest", "rot-unit"))
    okB = e2e(sidecar, os.path.join(HERE, "selftest", "simruns-rot"))
    print("RESULT A: %s" % ("skipped" if okA is None else ("PASS" if okA else "FAIL")))
    print("RESULT B: %s%s" % ("PASS" if okB else "FAIL", " (expected FAIL)" if a.expect_fail else ""))
    if a.expect_fail:
        return 0 if not okB else 1
    return 0 if (okA is not False and okB) else 1


if __name__ == "__main__":
    sys.exit(main())
