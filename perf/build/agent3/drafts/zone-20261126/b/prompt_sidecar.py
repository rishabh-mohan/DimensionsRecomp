#!/usr/bin/env python3
"""prompt_sidecar.py - M3 gameplay kit: build/agent3/toypad/toypad_sidecar.py plus mid-game Toy Pad control.

Same flags and boot behaviour as toypad_sidecar.py (its Tail, decode, find_run, parse_not_before are imported from it;
toypad_client/ldtag are used unchanged; nothing under build/agent3/toypad is written). Additions, all through ONE
action layer (the sidecar's own slot map: tag -> pad 1-3 (1 centre, 2 left, 3 right) + index 0-6, auto-managed):
  commands   place <tag> <pad> | remove <tag> | move <tag> <pad> (REMOVE, --gap, LOAD on the new pad, same index) |
             swap <a> <b> (both lifted, then each LOADed on the other's pad) | replace <tag> (lift + put back) | status
             <tag> = any <name>.bin in --tags-dir that ldtag.read_tag accepts (name [a-z0-9_]+; the 3 starter
             characters must also decode to their figure id). Starter tags keep their ldtag.STARTER index if free.
  ctl files  <run>/toypad-ctl/*.cmd (the sidecar creates the dir): taken in name order once >= 0.5 s old; one command
             per line ('#' = comment, max 20 lines, max 4 KB, stops at the first failing line); then renamed to .done
             (results appended) or .err (reason appended). Example: Set-Content <run>\\toypad-ctl\\001.cmd 'move gandalf 3'
  route      an input.csv mark named tp-<command>-<args> runs that command (mark tp-move-gandalf-3, tp-remove-batman).
  prompts    --on "REGEX=>tag[@pad]" (repeatable): a game.log line matching REGEX puts the tag on the pad (default
             its starter pad) --on-delay s later: replace if it is there, move if it is on another pad, else place.
             Re-arms after --on-cooldown s while the game keeps prompting; at most --on-max fires per trigger.
  --boot     starter (default) = the 3 starter tags placed on --trigger-log/--trigger-mark as before; none = no boot
             placement (tags reach the pads only through commands/prompts).
  --zone     (OFF by default) the story's zone step after the 3 prompts (manual run 20261126-051159-gpman-native,
             EXPLORE3 20261126-045407): T0 = pad 3 'lit FF 00 18 ... speed 15' once every --on prompt has fired ok; the
             pads then ask in the order 3 (Wyldstyle), 2 (Gandalf), 1 (Batman); a pad's cue is a speed-15 blink of
             FF 00 18 / FF 6E 18 / 00 00 18 (wanted figure on no pad) or FF 00 00 (pads 2/1: it is on another pad).
             Step pad P, figure F (pad 3 at T0 + --zone-delay, pads 2/1 on their own cue + --zone-gap): REMOVE every
             other figure on P, then REMOVE F if it is on any pad, then LOAD F on P; --zone-gap s between commands.
             Handoff = the next pad's cue (pad 1: all 3 pads 99 42 0E); none within --zone-confirm s after the last
             LOAD -> one retry of the step, then the zone rule stops (logged). A command error -> one retry, then stop.
             A later pad's cue while a step is open skips forward to it (counted: zone-skips= in the result line); a
             prompt that fires after T0 is logged as a 'zone' row 'prompt after T0'.
  --led-shots asks gameplay-watch.ps1 for screenshots ('shot' rows in toypad-events.csv): the zone cues/handoffs
             (with --zone) and the all-pads FF 00 00 speed-18 state at +5/+30/+60 s after it starts. Passive.
The story's prompts (manual run 20261125-204323-gpman-native): pad 2 'lit 00 00 16'/'00 00 05' (Batman), pad 3
'lit F4 69 16'/'3D 1A 05' (Wyldstyle), ~0.5 s apart for 120 s; then the game's failsafe plays on without a figure.
Writes only <run>/toypad-events.csv, <run>/toypad-ctl/ and stdout; its only client is the game's 127.0.0.1 listener.
Run with python -B (no __pycache__ in build/agent3/toypad).
"""
import argparse
import csv
import datetime
import os
import re
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
TOYPAD = os.path.normpath(os.path.join(HERE, "..", "toypad"))
sys.path.insert(0, TOYPAD)
import ldtag  # noqa: E402
import toypad_client as tc  # noqa: E402
from toypad_sidecar import DEFAULT_TRIGGER, RE_LISTENER, RE_TS, Tail, decode, find_run, parse_not_before  # noqa: E402

