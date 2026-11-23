#!/usr/bin/env python3
"""toypad_sidecar.py - places the virtual starter tags into one harness run of the game.

Started beside harness/run-game.ps1 (by explore.ps1, or by s4b-queue.ps1 for rows with a "toypad" key):
 1. finds the new run dir under --runs-root (name contains -<tag>, created at/after --not-before);
 2. tails <run>/game.log (shared read) for "Toypad listener active on 127.0.0.1:<port>";
 3. waits for the trigger: --trigger-log REGEX (default: pad 3 lit solid white = the front end's C8
    "all pads white" screen, ~8 s after START) and/or --trigger-mark NAME (an input.csv "mark" row);
 4. --delay s later, LOADs Batman (pad 2 / index 0), Gandalf (1/1), Wyldstyle (3/2) with path length 0
    (memory only: the game never writes a tag file), and counts the "Toypad listener: LOAD ->" lines;
 5. logs every Toypad game.log line, decoded, to <run>/toypad-events.csv until run-game writes
    <run>/summary.json, or --timeout.
Writes only <run>/toypad-events.csv and stdout. Never touches build/agent2. Harness-only (decision 1).
"""
import argparse
import csv
import datetime
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ldtag  # noqa: E402
import toypad_client as tc  # noqa: E402

CMD_NAMES = {0xB0: "wake", 0xB1: "seed", 0xB3: "challenge", 0xC0: "colour", 0xC1: "get-colour", 0xC2: "fade",
             0xC3: "flash", 0xC4: "fade-random", 0xC6: "fade-all", 0xC7: "flash-all", 0xC8: "colour-all",
             0xD0: "tag-list", 0xD1: "d1", 0xD2: "read", 0xD3: "write", 0xD4: "model", 0xE1: "pwd", 0xE5: "e5",
             0xF0: "f0", 0xF1: "f1", 0xF2: "f2", 0xF3: "f3"}
RE_LISTENER = re.compile(r"Toypad listener active on 127\.0\.0\.1:(\d+)")
RE_TS = re.compile(r"^\[(\d{4}-\d\d-\d\d (\d\d:\d\d:\d\d\.\d+))\]")
RE_FRAME = re.compile(r"Toypad\[(Write|Read ?)\]\s+((?:[0-9A-F]{2}\s*)+)")
DEFAULT_TRIGGER = r"Toypad: pad 3 mode 1 lit FF FF FF"


class Tail:
    """Follows a log by name, across spdlog-style rotation (game.log -> game.1.log -> game.2.log ...).

    Each call opens the file (shared read), reads on from the last offset and closes it again. When the
    name points at another file than last time (its file id changed, or it is shorter than the offset), the
    old file is read to its end first from its renamed copy (found by file id; game.1.log if the file system
    gives no ids), then any newer copies, then the new file from its start, so no line is lost.
    Fix of 11-22 22:50: the old tail re-opened game.log at the old offset; after a rotation the new file
    never grew past it, so w6gB never saw its trigger line (slow_frame_log_ms=1 rotates every ~45 s).
    on_rotate(n) is called before the lines of the n-th detected rotation are returned.
    """

    def __init__(self, path, keep=9, on_rotate=None):
        self.path = path
        self.pos = 0
        self.buf = b""
        self.fid = None
        self.rotations = 0
        self.on_rotate = on_rotate
        root, ext = os.path.splitext(path)
        self.rotated = ["%s.%d%s" % (root, i, ext) for i in range(1, keep + 1)]

    @staticmethod
    def _read(path, pos):
        """(data, file id, size) of path from pos on; data is None if the file can't be opened."""
        try:
            with open(path, "rb") as f:
                st = os.fstat(f.fileno())
                fid = (st.st_dev, st.st_ino) if st.st_ino else None
                if pos >= st.st_size:
                    return b"", fid, st.st_size
                f.seek(pos)
                return f.read(), fid, st.st_size
        except OSError:
            return None, None, 0

    @staticmethod
    def _fid(path):
        try:
            st = os.stat(path)
        except OSError:
            return None
        return (st.st_dev, st.st_ino) if st.st_ino else None

    def _split(self, data, end_of_file=False):
        self.buf += data
        parts = self.buf.split(b"\n")
        self.buf = parts.pop()
        if end_of_file and self.buf:
            parts.append(self.buf)
            self.buf = b""
        return [p.decode("utf-8", "replace").rstrip("\r") for p in parts]

    def lines(self):
        data, fid, size = self._read(self.path, self.pos)
        if data is None:
            return []
        if self.fid is None and self.pos == 0:
            self.fid = fid
        if fid is not None and self.fid is not None:
            same = fid == self.fid and size >= self.pos
        else:
            same = size >= self.pos
        if same:
            self.pos += len(data)
            return self._split(data)
        # Rotated (or truncated in place): finish the old file, then any newer copies, then the new file.
        self.rotations += 1
        if self.on_rotate:
            self.on_rotate(self.rotations)
        k = None
        if self.fid is not None and fid != self.fid:
            k = next((i for i, p in enumerate(self.rotated) if self._fid(p) == self.fid), None)
        elif self.fid is None and os.path.exists(self.rotated[0]):
            k = 0
        out = []
        if k is not None:
            old, _f, _s = self._read(self.rotated[k], self.pos)
            out += self._split(old or b"", end_of_file=True)
            for p in reversed(self.rotated[:k]):
                mid, _f, _s = self._read(p, 0)
                out += self._split(mid or b"", end_of_file=True)
        else:
            out += self._split(b"", end_of_file=True)
        new, fid, _s = self._read(self.path, 0)
        self.fid = fid
        self.pos = len(new or b"")
        out += self._split(new or b"")
        return out


