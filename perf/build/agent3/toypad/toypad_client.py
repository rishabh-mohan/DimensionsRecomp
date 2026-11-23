#!/usr/bin/env python3
"""toypad_client.py - client for the game's emulated Toy Pad listener (127.0.0.1:9191).

Protocol (emulated_toypad.cpp HandleCommand L872-966). Header = 5 bytes
[cmd, pad, index, old_pad, old_index]; pad 1 centre / 2 left / 3 right; index 0..6.
  0x01 LOAD    header + 180-byte tag + u16 LE path length + path. Path length 0 keeps
               the tag in memory only (the game writes a tag file only when it has a path).
               Server logs "Toypad listener: LOAD -> pad=P index=I (path len N)", hangs up.
  0x02 REMOVE  server logs "Toypad listener: REMOVE -> pad=P index=I", hangs up.
  0x03 MOVE    old_pad/old_index = source; 500 ms pickup delay; hangs up.
  0x04 GET_LED 40-byte snapshot: 'L', serial, version, regions(3), then 3 x 12 bytes
               (pad, mode, r, g, b, from r/g/b, on, off, count, speed). Stays connected.
A bad pad/index: server logs "rejected message ..." and hangs up without a reply.

  python toypad_client.py starter [--tags-dir DIR] [--port N] [--wait-listener S]
  python toypad_client.py load --tag FILE --pad P --index I [--path ""]
  python toypad_client.py remove --pad P --index I
  python toypad_client.py move --from-pad P --from-index I --pad P2 --index I2
  python toypad_client.py leds [--json]
Port: --port, else env REXGLUE_TOYPAD_PORT / XENIA_TOYPAD_PORT (as the game), else 9191.
"""
import argparse
import json
import os
import socket
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ldtag  # noqa: E402

DEFAULT_PORT = 9191
LED_SNAPSHOT_SIZE = 40


def default_port():
    for var in ("REXGLUE_TOYPAD_PORT", "XENIA_TOYPAD_PORT"):
        v = os.environ.get(var, "").strip()
        if v.isdigit() and 0 < int(v) < 65536:
            return int(v)
    return DEFAULT_PORT


def header(cmd, pad, index, old_pad=0, old_index=0):
    return bytes((cmd & 0xFF, pad & 0xFF, index & 0xFF, old_pad & 0xFF, old_index & 0xFF))


def connect(port, timeout=5.0, wait_s=0.0):
    deadline = time.time() + max(0.0, wait_s)
    while True:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
            s.settimeout(timeout)
            return s
        except OSError:
            if time.time() >= deadline:
                raise
            time.sleep(0.5)


def wait_hangup(s, timeout):
    """(True, b'') once the server closes the connection; (False, data) on bytes or timeout."""
    s.settimeout(timeout)
    try:
        data = s.recv(256)
        if not data:
            return True, b""
        return False, data
    except socket.timeout:
        return False, b""
    except (ConnectionResetError, ConnectionAbortedError):
        return True, b""


def load(port, tag, pad, index, path="", timeout=5.0, wait_s=0.0):
    tag = bytes(tag)
    if len(tag) != ldtag.TAG_SIZE:
        raise ValueError("tag must be %d bytes" % ldtag.TAG_SIZE)
    p = path.encode("utf-8")
    msg = header(0x01, pad, index) + tag + struct.pack("<H", len(p)) + p
    with connect(port, timeout, wait_s) as s:
        s.sendall(msg)
        ok, extra = wait_hangup(s, timeout)
    return ok


def remove(port, pad, index, timeout=5.0, wait_s=0.0):
    with connect(port, timeout, wait_s) as s:
        s.sendall(header(0x02, pad, index))
        ok, extra = wait_hangup(s, timeout)
    return ok


def move(port, from_pad, from_index, pad, index, timeout=5.0, wait_s=0.0):
    with connect(port, timeout, wait_s) as s:
        s.sendall(header(0x03, pad, index, from_pad, from_index))
        ok, extra = wait_hangup(s, timeout + 1.0)
    return ok


def get_leds(port, timeout=3.0, wait_s=0.0):
    """Raw GET_LED reply (40 bytes when supported; shorter if the listener hung up)."""
    with connect(port, timeout, wait_s) as s:
        s.sendall(header(0x04, 1, 0))
        buf = b""
        try:
            while len(buf) < LED_SNAPSHOT_SIZE:
                d = s.recv(LED_SNAPSHOT_SIZE - len(buf))
                if not d:
                    break
                buf += d
        except (socket.timeout, ConnectionResetError, ConnectionAbortedError):
            pass
    return buf


