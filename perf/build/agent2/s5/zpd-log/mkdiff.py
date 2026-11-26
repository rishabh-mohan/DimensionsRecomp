# Makes zpd-log.diff (a7e79c0-relative, LF) from base/ vs ov/ and checks
# line endings and line lengths of the added lines. Static only, no compiler.
import subprocess, sys, hashlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
REL = "src/graphics/d3d12/command_processor.cpp"
base = os.path.join(HERE, "base", "command_processor.cpp")
ov = os.path.join(HERE, "ov", *REL.split("/"))

for p in (base, ov):
    d = open(p, "rb").read()
    assert b"\r\n" not in d, p + " has CRLF"

r = subprocess.run(["git", "diff", "--no-index", "--no-color", "-U3", base, ov],
                   capture_output=True, cwd=HERE)
assert r.returncode == 1, (r.returncode, r.stderr)
lines = r.stdout.decode("utf-8").split("\n")
out = []
for l in lines:
    if l.startswith("diff --git "):
        l = "diff --git a/%s b/%s" % (REL, REL)
    elif l.startswith("index "):
        continue
    elif l.startswith("--- "):
        l = "--- a/" + REL
    elif l.startswith("+++ "):
        l = "+++ b/" + REL
    out.append(l)
text = "\n".join(out)
if not text.endswith("\n"):
    text += "\n"
long_ = [l for l in out if l.startswith("+") and not l.startswith("+++") and len(l) - 1 > 100]
dst = os.path.join(HERE, "zpd-log.diff")
open(dst, "wb").write(text.encode("utf-8"))
print("hunks", sum(1 for l in out if l.startswith("@@")),
      "added", sum(1 for l in out if l.startswith("+") and not l.startswith("+++")),
      "removed", sum(1 for l in out if l.startswith("-") and not l.startswith("---")))
print("lines over 100 cols:", len(long_))
for l in long_:
    print("  ", len(l) - 1, l)
print("zpd-log.diff sha256", hashlib.sha256(text.encode("utf-8")).hexdigest().upper())
sys.exit(1 if long_ else 0)
