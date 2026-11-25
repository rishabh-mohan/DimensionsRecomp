"""Read-only check of M2's 4 FINAL bins against build/agent2/final/BIN-PINS.md (M12, session 3).
- MANIFEST.txt sha256 == BIN-PINS pin; every file sha256/16 == BIN-PINS file table; no file outside the table.
- No subdirectory (cache/ or any other) in the bin dir.
- nativefinal/-off rexruntime + rexgpu-xenos byte-equal to native4b-bin; devfinal/-off carry C5BC627B / CB3A2CC9.
- native fingerprint string present in each final exe that BIN-PINS says carries it (native bins).
Usage: python -B final_bins_check.py [WS]   (prints a report; exit 0 = PASS, 1 = FAIL)"""
import hashlib, os, re, sys

WS = sys.argv[1] if len(sys.argv) > 1 else r"<workspace>"
A2 = os.path.join(WS, "build", "agent2")
BINS = ["devfinal", "devfinal-off", "nativefinal", "nativefinal-off"]
NAT_FP = b"1616ce65e973c583"  # exe holds the 16-hex fingerprint only (as native4b: 9b40acbbef4c57b3); the full "LEGO Dimensions native GPU ..." text is in b/nat/gen-on/native-gpu-build.txt
OLD_FP = b"9b40acbbef4c57b3"
WANT_SHARED = {"devfinal": ("C5BC627B", "CB3A2CC9"), "devfinal-off": ("C5BC627B", "CB3A2CC9"),
               "nativefinal": ("A33801D1", "E3CB99CF"), "nativefinal-off": ("A33801D1", "E3CB99CF")}


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


pins_path = os.path.join(A2, "final", "BIN-PINS.md")
pins = open(pins_path, encoding="utf-8-sig").read()
print("BIN-PINS.md sha256", sha(pins_path)[:16])
man_pin = {}
for m in re.finditer(r"^\| (\S+) \| (\S+-bin) \| ([0-9A-F]{64}) \|", pins, re.M):
    man_pin[m.group(1)] = (m.group(2), m.group(3))
files = {}
sec = pins.split("## File hashes", 1)[1].split("\n## ", 1)[0]
for line in sec.splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 5 and "." in cells[0] and cells[0] != "file":
        for b, c in zip(BINS, cells[1:]):
            files.setdefault(b, {})[cells[0]] = None if c == "-" else c.split()[0].upper()

bad = 0
def fail(msg):
    global bad
    bad += 1
    print("  FAIL", msg)

n4 = os.path.join(A2, "native4b-bin")
n4h = {f: sha(os.path.join(n4, f)) for f in ("rexruntime.dll", "rexgpu-xenos.dll")}
for b in BINS:
    d, want_man = man_pin[b]
    bd = os.path.join(A2, d)
    print(f"== {d}")
    got_man = sha(os.path.join(bd, "MANIFEST.txt"))
    print(f"  MANIFEST {got_man[:16]} pin {want_man[:16]}", "OK" if got_man == want_man else "")
    if got_man != want_man:
        fail("MANIFEST sha != BIN-PINS")
    subdirs = [e for e in os.listdir(bd) if os.path.isdir(os.path.join(bd, e))]
    print(f"  subdirs {subdirs or 'none'} (cache/ present: {'cache' in [s.lower() for s in subdirs]})")
    if subdirs:
        fail(f"subdirectories present {subdirs}")
    present = {e for e in os.listdir(bd) if os.path.isfile(os.path.join(bd, e)) and e != "MANIFEST.txt"}
    for fn, want in files[b].items():
        if want is None:
            if fn in present:
                fail(f"{fn} present but BIN-PINS says '-'")
            continue
        p = os.path.join(bd, fn)
        if not os.path.exists(p):
            fail(f"missing {fn}"); continue
        got = sha(p)
        ok = got.startswith(want)
        print(f"  {fn:28s} {got[:16]} {'OK' if ok else 'want ' + want}")
        if not ok:
            fail(f"{fn} sha")
    extra = present - set(files[b])
    if extra:
        fail(f"files not in BIN-PINS table {sorted(extra)}")
    rt, gpu = sha(os.path.join(bd, "rexruntime.dll")), sha(os.path.join(bd, "rexgpu-xenos.dll"))
    wrt, wgpu = WANT_SHARED[b]
    same4b = rt == n4h["rexruntime.dll"] and gpu == n4h["rexgpu-xenos.dll"]
    print(f"  rexruntime {rt[:8]} (want {wrt}), rexgpu {gpu[:8]} (want {wgpu}); byte-equal native4b: {same4b}")
    if not (rt.startswith(wrt) and gpu.startswith(wgpu)):
        fail("runtime/gpu dll identity")
    if b.startswith("native") and not same4b:
        fail("native final dlls differ from native4b")
    if b.startswith("dev") and same4b:
        fail("dev final dlls equal native4b (expected new)")
    if b.startswith("native"):
        fp = contains(os.path.join(bd, "legodimensions.exe"), NAT_FP)
        print(f"  exe contains '{NAT_FP.decode()}': {fp}")
        old = contains(os.path.join(bd, "legodimensions.exe"), OLD_FP)
        print(f"  exe lacks native4b fingerprint {OLD_FP.decode()}: {not old}")
        if not fp:
            fail("native fingerprint missing from exe")
        if old:
            fail("exe still carries the native4b fingerprint")
print("native4b rexruntime", n4h["rexruntime.dll"][:8], "rexgpu", n4h["rexgpu-xenos.dll"][:8])
print("TOTAL BAD", bad)
sys.exit(1 if bad else 0)