STARTER_SLOT = {n: (p, i) for n, p, i in ldtag.STARTER}
RE_NAME = re.compile(r"^[a-z0-9_]{1,32}$")
CTL_MIN_AGE = 0.5
CTL_MAX_BYTES = 4096
CTL_MAX_LINES = 20
RE_LED = re.compile(r"Toypad: pad ([123]) mode \d lit ([0-9A-F]{2} [0-9A-F]{2} [0-9A-F]{2}) \(on \d+ off \d+ count \d+ "
                    r"speed (\d+)\)")
ZONE_ORDER = (3, 2, 1)
ZONE_WANT = {3: "wyldstyle", 2: "gandalf", 1: "batman"}
ZONE_CUE = {3: ("FF 00 18",), 2: ("FF 6E 18", "FF 00 00"), 1: ("00 00 18", "FF 00 00")}
ZONE_SPEED = 15
ZONE_DONE = "99 42 0E"
ALERT = ("FF 00 00", 18)          # all pads fast red after the zone step (manual 20261126-051159 from 05:27:26)
ALERT_SHOTS = (5, 30, 60)
ALERT_REARM = 120.0


def _secs(ts):
    """'HH:MM:SS.fff' (a game.log time) -> seconds of the day; 0.0 if empty/unparsable."""
    try:
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except (AttributeError, ValueError):
        return 0.0


