#!/usr/bin/env python3
"""fake_listener.py - stand-in for the game's Toy Pad listener, for the self-test only.

Mirrors EmulatedToypad::HandleCommand (emulated_toypad.cpp L872-966): GET_LED is
answered before the pad checks (40-byte snapshot, connection stays open); a bad
pad/index is rejected with a hang-up; LOAD reads tag + u16 LE path length + path and
decodes the figure id with ldtag.figure_id (as LoadFigure -> GetFigureId does);
REMOVE; MOVE with a 0.5 s pickup delay; unknown commands are logged. Every
placement command ends with a hang-up.

  python fake_listener.py [--port 0]     (prints the port, logs events until Ctrl+C)
"""
import argparse
import os
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ldtag  # noqa: E402


class FakeListener:
    def __init__(self, port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(16)
        self.port = self.sock.getsockname()[1]
        self.events = []
        self.slots = {}
        self.serial = 0
        self.leds = [[i + 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for i in range(3)]
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def set_led(self, pad, mode, r, g, b):
        with self.lock:
            self.leds[pad - 1][1:5] = [mode, r, g, b]
            self.serial = (self.serial + 1) & 0xFF

    def _event(self, *e):
        with self.lock:
            self.events.append(e)

    @staticmethod
    def _recv_all(c, n):
        b = b""
        while len(b) < n:
            d = c.recv(n - len(b))
            if not d:
                return None
            b += d
        return b

    def _run(self):
        while self.running:
            try:
                c, _ = self.sock.accept()
            except OSError:
                break
            threading.Thread(target=self._client, args=(c,), daemon=True).start()

    def _client(self, c):
        try:
            c.settimeout(10)
            while self.running and self._handle(c):
                pass
        except OSError:
            pass
        finally:
            c.close()

    def _handle(self, c):
        h = self._recv_all(c, 5)
        if h is None:
            return False
        cmd, pad, index, old_pad, old_index = h
        if cmd == 0x04:
            with self.lock:
                snap = bytes([0x4C, self.serial, 2, 3]) + b"".join(bytes(r) for r in self.leds)
            c.sendall(snap)
            return True
        if pad < 1 or pad > 3 or index >= 7:
            self._event("rejected", cmd, pad, index)
            return False
        if cmd == 0x01:
            tag = self._recv_all(c, ldtag.TAG_SIZE)
            ln = self._recv_all(c, 2) if tag is not None else None
            if ln is None:
                self._event("short-load", pad, index)
                return False
            n = ln[0] | (ln[1] << 8)
            path = b""
            if n:
                path = self._recv_all(c, n)
                if path is None:
                    self._event("short-path", pad, index)
                    return False
            fid = ldtag.figure_id(tag)
            with self.lock:
                self.slots[index] = (pad, fid)
            self._event("load", pad, index, fid, n, ldtag.tag_uid(tag).hex().upper())
        elif cmd == 0x02:
            with self.lock:
                self.slots.pop(index, None)
            self._event("remove", pad, index)
        elif cmd == 0x03:
            if old_pad < 1 or old_pad > 3 or old_index >= 7:
                self._event("rejected-move", old_pad, old_index)
                return False
            with self.lock:
                src = self.slots.pop(old_index, None)
            if src is None:
                self._event("move-empty", old_pad, old_index)
                return False
            time.sleep(0.5)
            with self.lock:
                self.slots[index] = (pad, src[1])
            self._event("move", old_pad, old_index, pad, index)
        else:
            self._event("unknown", cmd)
        return False

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=0)
    a = ap.parse_args()
    fl = FakeListener(a.port)
    print("fake listener on 127.0.0.1:%d" % fl.port, flush=True)
    seen = 0
    try:
        while True:
            time.sleep(0.2)
            while seen < len(fl.events):
                print(fl.events[seen], flush=True)
                seen += 1
    except KeyboardInterrupt:
        fl.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