def parse_not_before(s):
    if not s:
        return time.time()
    try:
        return float(s)
    except ValueError:
        pass
    s2 = re.sub(r"(\.\d{6})\d+", r"\1", s)
    return datetime.datetime.fromisoformat(s2).timestamp()


def find_run(root, tag, not_before, timeout):
    t_end = time.time() + timeout
    while time.time() < t_end:
        best = None
        try:
            for d in os.scandir(root):
                if d.is_dir() and ("-" + tag) in d.name:
                    ct = d.stat().st_ctime
                    if ct >= not_before - 2 and (best is None or ct > best[0]):
                        best = (ct, d.path)
        except OSError:
            pass
        if best:
            return best[1]
        time.sleep(0.5)
    return None


def decode(line):
    """(kind, detail) for a Toypad game.log line."""
    m = RE_FRAME.search(line)
    if not m:
        i = line.find("Toypad")
        return "toypad", line[i:] if i >= 0 else line
    toks = m.group(2).split()
    if len(toks) < 6:
        return "frame", " ".join(toks)
    if m.group(1) == "Write":
        try:
            cmd = int(toks[4], 16)
        except ValueError:
            return "frame", " ".join(toks[:16])
        args = " ".join(toks[6:14])
        return "cmd", "%s %s seq %s args %s" % (toks[4], CMD_NAMES.get(cmd, "?"), toks[5], args)
    if toks[2] == "56" and len(toks) >= 15:
        return "event", "figure %s pad %s index %s uid %s" % ("added" if toks[7] == "00" else "removed(%s)" % toks[7],
                                                            toks[4], toks[6], "".join(toks[8:15]))
    return "reply", "seq %s len %s data %s" % (toks[4], toks[3], " ".join(toks[5:13]))


