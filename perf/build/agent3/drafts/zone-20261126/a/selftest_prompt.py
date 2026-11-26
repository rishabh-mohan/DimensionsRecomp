#!/usr/bin/env python3
"""selftest_prompt.py - offline test of prompt_sidecar.py WITHOUT the game (M3 gameplay kit).

fake_listener.py (build/agent3/toypad, imported read-only) stands in for the game's Toy Pad listener; a synthetic
game.log / input.csv under build/agent3/gameplay/selftest/simruns/ drives the sidecar:
  A (boot starter): listener + pads-white trigger -> 3 boot LOADs; the title LED cycle (no prompt may fire); the pad 2
    Batman prompt pulsing 6 s (fire, cooldown re-fire, then --on-max stops it); ctl files move/swap/remove/place/status
    (.done) and 4 bad ones (.err with the reason); route marks tp-replace-wyldstyle (ok) and tp-bad-x (error); the pad 3
    Wyldstyle prompt while Wyldstyle is on pad 1 and the pad 1 Gandalf prompt while Gandalf is on pad 2 (-> moves);
    summary.json ends it. The fake listener's LOAD/REMOVE sequence must equal the expected one exactly (order, pads,
    indexes, figure ids).
  B (boot none, fixed-pad specs): no boot LOADs; the Batman prompt -> a plain LOAD on pad 2, the Gandalf colour on pad 3
    is ignored by the @1 spec, on pad 1 -> a plain LOAD on pad 1.
  C: 4 bad --on specs -> exit 2 each.
  python -B selftest_prompt.py      exit 0 = PASS
"""
import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "toypad")))
from fake_listener import FakeListener  # noqa: E402

SIDECAR = os.path.join(HERE, "prompt_sidecar.py")
TAGS = os.path.join(HERE, "tags")
ROOT = os.path.join(HERE, "selftest", "simruns")
# A: the kit's colour-based triggers (any pad, pad from the regex); B: fixed-pad specs
ON_A = ["pad (?P<pad>[123]) mode 3 lit (00 00 16|00 00 05)=>batman@*",
        "pad (?P<pad>[123]) mode 3 lit (F4 69 16|3D 1A 05)=>wyldstyle@*",
        "pad (?P<pad>[123]) mode 3 lit (F4 00 16|3D 00 05)=>gandalf@*"]
ON_B = ["pad 2 mode 3 lit 00 00 (05|16)=>batman", "pad 1 mode 3 lit (F4 00 16|3D 00 05)=>gandalf@1"]
TITLE = ["FF 00 00", "FF 6E 00", "00 6E 00", "00 6E 18", "00 00 18", "FF 00 18", "99 42 0E", "00 00 0B", "7F 36 0B",
         "7F 00 0B"]                                  # + the post-prompt settle colours
FAILS = []


def check(cond, what):
    print("%s %s" % ("ok  " if cond else "FAIL", what), flush=True)
    if not cond:
        FAILS.append(what)


class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8")

    def w(self, msg):
        self.f.write("[2026-11-25 21:00:00.000] [info] [core] [t1] %s\n" % msg)
        self.f.flush()

    def lit(self, pad, rgb, mode=3):
        self.w("Toypad: pad %d mode %d lit %s (on 0 off 0 count 1 speed 16)" % (pad, mode, rgb))

    def pulse(self, pad, a, b, secs, step=0.25):
        t_end = time.time() + secs
        k = 0
        while time.time() < t_end:
            self.lit(pad, a if k % 2 == 0 else b)
            k += 1
            time.sleep(step)


def acts(fl):
    return [e[:3] + ((e[3],) if e[0] == "load" else ()) for e in list(fl.events) if e[0] in ("load", "remove")]


def wait_acts(fl, n, timeout=20):
    t_end = time.time() + timeout
    while time.time() < t_end and len(acts(fl)) < n:
        time.sleep(0.1)
    return len(acts(fl))