def parse_leds(buf):
    if len(buf) != LED_SNAPSHOT_SIZE or buf[0] != 0x4C:
        return None
    regions = []
    for i in range(min(3, buf[3])):
        r = buf[4 + i * 12: 16 + i * 12]
        regions.append({"pad": r[0], "mode": r[1], "rgb": "%02X%02X%02X" % (r[2], r[3], r[4]),
                        "from": "%02X%02X%02X" % (r[5], r[6], r[7]),
                        "on": r[8], "off": r[9], "count": r[10], "speed": r[11]})
    return {"serial": buf[1], "version": buf[2], "regions": regions}


def leds_text(parsed):
    if not parsed:
        return "unsupported"
    return " ".join("p%d:m%d:%s" % (r["pad"], r["mode"], r["rgb"]) for r in parsed["regions"])


def starter_tags(tags_dir):
    """Load (making them if missing) the starter tags: [(name, pad, index, bytes)]."""
    out = []
    missing = [n for n, _, _ in ldtag.STARTER if not os.path.exists(os.path.join(tags_dir, n + ".bin"))]
    if missing:
        ldtag.write_starter(tags_dir)
    for name, pad, index in ldtag.STARTER:
        tag = ldtag.read_tag(os.path.join(tags_dir, name + ".bin"))
        if ldtag.figure_id(tag) != ldtag.CHARACTERS[name]:
            raise ValueError("%s.bin decodes to id %d" % (name, ldtag.figure_id(tag)))
        out.append((name, pad, index, tag))
    return out


def place_starter(port, tags_dir=ldtag.DEFAULT_TAGS_DIR, gap_s=1.0, wait_s=0.0, log=print):
    results = []
    for k, (name, pad, index, tag) in enumerate(starter_tags(tags_dir)):
        if k:
            time.sleep(gap_s)
        t0 = time.time()
        try:
            ok = load(port, tag, pad, index, "", wait_s=wait_s if k == 0 else 0.0)
            err = ""
        except OSError as e:
            ok, err = False, str(e)
        results.append((name, pad, index, ok))
        log("LOAD %s id=%d pad=%d index=%d path_len=0 -> %s%s (%.2f s)" % (
            name, ldtag.CHARACTERS[name], pad, index, "hangup-ok" if ok else "FAIL", (" " + err) if err else "", time.time() - t0))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--wait-listener", type=float, default=0.0, help="retry the first connect for S seconds")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("starter")
    s.add_argument("--tags-dir", default=ldtag.DEFAULT_TAGS_DIR)
    s.add_argument("--gap", type=float, default=1.0)
    lo = sub.add_parser("load")
    lo.add_argument("--tag", required=True)
    lo.add_argument("--pad", type=int, required=True)
    lo.add_argument("--index", type=int, required=True)
    lo.add_argument("--path", default="", help="'' (default) = memory only, no tag file writes")
    rm = sub.add_parser("remove")
    rm.add_argument("--pad", type=int, required=True)
    rm.add_argument("--index", type=int, required=True)
    mv = sub.add_parser("move")
    mv.add_argument("--from-pad", type=int, required=True)
    mv.add_argument("--from-index", type=int, required=True)
    mv.add_argument("--pad", type=int, required=True)
    mv.add_argument("--index", type=int, required=True)
    le = sub.add_parser("leds")
    le.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    port = a.port or default_port()

    if a.cmd == "starter":
        res = place_starter(port, a.tags_dir, a.gap, a.wait_listener)
        return 0 if all(r[3] for r in res) else 1
    if a.cmd == "load":
        ok = load(port, ldtag.read_tag(a.tag), a.pad, a.index, a.path, wait_s=a.wait_listener)
        print("LOAD %s pad=%d index=%d -> %s" % (a.tag, a.pad, a.index, "hangup-ok" if ok else "FAIL"))
        return 0 if ok else 1
    if a.cmd == "remove":
        ok = remove(port, a.pad, a.index, wait_s=a.wait_listener)
        print("REMOVE pad=%d index=%d -> %s" % (a.pad, a.index, "hangup-ok" if ok else "FAIL"))
        return 0 if ok else 1
    if a.cmd == "move":
        ok = move(port, a.from_pad, a.from_index, a.pad, a.index, wait_s=a.wait_listener)
        print("MOVE %d/%d -> %d/%d -> %s" % (a.from_pad, a.from_index, a.pad, a.index, "hangup-ok" if ok else "FAIL"))
        return 0 if ok else 1
    if a.cmd == "leds":
        buf = get_leds(port, wait_s=a.wait_listener)
        p = parse_leds(buf)
        print(json.dumps(p) if a.json else "LEDS %s (%d bytes)" % (leds_text(p), len(buf)))
        return 0 if p else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