def main():
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
    a = ap.parse_args()
    t_start = time.time()
    nb = parse_not_before(a.not_before)
    print("%s sidecar: tag %s, runs %s, trigger log %r mark %r" % (datetime.datetime.now().strftime("%H:%M:%S"), a.tag,
                                                                  a.runs_root, a.trigger_log, a.trigger_mark), flush=True)
    # Make sure the tags exist and decode right before the game starts.
    tags = tc.starter_tags(a.tags_dir)
    print("tags ok: " + ", ".join("%s id=%d pad=%d index=%d" % (n, ldtag.figure_id(t), p, i) for n, p, i, t in tags), flush=True)
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
    gl = Tail(os.path.join(run, "game.log"),
              on_rotate=lambda n: log("log-rotated", "game.log rotated (%d so far); old file read to its end first" % n))
    ic = Tail(os.path.join(run, "input.csv")) if (a.trigger_mark or a.then_mark) else None
    trig = re.compile(a.trigger_log) if a.trigger_log else None
    then_re = re.compile(a.then_log) if a.then_log else None
    port = a.port or tc.default_port()
    listener = False
    trig_at = None
    placed_at = None
    then_at = None
    then_done = None
    confirms = 0
    removes = 0
    summary = os.path.join(run, "summary.json")
    deadline = t_start + a.timeout

    def do_then():
        if a.then_action in ("replace", "remove"):
            for n, p, i, _t in tags:
                ok = tc.remove(port, p, i, timeout=5.0)
                log("remove", "REMOVE %s pad=%d index=%d -> %s" % (n, p, i, "hangup-ok" if ok else "FAILED"))
                time.sleep(a.gap)
        if a.then_action in ("replace", "place"):
            time.sleep(a.gap)
            tc.place_starter(port, a.tags_dir, gap_s=a.gap, wait_s=5.0, log=lambda msg: log("load", msg))

    while time.time() < deadline:
        for line in gl.lines():
            m = RE_TS.match(line)
            ts = m.group(2) if m else ""
            if not listener:
                mm = RE_LISTENER.search(line)
                if mm:
                    listener = True
                    port = a.port or int(mm.group(1))
                    log("listener", "port %d" % port, ts)
            if "Toypad" in line:
                kind, detail = decode(line)
                if "Toypad listener: LOAD ->" in line:
                    confirms += 1
                    kind = "load-confirm"
                elif "Toypad listener: REMOVE ->" in line:
                    removes += 1
                    kind = "remove-confirm"
                log(kind, detail, ts)
            if trig is not None and trig_at is None and listener and trig.search(line):
                trig_at = time.time()
                log("trigger", "log /%s/" % a.trigger_log, ts)
            if then_re is not None and placed_at is not None and then_at is None and then_re.search(line):
                then_at = time.time()
                log("then-trigger", "log /%s/, %s in %.0f s" % (a.then_log, a.then_action, a.then_delay), ts)
        if ic is not None and listener:
            for line in ic.lines():
                parts = line.split(",")
                if len(parts) > 3 and parts[2] == "mark":
                    if a.trigger_mark and trig_at is None and parts[3] == a.trigger_mark:
                        trig_at = time.time()
                        log("trigger", "mark %s" % a.trigger_mark)
                    if a.then_mark and placed_at is not None and then_at is None and parts[3] == a.then_mark:
                        then_at = time.time()
                        log("then-trigger", "mark %s, %s in %.0f s" % (a.then_mark, a.then_action, a.then_delay))
        if trig_at is not None and placed_at is None and time.time() >= trig_at + a.delay:
            tc.place_starter(port, a.tags_dir, gap_s=a.gap, wait_s=5.0, log=lambda msg: log("load", msg))
            placed_at = time.time()
        if then_at is not None and then_done is None and time.time() >= then_at + a.then_delay:
            do_then()
            then_done = time.time()
        if os.path.exists(summary):
            for line in gl.lines():
                if "Toypad" in line:
                    m = RE_TS.match(line)
                    kind, detail = decode(line)
                    if "Toypad listener: LOAD ->" in line:
                        confirms += 1
                        kind = "load-confirm"
                    elif "Toypad listener: REMOVE ->" in line:
                        removes += 1
                        kind = "remove-confirm"
                    log(kind, detail, m.group(2) if m else "")
            log("end", "run-game finished (summary.json)")
            break
        time.sleep(0.25)
    else:
        log("end", "sidecar timeout %.0f s" % a.timeout)
    log("result", "listener=%s trigger=%s placed=%s load-confirms=%d/%d then=%s remove-confirms=%d" % (
        listener, trig_at is not None, placed_at is not None, confirms, 6 if a.then_action in ("replace", "place") and then_done else 3,
        ("%s done" % a.then_action) if then_done else ("triggered, not done" if then_at else ("off" if (then_re is None and not a.then_mark) else "not triggered")),
        removes))
    ev.close()
    return 0 if confirms >= 3 else 1


if __name__ == "__main__":
    sys.exit(main())
