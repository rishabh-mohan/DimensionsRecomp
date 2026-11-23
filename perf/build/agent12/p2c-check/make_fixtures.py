#!/usr/bin/env python3
"""Real-format fixtures for p2c_check.py (Agent 12, task #11, 2026-11-22).

No S4b run exists yet, so this takes a real S4a run (slow-frame lines without s4-p2c's field)
and appends the field in the diff's exact format, ' | memexport full-buffer {}x (total {})'
(build/agent12/s4-p2c/memexport-full-buffer-counter.diff L32-33, the last field of the line),
to every slow-frame line, as an S4b build prints it. Everything else is copied unchanged,
with the same line endings. Rotated logs are kept, and T runs on across them, oldest first.

Writes three run dirs under OUT:
  pass/  F 0, T 0 on every line                                -> PASS (total 0), exit 0
  fail/  F 2 on the 10th slow-frame line, and T +3 more at the
         20th (3 fallbacks in frames that were not logged)     -> FAIL (total 5), exit 1
  cut/   as pass/, but the last slow-frame line has no field    -> PASS (total 0), WARN cut off

usage: python make_fixtures.py <S4a run dir> <out dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2c_check  # noqa: E402

FIELD = " | memexport full-buffer {}x (total {})"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    files, missing = p2c_check.resolve([src])
    if missing or not files:
        print(f"not found: {', '.join(missing) or src}")
        return 2
    data = []
    for path in files:
        with open(path, encoding="utf-8", errors="replace", newline="") as fh:
            data.append((os.path.basename(path), fh.read().splitlines(keepends=True)))
    n_slow = sum(1 for _, lines in data for line in lines if p2c_check.SLOW.search(line))
    if n_slow < 25:
        print(f"need >= 25 slow-frame lines, found {n_slow}")
        return 2
    if any(p2c_check.FIELD.search(line) for _, lines in data for line in lines):
        print("the source already has the counter field")
        return 2
    for kind in ("pass", "fail", "cut"):
        d = os.path.join(out, kind)
        os.makedirs(d, exist_ok=True)
        n = t = 0
        for name, lines in data:
            res = []
            for line in lines:
                if not p2c_check.SLOW.search(line):
                    res.append(line)
                    continue
                n += 1
                body = line.rstrip("\r\n")
                eol = line[len(body):]
                f = 0
                if kind == "fail":
                    if n == 10:
                        f = 2
                    if n == 20:
                        t += 3
                t += f
                if kind == "cut" and n == n_slow:
                    res.append(line)
                else:
                    res.append(body + FIELD.format(f, t) + eol)
            with open(os.path.join(d, name), "w", encoding="utf-8", newline="") as fh:
                fh.write("".join(res))
        print(f"{kind}: {len(data)} log(s) ({', '.join(name for name, _ in data)}), "
              f"{n} slow-frame lines, final T {t} -> {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
