"""Replace the lines from a start prefix (inclusive) to an end prefix (exclusive) with the text of a file.

Usage: python splice_notes.py NOTES START_PREFIX END_PREFIX NEW_TEXT_FILE [--expect-sha PREFIX]
Each prefix must match exactly one line, and END must come after START. The notes stay LF, no BOM.
"""
import argparse
import hashlib
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notes")
    ap.add_argument("start")
    ap.add_argument("end")
    ap.add_argument("new")
    ap.add_argument("--expect-sha")
    ns = ap.parse_args()
    data = open(ns.notes, "rb").read()
    sha = hashlib.sha256(data).hexdigest().upper()
    if ns.expect_sha and not sha.startswith(ns.expect_sha.upper()):
        sys.exit(f"notes sha {sha} does not start with {ns.expect_sha}")
    if data.startswith(b"\xef\xbb\xbf") or b"\r\n" in data:
        sys.exit("notes have a BOM or CRLF; refusing")
    lines = data.decode("utf-8").split("\n")
    s = [i for i, line in enumerate(lines) if line.startswith(ns.start)]
    e = [i for i, line in enumerate(lines) if line.startswith(ns.end)]
    if len(s) != 1 or len(e) != 1 or e[0] <= s[0]:
        sys.exit(f"start matches {s}, end matches {e}")
    new = open(ns.new, "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
    if not new.endswith("\n"):
        new += "\n"
    new_lines = new[:-1].split("\n")
    out = "\n".join(lines[: s[0]] + new_lines + lines[e[0]:]).encode("utf-8")
    with open(ns.notes, "wb") as f:
        f.write(out)
    print(f"replaced lines {s[0] + 1}-{e[0]} ({e[0] - s[0]} lines) with {len(new_lines)} lines; "
          f"sha {sha[:8]} -> {hashlib.sha256(out).hexdigest().upper()[:8]}, {len(out)} B")


if __name__ == "__main__":
    main()
