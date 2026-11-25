"""S3T-1 (a)+(c): recompute every build/agent2/*-bin/MANIFEST.txt file hash; read-only.
Manifest data lines: name \t size \t mtime \t sha256 \t source. Run at Idle priority.
Usage: python manifest_check.py [WS]   (writes nothing; prints a report)"""
import hashlib, os, sys, glob, re

WS = sys.argv[1] if len(sys.argv) > 1 else r"<workspace>"
FP = b"9b40acbbef4c57b3"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def contains(path, needle):
    tail = b""
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            if needle in tail + chunk:
                return True
            tail = chunk[-len(needle):]
    return False


bad = 0
for man in sorted(glob.glob(os.path.join(WS, "build", "agent2", "*-bin", "MANIFEST.txt"))):
    d = os.path.dirname(man)
    name = os.path.basename(d)
    lines = [l for l in open(man, encoding="utf-8-sig", errors="replace").read().splitlines()
             if l and not l.startswith("#")]
    listed = set()
    ok = 0
    for l in lines:
        p = l.split("\t")
        if len(p) < 4:
            print(f"{name}: UNPARSED line {l[:80]!r}")
            bad += 1
            continue
        fn, size, want = p[0], int(p[1]), p[3].upper()
        listed.add(fn.lower())
        fp = os.path.join(d, fn)
        if not os.path.exists(fp):
            print(f"{name}: MISSING {fn}"); bad += 1; continue
        got_size = os.path.getsize(fp)
        got = sha(fp)
        if got != want or got_size != size:
            print(f"{name}: MISMATCH {fn} size {got_size}/{size} sha {got[:16]} want {want[:16]}"); bad += 1
        else:
            ok += 1
    extra = [f for f in os.listdir(d) if f.lower() not in listed and f != "MANIFEST.txt"]
    fpline = re.search(r"native GPU ([0-9a-f]{16})", open(man, encoding="utf-8", errors="replace").read())
    print(f"{name}: {ok}/{len(lines)} OK; manifest sha256 {sha(man)[:16]}; fingerprint {fpline.group(1) if fpline else '-'}"
          + (f"; unlisted: {extra}" if extra else ""))

# (c) native4b fingerprint in the exe
exe = os.path.join(WS, "build", "agent2", "native4b-bin", "legodimensions.exe")
print("native4b exe contains", FP.decode(), "=", contains(exe, FP))
print("TOTAL BAD", bad)