class Zone:
    """--zone: the observed-driven zone step. feed_led/feed_confirm from game.log lines, tick() from the main loop."""

    def __init__(self, pad, log, shot, prompts_done, delay, gap, confirm):
        self.pad, self.log, self.shot, self.prompts_done = pad, log, shot, prompts_done
        self.delay, self.gap, self.confirm = delay, gap, confirm
        self.state = "armed"      # armed -> wait -> act -> confirm -> (next step) ... -> done | stopped
        self.k = -1               # index into ZONE_ORDER
        self.due = None           # next command (wait/act) or the confirm deadline
        self.queue = []
        self.retried = False
        self.t0 = None
        self.last_confirm = None  # time of the last listener LOAD confirm for this step's pad
        self.amber = set()
        self.result = "armed"
        self.skips = 0            # forward skips (a later pad's cue while a step was open)

    def _start(self, k, due, why, ts):
        self.k, self.state, self.due, self.queue, self.retried, self.last_confirm = k, "wait", due, [], False, None
        self.amber = set()
        p = ZONE_ORDER[k]
        self.log("zone", "step %d pad %d wants %s: %s; first command in %.1f s" % (
            k + 1, p, ZONE_WANT[p], why, max(0.0, due - time.time())), ts)

    def plan(self):
        p = ZONE_ORDER[self.k]
        f = ZONE_WANT[p]
        cmds = [["remove", n] for n, (q, _i) in sorted(self.pad.on.items()) if q == p and n != f]
        if f in self.pad.on:
            cmds.append(["remove", f])
        cmds.append(["place", f, str(p)])
        return cmds

    def _stop(self, why, ts=""):
        self.state, self.due, self.queue, self.result = "stopped", None, [], "stopped: " + why
        self.log("zone-stop", why, ts)
        self.shot("zone-stop")

    def feed_confirm(self, pad_no, ts=""):
        if self.state in ("act", "confirm") and pad_no == ZONE_ORDER[self.k]:
            self.last_confirm = (time.time(), ts)

    def feed_led(self, p, rgb, speed, ts):
        now = time.time()
        if self.state in ("done", "stopped") or speed != ZONE_SPEED:
            return
        if self.state == "armed":
            if p == 3 and rgb in ZONE_CUE[3] and self.prompts_done():
                self.t0 = now
                self.log("zone-t0", "pad 3 lit %s speed %d after the prompts" % (rgb, speed), ts)
                self.shot("zone-t0")
                self._start(0, now + self.delay, "T0 + %.0f s" % self.delay, ts)
            return
        if self.k == len(ZONE_ORDER) - 1 and rgb == ZONE_DONE:
            self.amber.add(p)
            if len(self.amber) == 3:
                self._handoff("all 3 pads %s" % ZONE_DONE, ts)
                self.state, self.due, self.result = "done", None, "done"
                self.log("zone-done", "all 3 pads %s, T0 + %.1f s" % (ZONE_DONE, now - self.t0), ts)
                self.shot("zone-done")
            return
        if p not in ZONE_ORDER[self.k + 1:] or rgb not in ZONE_CUE[p]:
            return
        j = ZONE_ORDER.index(p)
        if j > self.k + 1:
            self.skips += 1
            self.log("zone", "pad %d cue %s while step %d (pad %d) was open: skipping to it" % (
                p, rgb, self.k + 1, ZONE_ORDER[self.k]), ts)
        else:
            self._handoff("pad %d lit %s" % (p, rgb), ts)
        self.shot("zone-cue-pad%d" % p)
        self._start(j, now + self.gap, "cue pad %d lit %s" % (p, rgb), ts)

    def _handoff(self, what, ts):
        p = ZONE_ORDER[self.k]
        if self.state == "confirm" and self.last_confirm is not None:
            t_sc, t_game = self.last_confirm
            dt, base = _secs(ts) - _secs(t_game), "game_ts"
            if not (ts and t_game) or dt < 0:
                dt, base = time.time() - t_sc, "sidecar clock"
            self.log("zone", "step %d pad %d handoff (%s) %.3f s after the LOAD confirm (%s)%s" % (
                self.k + 1, p, what, dt, base, " (after the retry)" if self.retried else ""), ts)
        else:
            self.log("zone", "step %d pad %d handoff (%s) in state %s, before our LOAD was confirmed (game timeout or "
                     "an earlier figure)" % (self.k + 1, p, what, self.state), ts)

    def tick(self):
        if self.state not in ("wait", "act", "confirm") or self.due is None or time.time() < self.due:
            return
        p = ZONE_ORDER[self.k]
        if self.state == "confirm":
            if self.retried:
                self._stop("step %d pad %d: no handoff %.0f s after the retry" % (self.k + 1, p, self.confirm))
                return
            self.retried = True
            self.log("zone", "step %d pad %d: no handoff %.0f s after the last LOAD: retry" % (self.k + 1, p, self.confirm))
            self.state, self.queue = "act", self.plan()
        elif self.state == "wait":
            self.state, self.queue = "act", self.plan()
            self.log("zone", "step %d pad %d plan: %s" % (self.k + 1, p, "; ".join(" ".join(c) for c in self.queue)))
        words = self.queue.pop(0)
        ok, msg = self.pad.run(words, "zone")
        self.log("zone", "step %d %s: %s -> %s" % (self.k + 1, "ok" if ok else "ERR", " ".join(words), msg))
        if not ok:
            if self.retried:
                self._stop("step %d pad %d: %s failed after the retry: %s" % (self.k + 1, p, " ".join(words), msg))
                return
            self.retried = True
            self.queue = self.plan()
            self.log("zone", "step %d pad %d: retry plan %s" % (self.k + 1, p, "; ".join(" ".join(c) for c in self.queue)))
        if self.queue:
            self.due = time.time() + self.gap
        else:
            self.state, self.due = "confirm", time.time() + self.confirm


