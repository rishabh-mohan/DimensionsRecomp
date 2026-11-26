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
  C: 4 bad --on specs -> exit 2 each; --zone without --on -> exit 2.
  D (--zone --led-shots): boot, a ctl swap to the confirmed layout (batman 2, gandalf 3, wyldstyle 1), the pad 3 zone
    colour before the prompt is answered and at the wrong speed (no T0), the Batman prompt, T0 -> step 1 (remove
    gandalf, remove + LOAD wyldstyle 3) after --zone-delay, pad 2 cue -> step 2 (remove batman, LOAD gandalf 2), no
    handoff -> one retry, pad 1 cue (FF 00 00 variant) -> LOAD batman 1, all pads 99 42 0E -> done; the speed-18 state
    -> alert + the +5 s shot row; exact LOAD/REMOVE sequence and shot rows.
  E (--zone, boot none): no handoff after step 1 and its retry -> the rule stops; a later cue does nothing.
  F (--zone, boot none): the Batman prompt fires again after T0 (a 'prompt after T0' zone row), the pad 1 cue while
    step 1 is open -> forward skip to step 3 (zone-skips=1), all pads 99 42 0E -> done.
  python -B selftest_prompt.py      exit 0 = PASS
"""
import csv
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

    def lit(self, pad, rgb, mode=3, speed=16):
        self.w("Toypad: pad %d mode %d lit %s (on 0 off 0 count 1 speed %d)" % (pad, mode, rgb, speed))

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
    r = subprocess.run([sys.executable, "-B", SIDECAR, "--runs-root", ROOT, "--tag", "simC", "--zone"],
                       capture_output=True, text=True, timeout=30)
    check(r.returncode == 2 and "bad --zone" in r.stdout, "C --zone without --on prompts -> exit %d" % r.returncode)


ZONE_ARGS = ["--zone", "--zone-delay", "1", "--zone-gap", "0.3", "--zone-confirm", "2", "--led-shots"]


def rows(run, kind):
    with open(os.path.join(run, "toypad-events.csv"), newline="", encoding="utf-8") as f:
        return [r[4] for r in csv.reader(f) if len(r) == 5 and r[3] == kind]


def scenario_d():
    print("--- D: --zone step (3 -> 2 -> 1, one retry on pad 2), --led-shots, the speed-18 alert", flush=True)
    fl = FakeListener(0)
    p, run = start(fl, "simD", ZONE_ARGS, ["pad 2 mode 3 lit 00 00 (05|16)=>batman"])
    g = Log(os.path.join(run, "game.log"))
    g.w("Toypad listener active on 127.0.0.1:%d" % fl.port)
    g.lit(3, "FF FF FF", mode=1)
    check(wait_acts(fl, 3) == 3, "D boot: 3 LOADs (batman 2, gandalf 1, wyldstyle 3)")
    for _ in range(3):                                # the zone colours before the prompt is answered: no T0
        g.lit(3, "FF 00 18", speed=15)
        time.sleep(0.25)
    time.sleep(1.5)
    check(len(acts(fl)) == 3, "D pad 3 FF 00 18 speed 15 before the prompts are done: no zone action")
    ctl = os.path.join(run, "toypad-ctl")
    with open(os.path.join(ctl, "001.cmd"), "w", encoding="utf-8") as f:
        f.write("swap gandalf wyldstyle\n")         # -> the confirmed layout b2 g3 w1
    check(wait_acts(fl, 7) == 7, "D ctl swap -> batman 2, gandalf 3, wyldstyle 1")
    g.pulse(2, "00 00 16", "00 00 05", 1.0)
    check(wait_acts(fl, 9) == 9, "D batman prompt answered (replace)")
    g.lit(3, "FF 00 18", speed=16)                    # wrong speed: no T0
    time.sleep(0.6)
    t0 = time.time()
    g.lit(3, "FF 00 18", speed=15)                    # T0
    check(wait_acts(fl, 12) == 12 and time.time() - t0 >= 1.0, "D step 1 (pad 3) after T0 + delay: 3 commands")
    g.w("Toypad listener: LOAD -> pad=3 index=2 (path len 0)")
    g.lit(2, "FF 6E 18", speed=15)                    # handoff -> step 2
    check(wait_acts(fl, 14) == 14, "D step 2 (pad 2): remove batman, place gandalf 2")
    check(wait_acts(fl, 16, timeout=8) == 16, "D step 2: no handoff in 2 s -> one retry (remove + place gandalf 2)")
    g.w("Toypad listener: LOAD -> pad=2 index=1 (path len 0)")
    g.lit(1, "FF 00 00", speed=15)                    # pad 1 cue, variant 'wanted figure on another pad'
    check(wait_acts(fl, 17) == 17, "D step 3 (pad 1): place batman 1")
    g.w("Toypad listener: LOAD -> pad=1 index=0 (path len 0)")
    for pad_ in (1, 2, 3):
        g.lit(pad_, "99 42 0E", speed=15)
    time.sleep(1.0)
    t_end = time.time() + 6.5
    while time.time() < t_end:                        # the all-pads fast red state
        for pad_ in (1, 2, 3):
            g.lit(pad_, "FF 00 00", speed=18)
        time.sleep(0.25)
    out = finish(p, run)
    fl.close()
    exp = [("load", 2, 0, 1), ("load", 1, 1, 2), ("load", 3, 2, 3),
           ("remove", 1, 1), ("remove", 3, 2), ("load", 3, 1, 2), ("load", 1, 2, 3),   # swap gandalf wyldstyle
           ("remove", 2, 0), ("load", 2, 0, 1),                                        # batman prompt
           ("remove", 3, 1), ("remove", 1, 2), ("load", 3, 2, 3),                      # step 1
           ("remove", 2, 0), ("load", 2, 1, 2),                                        # step 2
           ("remove", 2, 1), ("load", 2, 1, 2),                                        # step 2 retry
           ("load", 1, 0, 1)]                                                          # step 3
    got = acts(fl)
    check(got == exp, "D listener LOAD/REMOVE sequence (%d actions)" % len(got))
    if got != exp:
        print("   got %s\n   exp %s" % (got, exp))
    check(p.returncode == 0, "D sidecar exit %d" % p.returncode)
    check("zone=done zone-skips=0 alerts=1" in out, "D result: zone=done, zone-skips=0, alerts=1")
    shots = rows(run, "shot")
    check(shots == ["zone-t0", "zone-cue-pad2", "zone-cue-pad1", "zone-done", "alert1-plus05s"],
          "D shot rows: %s" % " ".join(shots))
    zl = " | ".join(rows(run, "zone"))
    check("after the LOAD confirm (game_ts) (after the retry)" in zl and "plan: remove gandalf; remove wyldstyle; "
          "place wyldstyle 3" in zl, "D zone rows: step 1 plan, retry handoff timed from the LOAD confirm")
    return out


def scenario_e():
    print("--- E: --zone with no handoff: one retry, then the zone rule stops", flush=True)
    fl = FakeListener(0)
    p, run = start(fl, "simE", ["--boot", "none"] + ZONE_ARGS[:-1], ["pad 2 mode 3 lit 00 00 (05|16)=>batman"])
    g = Log(os.path.join(run, "game.log"))
    g.w("Toypad listener active on 127.0.0.1:%d" % fl.port)
    g.pulse(2, "00 00 16", "00 00 05", 0.5)
    check(wait_acts(fl, 1) == 1, "E batman prompt: a plain LOAD on pad 2")
    g.lit(3, "FF 00 18", speed=15)
    check(wait_acts(fl, 4, timeout=10) == 4, "E step 1: place wyldstyle 3, then the retry (remove + place)")
    t_end = time.time() + 8
    while time.time() < t_end and not rows(run, "zone-stop"):
        time.sleep(0.2)
    g.lit(2, "FF 6E 18", speed=15)                    # too late: the rule has stopped
    time.sleep(1.0)
    out = finish(p, run)
    fl.close()
    check(acts(fl) == [("load", 2, 0, 1), ("load", 3, 2, 3), ("remove", 3, 2), ("load", 3, 2, 3)],
          "E sequence: no action after the stop (%s)" % acts(fl))
    check("zone=stopped: step 1 pad 3: no handoff" in out and "shots=0" in out, "E result: zone stopped at step 1, "
          "no shot rows without --led-shots")
    check(p.returncode == 0, "E sidecar exit %d" % p.returncode)
    return out


def scenario_f():
    print("--- F: --zone, a prompt after T0 (logged), pad 1 cue while step 1 is open (forward skip, counted)", flush=True)
    fl = FakeListener(0)
    p, run = start(fl, "simF", ["--boot", "none"] + ZONE_ARGS[:-1], ["pad 2 mode 3 lit 00 00 (05|16)=>batman"])
    g = Log(os.path.join(run, "game.log"))
    g.w("Toypad listener active on 127.0.0.1:%d" % fl.port)
    g.pulse(2, "00 00 16", "00 00 05", 0.5)
    check(wait_acts(fl, 1) == 1, "F batman prompt: a plain LOAD on pad 2")
    time.sleep(2.3)                                   # past --on-cooldown 2
    g.lit(3, "FF 00 18", speed=15)                    # T0
    g.pulse(2, "00 00 16", "00 00 05", 0.5)           # the prompt again after T0 -> fire 2/2 (replace batman)
    check(wait_acts(fl, 4) == 4, "F prompt replace (remove + LOAD batman 2) and step 1 (LOAD wyldstyle 3)")
    g.lit(1, "FF 00 00", speed=15)                    # pad 1 cue while step 1 is open -> skip to step 3
    check(wait_acts(fl, 6) == 6, "F skip to step 3: remove batman, LOAD batman 1")
    g.w("Toypad listener: LOAD -> pad=1 index=0 (path len 0)")
    for pad_ in (1, 2, 3):
        g.lit(pad_, "99 42 0E", speed=15)
    time.sleep(1.0)
    out = finish(p, run)
    fl.close()
    got = acts(fl)
    check(len(got) == 6 and got[-2:] == [("remove", 2, 0), ("load", 1, 0, 1)],
          "F sequence: 6 actions, ends remove batman 2 + LOAD batman 1 (%s)" % got)
    zl = " | ".join(rows(run, "zone"))
    check("prompt after T0: batman fire 2/2 -> pad 2" in zl and "skipping to it" in zl,
          "F zone rows: 'prompt after T0' and the forward skip")
    check("zone=done zone-skips=1 " in out and "prompts=batman:2/2" in out, "F result: zone=done, zone-skips=1, batman 2/2")
    check(p.returncode == 0, "F sidecar exit %d" % p.returncode)
    return out


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    os.makedirs(ROOT)
    out_a = scenario_a()
    out_b = scenario_b()
    scenario_c()
    out_d = scenario_d()
    out_e = scenario_e()
    out_f = scenario_f()
    if FAILS:
        print("--- sidecar output A ---\n" + out_a.rstrip() + "\n--- sidecar output B ---\n" + out_b.rstrip() +
              "\n--- sidecar output D ---\n" + out_d.rstrip() + "\n--- sidecar output E ---\n" + out_e.rstrip() +
              "\n--- sidecar output F ---\n" + out_f.rstrip())
    print("RESULT: %s (%d failed)" % ("PASS" if not FAILS else "FAIL", len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