def start(fl, tag, extra, ons):
    t0 = time.time()
    argv = [sys.executable, "-B", SIDECAR, "--runs-root", ROOT, "--tag", tag, "--not-before", str(t0), "--timeout", "90",
            "--port", str(fl.port), "--delay", "0.3", "--gap", "0.1", "--on-delay", "0.2", "--on-cooldown", "2",
            "--on-max", "2", "--tags-dir", TAGS] + extra
    for s in ons:
        argv += ["--on", s]
    out = open(os.path.join(ROOT, tag + ".sidecar.out.txt"), "w", encoding="utf-8")   # a file, not a pipe: no stall
    p = subprocess.Popen(argv, stdout=out, stderr=subprocess.STDOUT, text=True)
    p.out_file = out
    time.sleep(0.8)
    run = os.path.join(ROOT, "20261125-210000-" + tag)
    os.makedirs(run)
    return p, run


def finish(p, run):
    with open(os.path.join(run, "summary.json"), "w") as f:
        f.write("{}")
    p.wait(timeout=60)
    p.out_file.close()
    with open(p.out_file.name, encoding="utf-8", errors="replace") as f:
        return f.read()


def scenario_a():
    print("--- A: boot starter, prompts, ctl, route marks", flush=True)
    fl = FakeListener(0)
    p, run = start(fl, "simA", [], ON_A)
    g = Log(os.path.join(run, "game.log"))
    g.w("Toypad listener active on 127.0.0.1:%d" % fl.port)
    g.lit(3, "FF FF FF", mode=1)                      # the boot trigger (all pads white)
    check(wait_acts(fl, 3) == 3, "A boot: 3 LOADs")
    for pad_, idx in ((2, 0), (1, 1), (3, 2)):
        g.w("Toypad listener: LOAD -> pad=%d index=%d (path len 0)" % (pad_, idx))
    for _ in range(3):                                # title cycle on all pads: must not fire a prompt
        for rgb in TITLE:
            for pad_ in (1, 2, 3):
                g.lit(pad_, rgb)
        time.sleep(0.2)
    time.sleep(1.0)
    check(len(acts(fl)) == 3, "A title LED cycle: no prompt fired")
    g.pulse(2, "00 00 16", "00 00 05", 6.0)           # Batman prompt: fire, re-fire after the cooldown, then on-max
    check(wait_acts(fl, 7) == 7, "A batman prompt: 2 fires (replace x2), on-max stops a 3rd")
    ctl = os.path.join(run, "toypad-ctl")
    check(os.path.isdir(ctl), "A ctl dir created")
    cmds = [("001", "move gandalf 3"), ("002", "swap batman gandalf"), ("003", "remove wyldstyle"),
            ("004", "# comment line\nplace wyldstyle 1"), ("005", "bogus thing"), ("006", "place batman 2"),
            ("007", "place joker 1"), ("008", "status"), ("009", "move batman 9")]
    for n, c in cmds:
        with open(os.path.join(ctl, n + ".cmd"), "w", encoding="utf-8") as f:
            f.write(c + "\n")
    t_end = time.time() + 30
    while time.time() < t_end and any(x.endswith(".cmd") for x in os.listdir(ctl)):
        time.sleep(0.2)
    names = sorted(os.listdir(ctl))
    check(names == ["001.done", "002.done", "003.done", "004.done", "005.err", "006.err", "007.err", "008.done",
                    "009.err"], "A ctl files renamed: %s" % " ".join(names))
    reasons = {n: open(os.path.join(ctl, n), encoding="utf-8").read() for n in names}
    check("unknown command" in reasons.get("005.err", ""), "A 005.err says unknown command")
    check("already on pad" in reasons.get("006.err", ""), "A 006.err says already on pad")
    check("no tag file" in reasons.get("007.err", ""), "A 007.err says no tag file")
    check("bad pad" in reasons.get("009.err", ""), "A 009.err says bad pad")
    check("batman pad=3 index=0, gandalf pad=2 index=1, wyldstyle pad=1 index=2" in reasons.get("008.done", ""),
          "A 008.done status = the slot map after move/swap/remove/place")
    with open(os.path.join(run, "input.csv"), "w", encoding="utf-8") as f:
        f.write("t,step,kind,detail\n1.0,1,mark,tp-replace-wyldstyle\n1.1,2,mark,tp-bad-x\n")
    check(wait_acts(fl, 17) == 17, "A route mark tp-replace-wyldstyle: REMOVE + LOAD")
    g.pulse(3, "F4 69 16", "3D 1A 05", 1.0)           # Wyldstyle prompt (pad 3) while she is on pad 1 -> move
    check(wait_acts(fl, 19) == 19, "A wyldstyle prompt on pad 3 (she is on pad 1): a move")
    g.pulse(1, "F4 00 16", "3D 00 05", 1.0)           # Gandalf prompt (pad 1) while he is on pad 2 -> move
    check(wait_acts(fl, 21) == 21, "A gandalf prompt on pad 1 (he is on pad 2): a move")
    time.sleep(1.0)
    out = finish(p, run)
    fl.close()
    exp = [("load", 2, 0, 1), ("load", 1, 1, 2), ("load", 3, 2, 3),          # boot
           ("remove", 2, 0), ("load", 2, 0, 1), ("remove", 2, 0), ("load", 2, 0, 1),  # batman prompt x2
           ("remove", 1, 1), ("load", 3, 1, 2),                              # move gandalf 3
           ("remove", 2, 0), ("remove", 3, 1), ("load", 3, 0, 1), ("load", 2, 1, 2),  # swap batman gandalf
           ("remove", 3, 2), ("load", 1, 2, 3),                              # remove / place wyldstyle 1
           ("remove", 1, 2), ("load", 1, 2, 3),                              # route tp-replace-wyldstyle
           ("remove", 1, 2), ("load", 3, 2, 3),                              # wyldstyle prompt -> move to pad 3
           ("remove", 2, 1), ("load", 1, 1, 2)]                              # gandalf prompt -> move to pad 1
    got = acts(fl)
    check(got == exp, "A listener LOAD/REMOVE sequence (%d actions)" % len(got))
    if got != exp:
        print("   got %s\n   exp %s" % (got, exp))
    check(p.returncode == 0, "A sidecar exit %d" % p.returncode)
    check("prompts=batman:2/2 wyldstyle:1/1 gandalf:1/1" in out, "A result: prompts batman 2/2, wyldstyle 1/1, gandalf 1/1")
    check("ctl=5 done/4 err route=1 ok/1 err" in out, "A result: ctl 5 done / 4 err, route 1 ok / 1 err")
    ev = open(os.path.join(run, "toypad-events.csv"), encoding="utf-8").read()
    check(ev.count(",prompt,") == 4 and ",ctl," in ev and ",route," in ev, "A toypad-events.csv has prompt/ctl/route rows")
    return out