class Toypad:
    """The sidecar's slot map + the actions. run(words) -> (ok, message); never raises for a bad command."""

    def __init__(self, port_fn, tags_dir, gap, log):
        self.port_fn = port_fn
        self.tags_dir = tags_dir
        self.gap = gap
        self.log = log
        self.on = {}            # name -> (pad, index)
        self.cache = {}

    def tag(self, name):
        if not RE_NAME.match(name or ""):
            raise ValueError("bad tag name %r (want [a-z0-9_]+)" % name)
        if name not in self.cache:
            path = os.path.join(self.tags_dir, name + ".bin")
            if not os.path.isfile(path):
                raise ValueError("no tag file %s.bin in the tags dir" % name)
            t = ldtag.read_tag(path)
            if len(t) != ldtag.TAG_SIZE:
                raise ValueError("%s.bin is %d bytes, not %d" % (name, len(t), ldtag.TAG_SIZE))
            if name in ldtag.CHARACTERS and ldtag.figure_id(t) != ldtag.CHARACTERS[name]:
                raise ValueError("%s.bin decodes to id %d" % (name, ldtag.figure_id(t)))
            self.cache[name] = t
        return self.cache[name]

    @staticmethod
    def pad_arg(s):
        if s not in ("1", "2", "3"):
            raise ValueError("bad pad %r (1 centre, 2 left, 3 right)" % s)
        return int(s)

    def free_index(self, name):
        used = {i for _p, i in self.on.values()}
        pref = STARTER_SLOT.get(name, (0, None))[1]
        if pref is not None and pref not in used:
            return pref
        return next((i for i in range(7) if i not in used), None)

    def _load(self, name, pad, idx, why, wait_s=0.0):
        t0 = time.time()
        try:
            ok = tc.load(self.port_fn(), self.tag(name), pad, idx, "", timeout=5.0, wait_s=wait_s)
            err = ""
        except OSError as e:
            ok, err = False, " " + str(e)
        if ok:
            self.on[name] = (pad, idx)
        msg = "LOAD %s id=%d pad=%d index=%d path_len=0 -> %s%s (%.2f s)" % (
            name, ldtag.figure_id(self.tag(name)), pad, idx, "hangup-ok" if ok else "FAIL", err, time.time() - t0)
        self.log("load", "%s [%s]" % (msg, why))
        return ok, msg

    def _remove(self, name, why):
        pad, idx = self.on.pop(name)
        try:
            ok = tc.remove(self.port_fn(), pad, idx, timeout=5.0)
            err = ""
        except OSError as e:
            ok, err = False, " " + str(e)
        msg = "REMOVE %s pad=%d index=%d -> %s%s" % (name, pad, idx, "hangup-ok" if ok else "FAIL", err)
        self.log("remove", "%s [%s]" % (msg, why))
        return ok, msg

    def place(self, name, pad, why, wait_s=0.0):
        self.tag(name)
        if name in self.on:
            raise ValueError("%s is already on pad %d (use move or replace)" % (name, self.on[name][0]))
        idx = self.free_index(name)
        if idx is None:
            raise ValueError("all 7 slots are in use")
        return self._load(name, pad, idx, why, wait_s)

    def remove(self, name, why):
        self.tag(name)
        if name not in self.on:
            raise ValueError("%s is not on the pad" % name)
        return self._remove(name, why)

    def move(self, name, pad, why):
        self.tag(name)
        if name not in self.on:
            raise ValueError("%s is not on the pad (use place)" % name)
        if self.on[name][0] == pad:
            raise ValueError("%s is already on pad %d (use replace)" % (name, pad))
        idx = self.on[name][1]
        ok1, m1 = self._remove(name, why)
        time.sleep(self.gap)
        ok2, m2 = self._load(name, pad, idx, why)
        return ok1 and ok2, m1 + "; " + m2

    def replace(self, name, why):
        self.tag(name)
        if name not in self.on:
            raise ValueError("%s is not on the pad (use place)" % name)
        pad, idx = self.on[name]
        ok1, m1 = self._remove(name, why)
        time.sleep(self.gap)
        ok2, m2 = self._load(name, pad, idx, why)
        return ok1 and ok2, m1 + "; " + m2

    def swap(self, a, b, why):
        self.tag(a)
        self.tag(b)
        if a == b:
            raise ValueError("swap needs two different tags")
        for n in (a, b):
            if n not in self.on:
                raise ValueError("%s is not on the pad" % n)
        (pa, ia), (pb, ib) = self.on[a], self.on[b]
        if pa == pb:
            raise ValueError("%s and %s are both on pad %d" % (a, b, pa))
        ok1, m1 = self._remove(a, why)
        time.sleep(self.gap)
        ok2, m2 = self._remove(b, why)
        time.sleep(self.gap)
        ok3, m3 = self._load(a, pb, ia, why)
        time.sleep(self.gap)
        ok4, m4 = self._load(b, pa, ib, why)
        return ok1 and ok2 and ok3 and ok4, "; ".join((m1, m2, m3, m4))

    def status(self):
        return "slots: " + (", ".join("%s pad=%d index=%d" % (n, p, i) for n, (p, i) in sorted(self.on.items())) or "empty")

    def run(self, words, why):
        """One command (a list of words) -> (ok, message)."""
        try:
            if not words:
                raise ValueError("empty command")
            cmd, args = words[0].lower(), [w.lower() for w in words[1:]]
            need = {"place": 2, "remove": 1, "move": 2, "swap": 2, "replace": 1, "status": 0}
            if cmd not in need:
                raise ValueError("unknown command %r (place, remove, move, swap, replace, status)" % cmd)
            if len(args) != need[cmd]:
                raise ValueError("%s takes %d argument(s), got %d" % (cmd, need[cmd], len(args)))
            if cmd == "place":
                return self.place(args[0], self.pad_arg(args[1]), why)
            if cmd == "remove":
                return self.remove(args[0], why)
            if cmd == "move":
                return self.move(args[0], self.pad_arg(args[1]), why)
            if cmd == "swap":
                return self.swap(args[0], args[1], why)
            if cmd == "replace":
                return self.replace(args[0], why)
            return True, self.status()
        except (ValueError, OSError) as e:
            return False, str(e)


