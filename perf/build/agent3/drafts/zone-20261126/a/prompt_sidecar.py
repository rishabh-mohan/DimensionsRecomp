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
        "ctl=%d done/%d err route=%d ok/%d err %s" % (
            st["listener"], a.boot, st["trig_at"] is not None, st["placed_at"] is not None, st["confirms"],
            ("%s done" % a.then_action) if then_done else ("triggered, not done" if st["then_at"] else (
                "off" if (then_re is None and not a.then_mark) else "not triggered")),
            st["removes"], " ".join("%s:%d/%d" % (p["name"], p["ok"], p["fires"]) for p in prompts) or "off",
            st["ctl_done"], st["ctl_err"], st["route"], st["route_err"], pad.status()))
    ev.close()
    return 0 if st["listener"] and st["confirms"] >= want else 1


if __name__ == "__main__":
    sys.exit(main())