def scenario_b():
    print("--- B: boot none, fixed-pad triggers", flush=True)
    fl = FakeListener(0)
    p, run = start(fl, "simB", ["--boot", "none"], ON_B)
    g = Log(os.path.join(run, "game.log"))
    g.w("Toypad listener active on 127.0.0.1:%d" % fl.port)
    g.lit(3, "FF FF FF", mode=1)
    time.sleep(1.5)
    check(len(acts(fl)) == 0, "B no boot placement")
    g.pulse(2, "00 00 16", "00 00 05", 1.0)
    g.pulse(3, "F4 00 16", "3D 00 05", 1.0)           # gandalf colour on pad 3: the @1 trigger must ignore it
    g.pulse(1, "F4 00 16", "3D 00 05", 1.0)
    wait_acts(fl, 2)
    time.sleep(0.5)
    out = finish(p, run)
    fl.close()
    check(acts(fl) == [("load", 2, 0, 1), ("load", 1, 1, 2)],
          "B prompts -> plain LOADs batman pad 2, gandalf pad 1 only (%s)" % acts(fl))
    check(p.returncode == 0, "B sidecar exit %d" % p.returncode)
    return out


def scenario_c():
    print("--- C: bad --on specs", flush=True)
    for spec, why in (("lit 00=>joker", "non-starter tag without @pad"), ("lit 00=>batman@*", "@* without a pad group"),
                      ("lit (00=>batman", "bad regex"), ("lit 00=>batman@4", "bad pad")):
        r = subprocess.run([sys.executable, "-B", SIDECAR, "--runs-root", ROOT, "--tag", "simC", "--on", spec],
                           capture_output=True, text=True, timeout=30)
        check(r.returncode == 2 and "bad --on" in r.stdout, "C %s -> exit %d" % (why, r.returncode))


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    os.makedirs(ROOT)
    out_a = scenario_a()
    out_b = scenario_b()
    scenario_c()
    if FAILS:
        print("--- sidecar output A ---\n" + out_a.rstrip() + "\n--- sidecar output B ---\n" + out_b.rstrip())
    print("RESULT: %s (%d failed)" % ("PASS" if not FAILS else "FAIL", len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