def parse_on(spec):
    """'REGEX=>tag[@pad]' -> (regex, name, pad); ValueError/re.error on a bad spec."""
    rx, sep, target = spec.rpartition("=>")
    name, _at, pad = target.strip().lower().partition("@")
    if not sep or not rx or not RE_NAME.match(name):
        raise ValueError("--on %r: want REGEX=>tag[@pad]" % spec)
    rxc = re.compile(rx)
    if pad == "*":
        if "pad" not in rxc.groupindex:
            raise ValueError("--on %r: @* needs a (?P<pad>...) group in the regex" % spec)
        pad = None
    elif pad:
        pad = Toypad.pad_arg(pad)
    elif name in STARTER_SLOT:
        pad = STARTER_SLOT[name][0]
    else:
        raise ValueError("--on %r: %s is not a starter tag, give @pad" % (spec, name))
    return rxc, name, pad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-root", default=os.path.join("build", "agent3", "runs"))
    ap.add_argument("--tag", required=True)
    ap.add_argument("--not-before", default="", help="epoch seconds or ISO time (PowerShell 'o')")
    ap.add_argument("--find-timeout", type=float, default=150)
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--trigger-log", default=DEFAULT_TRIGGER, help="regex on game.log ('' = off)")
    ap.add_argument("--trigger-mark", default="", help="input.csv mark name ('' = off)")
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--gap", type=float, default=1.0)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--tags-dir", default=ldtag.DEFAULT_TAGS_DIR)
    ap.add_argument("--then-log", default="", help="regex on game.log, matched after the tags are placed: a second "
                    "action --then-delay s later ('' = off)")
    ap.add_argument("--then-delay", type=float, default=20.0)
    ap.add_argument("--then-mark", default="", help="input.csv mark name, seen after the tags are placed: the second "
                    "action --then-delay s later ('' = off)")
    ap.add_argument("--then-action", choices=["replace", "remove", "place"], default="replace",
                    help="replace = REMOVE the 3 tags, then LOAD them again; remove; place = LOAD again")
    ap.add_argument("--boot", choices=["starter", "none"], default="starter",
                    help="starter = place the 3 starter tags on the trigger (as toypad_sidecar.py); none = no boot placement")
    ap.add_argument("--on", action="append", default=[], metavar="REGEX=>tag[@pad]",
                    help="prompt trigger (repeatable): put the tag on the pad when REGEX matches a game.log line")
    ap.add_argument("--on-delay", type=float, default=1.0)
    ap.add_argument("--on-cooldown", type=float, default=15.0)
    ap.add_argument("--on-max", type=int, default=4)
    ap.add_argument("--zone", action="store_true", help="OFF by default: answer the story's zone step (see above)")
    ap.add_argument("--zone-delay", type=float, default=25.0, help="s from T0 to the first pad 3 command (gameplay-run.ps1 'zone' passes 45)")
    ap.add_argument("--zone-gap", type=float, default=2.0, help="s between zone commands (and from a cue to its first)")
    ap.add_argument("--zone-confirm", type=float, default=10.0, help="s after a step's last LOAD to wait for the handoff")
    ap.add_argument("--led-shots", action="store_true", help="'shot' rows for gameplay-watch.ps1 (see above)")
    a = ap.parse_args(argv)
    try:
        ons = [parse_on(s) for s in a.on]
    except (ValueError, re.error) as e:
        print("bad --on: %s" % e, flush=True)
        return 2
    t_start = time.time()
    nb = parse_not_before(a.not_before)
    print("%s prompt sidecar: tag %s, runs %s, boot %s, trigger log %r mark %r, %d prompt trigger(s)" % (
        datetime.datetime.now().strftime("%H:%M:%S"), a.tag, a.runs_root, a.boot, a.trigger_log, a.trigger_mark,
        len(ons)), flush=True)
    tags = tc.starter_tags(a.tags_dir)
    print("tags ok: " + ", ".join("%s id=%d pad=%d index=%d" % (n, ldtag.figure_id(t), p, i) for n, p, i, t in tags), flush=True)
    for rx, n, p in ons:
        print("on: /%s/ => %s pad %s" % (rx.pattern, n, "from the match" if p is None else p), flush=True)
    if a.zone and not ons:
        print("bad --zone: it needs the --on prompt triggers (T0 counts only after each has fired ok)", flush=True)
        return 2
    print("zone %s%s; led shots %s" % ("ON" if a.zone else "off", " (delay %.0f s, gap %.0f s, confirm %.0f s)" % (
        a.zone_delay, a.zone_gap, a.zone_confirm) if a.zone else "", "on" if a.led_shots else "off"), flush=True)
    run = find_run(a.runs_root, a.tag, nb, a.find_timeout)
    if not run:
        print("no run dir for tag %s within %.0f s" % (a.tag, a.find_timeout), flush=True)
        return 2
    ev_path = os.path.join(run, "toypad-events.csv")
    new = not os.path.exists(ev_path)
    ev = open(ev_path, "a", newline="", encoding="utf-8")
    w = csv.writer(ev)
    if new:
        w.writerow(["wall", "t_sidecar", "game_ts", "kind", "detail"])

    def log(kind, detail, game_ts=""):
        wall = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        w.writerow([wall, "%.2f" % (time.time() - t_start), game_ts, kind, detail])
        ev.flush()
        print("%s %s %s" % (wall, kind, detail), flush=True)

    log("run-dir", run)
    ctl = os.path.join(run, "toypad-ctl")
    os.makedirs(ctl, exist_ok=True)
    log("ctl-dir", ctl)
    gl = Tail(os.path.join(run, "game.log"),
              on_rotate=lambda n: log("log-rotated", "game.log rotated (%d so far); old file read to its end first" % n))
    ic = Tail(os.path.join(run, "input.csv"))
    boot = a.boot == "starter"
    trig = re.compile(a.trigger_log) if (boot and a.trigger_log) else None
    then_re = re.compile(a.then_log) if a.then_log else None
    st = {"port": a.port or tc.default_port(), "listener": False, "trig_at": None, "placed_at": None, "then_at": None,
          "confirms": 0, "removes": 0, "ctl_done": 0, "ctl_err": 0, "route": 0, "route_err": 0}
    pad = Toypad(lambda: st["port"], a.tags_dir, a.gap, log)
    then_done = None
    prompts = [{"rx": rx, "name": n, "pad": p, "fires": 0, "last": None, "due": None, "due_pad": None, "ok": 0}
               for rx, n, p in ons]
    summary = os.path.join(run, "summary.json")
    deadline = t_start + a.timeout
    shots = {"n": 0}

    def shot(label, ts=""):
        if a.led_shots:
            shots["n"] += 1
            log("shot", label, ts)

    zone = Zone(pad, log, shot, lambda: bool(prompts) and all(pr["ok"] >= 1 for pr in prompts),
                a.zone_delay, a.zone_gap, a.zone_confirm) if a.zone else None
    alert = {"start": None, "last": None, "due": [], "n": 0}

    def led(line, ts):
        m = RE_LED.search(line)
        if not m:
            return
        p, rgb, speed = int(m.group(1)), m.group(2), int(m.group(3))
        if zone is not None:
            zone.feed_led(p, rgb, speed, ts)
        if (rgb, speed) == ALERT:
            now = time.time()
            if alert["start"] is None or now - alert["last"] > ALERT_REARM:
                alert["start"], alert["n"] = now, alert["n"] + 1
                alert["due"] = [(now + s, s) for s in ALERT_SHOTS]
                log("alert", "pad %d lit %s speed %d: all-pads fast red state %d starts" % (p, rgb, speed, alert["n"]), ts)
            alert["last"] = now

    def place_starters(why):
        for k, (n, p, _i, _t) in enumerate(tags):
            if k:
                time.sleep(a.gap)
            if n not in pad.on:
                try:
                    pad.place(n, p, why, wait_s=5.0 if k == 0 else 0.0)
                except ValueError as e:
                    log("load", "LOAD %s skipped: %s [%s]" % (n, e, why))

    def do_then():
        if a.then_action in ("replace", "remove"):
            for n, _p, _i, _t in tags:
                if n in pad.on:
                    pad.remove(n, "then")
                    time.sleep(a.gap)
        if a.then_action in ("replace", "place"):
            time.sleep(a.gap)
            place_starters("then")

    def prompt_act(pr):
        n, p = pr["name"], pr["due_pad"]
        if n in pad.on and pad.on[n][0] == p:
            words = ["replace", n]
        elif n in pad.on:
            words = ["move", n, str(p)]
        else:
            words = ["place", n, str(p)]
        ok, msg = pad.run(words, "prompt")
        log("prompt-done", "%s %s: %s" % ("ok" if ok else "FAIL", " ".join(words), msg))
        return ok

    def ctl_poll():
        try:
            names = sorted(os.listdir(ctl))
        except OSError:
            return
        for fn in names:
            if not fn.lower().endswith(".cmd"):
                continue
            path = os.path.join(ctl, fn)
            try:
                s = os.stat(path)
            except OSError:
                return
            if time.time() - s.st_mtime < CTL_MIN_AGE:
                return                                # keep the name order: wait for this file first
            results, ok_all = [], True
            try:
                if s.st_size > CTL_MAX_BYTES:
                    raise ValueError("file is %d bytes (max %d)" % (s.st_size, CTL_MAX_BYTES))
                with open(path, encoding="utf-8-sig", errors="replace") as f:
                    text = f.read()
                cmds = [ln.split("#")[0].strip() for ln in text.splitlines()]
                cmds = [c for c in cmds if c]
                if not cmds:
                    raise ValueError("no command in the file")
                if len(cmds) > CTL_MAX_LINES:
                    raise ValueError("%d commands (max %d)" % (len(cmds), CTL_MAX_LINES))
                for c in cmds:
                    ok, msg = pad.run(c.split(), "ctl " + fn)
                    results.append("%s: %s -> %s" % ("ok" if ok else "ERR", c, msg))
                    log("ctl", "%s %s: %s -> %s" % (fn, "ok" if ok else "ERR", c, msg))
                    if not ok:
                        ok_all = False
                        break
            except PermissionError:
                return                                # still open in the writer: next poll
            except (ValueError, OSError) as e:
                ok_all = False
                results.append("ERR: %s" % e)
                log("ctl", "%s ERR: %s" % (fn, e))
            dst = path[:-4] + (".done" if ok_all else ".err")
            if os.path.exists(dst):
                dst = "%s.%d" % (dst, int(time.time() * 1000))
            try:
                os.replace(path, dst)
                with open(dst, "a", encoding="utf-8") as f:
                    f.write("\n# %s %s\n" % (datetime.datetime.now().strftime("%H:%M:%S"), "done" if ok_all else "error"))
                    f.write("".join("# %s\n" % r for r in results))
            except OSError as e:
                log("ctl", "%s: cannot rename/annotate: %s" % (fn, e))
                return
            st["ctl_done" if ok_all else "ctl_err"] += 1

    def feed(line):
        m = RE_TS.match(line)
        ts = m.group(2) if m else ""
        if not st["listener"]:
            mm = RE_LISTENER.search(line)
            if mm:
                st["listener"] = True
                st["port"] = a.port or int(mm.group(1))
                log("listener", "port %d" % st["port"], ts)
                if not boot:
                    st["placed_at"] = time.time()     # then-* and prompts may act from now on
        if "Toypad" in line:
            kind, detail = decode(line)
            if "Toypad listener: LOAD ->" in line:
                st["confirms"] += 1
                kind = "load-confirm"
            elif "Toypad listener: REMOVE ->" in line:
                st["removes"] += 1
                kind = "remove-confirm"
            log(kind, detail, ts)
        if not st["listener"]:
            return
        if "Toypad" in line and (zone is not None or a.led_shots):
            mc = re.search(r"Toypad listener: LOAD -> pad=([123]) ", line)
            if mc and zone is not None:
                zone.feed_confirm(int(mc.group(1)), ts)
            led(line, ts)
        if trig is not None and st["trig_at"] is None and trig.search(line):
            st["trig_at"] = time.time()
            log("trigger", "log /%s/" % a.trigger_log, ts)
        if then_re is not None and st["placed_at"] is not None and st["then_at"] is None and then_re.search(line):
            st["then_at"] = time.time()
            log("then-trigger", "log /%s/, %s in %.0f s" % (a.then_log, a.then_action, a.then_delay), ts)
        if st["placed_at"] is None:
            return                                    # prompts count only after the boot placement
        now = time.time()
        for pr in prompts:
            if pr["due"] is None and pr["fires"] < a.on_max and (pr["last"] is None or now >= pr["last"] + a.on_cooldown):
                mp = pr["rx"].search(line)
                if not mp:
                    continue
                p = pr["pad"] if pr["pad"] is not None else int(mp.group("pad")) if mp.group("pad") in ("1", "2", "3") else None
                if p is None:
                    continue
                pr["due"], pr["due_pad"] = now + a.on_delay, p
                pr["fires"] += 1
                log("prompt", "%s fire %d/%d: /%s/ -> pad %d in %.1f s" % (
                    pr["name"], pr["fires"], a.on_max, pr["rx"].pattern, p, a.on_delay), ts)
                if zone is not None and zone.t0 is not None:
                    log("zone", "prompt after T0: %s fire %d/%d -> pad %d (zone step %d, state %s)" % (
                        pr["name"], pr["fires"], a.on_max, p, zone.k + 1, zone.state), ts)

    def marks():
        for line in ic.lines():
            parts = line.split(",")
            if len(parts) <= 3 or parts[2] != "mark":
                continue
            name = parts[3].strip()
            if boot and a.trigger_mark and st["trig_at"] is None and name == a.trigger_mark:
                st["trig_at"] = time.time()
                log("trigger", "mark %s" % a.trigger_mark)
            if a.then_mark and st["placed_at"] is not None and st["then_at"] is None and name == a.then_mark:
                st["then_at"] = time.time()
                log("then-trigger", "mark %s, %s in %.0f s" % (a.then_mark, a.then_action, a.then_delay))
            if name.lower().startswith("tp-"):
                words = name[3:].split("-")
                ok, msg = pad.run(words, "mark " + name)
                st["route" if ok else "route_err"] += 1
                log("route", "%s %s: %s -> %s" % (name, "ok" if ok else "ERR", " ".join(words), msg))

    while time.time() < deadline:
        for line in gl.lines():
            feed(line)
        if st["listener"]:
            marks()
            ctl_poll()
        if boot and st["trig_at"] is not None and st["placed_at"] is None and time.time() >= st["trig_at"] + a.delay:
            place_starters("boot")
            st["placed_at"] = time.time()
        if st["then_at"] is not None and then_done is None and time.time() >= st["then_at"] + a.then_delay:
            do_then()
            then_done = time.time()
        for pr in prompts:
            if pr["due"] is not None and time.time() >= pr["due"]:
                pr["ok"] += 1 if prompt_act(pr) else 0
                pr["due"] = None
                pr["last"] = time.time()
        if zone is not None:
            zone.tick()
        while alert["due"] and time.time() >= alert["due"][0][0]:
            _t, s = alert["due"].pop(0)
            shot("alert%d-plus%02ds" % (alert["n"], s))
        if os.path.exists(summary):
            for line in gl.lines():
                feed(line)
            log("end", "run-game finished (summary.json)")
            break
        time.sleep(0.25)
    else:
        log("end", "sidecar timeout %.0f s" % a.timeout)
    want = 3 if boot else 0
    log("result", "listener=%s boot=%s trigger=%s placed=%s load-confirms=%d then=%s remove-confirms=%d prompts=%s "
        "ctl=%d done/%d err route=%d ok/%d err zone=%s zone-skips=%d alerts=%d shots=%d %s" % (
            st["listener"], a.boot, st["trig_at"] is not None, st["placed_at"] is not None, st["confirms"],
            ("%s done" % a.then_action) if then_done else ("triggered, not done" if st["then_at"] else (
                "off" if (then_re is None and not a.then_mark) else "not triggered")),
            st["removes"], " ".join("%s:%d/%d" % (p["name"], p["ok"], p["fires"]) for p in prompts) or "off",
            st["ctl_done"], st["ctl_err"], st["route"], st["route_err"],
            "off" if zone is None else ("%s (step %d)" % (zone.result, zone.k + 1) if zone.result != "done" else "done"),
            0 if zone is None else zone.skips,
            alert["n"], shots["n"], pad.status()))
    ev.close()
    return 0 if st["listener"] and st["confirms"] >= want else 1


if __name__ == "__main__":
    sys.exit(main())
