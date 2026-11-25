"""Apply check of the #33 patches on a scratch copy of rexglue-sdk 5350b1d (M6, session 3, S3T-6).

Never touches the live SDK worktree: the 4 target files are read as blobs with
`git show 5350b1d:<path>` (read-only) into build/agent6/s33-popin/scratch/<name>/, and
`git apply` runs there with GIT_CEILING_DIRECTORIES set, so it can't pick up an outer repo
(the "Skipped patch" trap, RESUME section 7 step 3). After applying it checks that every target
file really changed, that no "Skipped patch" line was printed, and that the reverse check passes.
Then it diffs the nohunk5 result against the full rated patch's result.
Usage: python -B apply_check.py   (prints a report; exit 0 = all checks passed)
"""
import difflib
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE.parents[2]
SDK = WS / "DimensionsRecomp" / "rexglue-sdk"
BASE = "5350b1de99276b7a7be701bf00914f1ee58ce9bc"
FILES = [
    "include/rex/graphics/d3d12/pipeline_cache.h",
    "src/graphics/d3d12/command_processor.cpp",
    "src/graphics/d3d12/pipeline_cache.cpp",
    "src/graphics/frame_stats.h",
]
PATCHES = {"nohunk5": HERE / "s33-popin-nohunk5.patch", "full": HERE / "s33-popin.patch"}
SCRATCH = HERE / "scratch"
fails = []


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def git(args, cwd, env=None):
    # core.autocrlf=false: the system gitconfig sets autocrlf=true, and outside the SDK repo
    # (no .gitattributes `eol=lf`) git apply would write CRLF files.
    p = subprocess.run(["git", "-c", "core.autocrlf=false"] + args, cwd=cwd, env=env,
                       capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


print("SDK HEAD and blobs (read-only):")
rc, head, _ = git(["rev-parse", "HEAD"], SDK)
check(rc == 0 and head.strip() == BASE, "live SDK HEAD = %s (got %s)" % (BASE[:7], head.strip()[:12]))
blobs = {}
for f in FILES:
    rc, bid, _ = git(["rev-parse", "%s:%s" % (BASE, f)], SDK)
    rc2, wid, _ = git(["hash-object", "--", f], SDK)
    check(rc == 0 and rc2 == 0 and bid.strip() == wid.strip(),
          "%s: worktree blob = 5350b1d blob %s" % (f, bid.strip()[:12]))
    p = subprocess.run(["git", "show", "%s:%s" % (BASE, f)], cwd=SDK, capture_output=True)
    check(p.returncode == 0 and b"\r" not in p.stdout, "%s: blob read, LF only" % f)
    blobs[f] = p.stdout

if SCRATCH.exists():
    shutil.rmtree(SCRATCH)
results = {}
for name, patch in PATCHES.items():
    pb = patch.read_bytes()
    print("\n%s: %s, %d bytes, sha256 %s" % (name, patch.name, len(pb), sha(pb)))
    d = SCRATCH / name
    for f in FILES:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_bytes(blobs[f])
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(SCRATCH))
    rc, out, err = git(["rev-parse", "--show-toplevel"], d, env)
    check(rc != 0, "no git repo above the scratch copy (rev-parse rc %d)" % rc)
    for args, label in ((["apply", "--check", "--verbose"], "check"),
                        (["apply", "--verbose"], "apply"),
                        (["apply", "-R", "--check", "--verbose"], "reverse check")):
        rc, out, err = git(args + [str(patch)], d, env)
        text = (out + err).strip()
        print("  $ git %s <patch>  (cwd scratch/%s) -> exit %d" % (" ".join(args), name, rc))
        for line in text.splitlines():
            print("      " + line)
        check(rc == 0, "%s exit 0" % label)
        check("Skipped patch" not in text, "%s: no 'Skipped patch'" % label)
        check("offset" not in text and "fuzz" not in text.lower(), "%s: no offsets or fuzz" % label)
        check(text.count("Checking patch") == 4 or label == "apply",
              "%s: 4 'Checking patch' lines" % label)
    res = {}
    for f in FILES:
        b = (d / f).read_bytes()
        res[f] = b
        check(b != blobs[f], "%s changed (sha256 %s)" % (f, sha(b)[:16]))
        check(b"\r" not in b, "%s: result is LF only" % f)
    results[name] = res
    rc, out, err = git(["apply", "--numstat", str(patch)], d, env)
    print("  numstat:\n      " + out.strip().replace("\n", "\n      "))

print("\nnohunk5 result vs full-patch result (expect: only N1's 3 lines and hunk #5):")
for f in FILES:
    a = results["full"][f].decode().splitlines()
    b = results["nohunk5"][f].decode().splitlines()
    diff = [l for l in difflib.unified_diff(a, b, "full/" + f, "nohunk5/" + f, n=0, lineterm="")]
    for l in diff:
        print("    " + l)
    changed = [l for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    if f.endswith("pipeline_cache.h"):
        check(len(changed) == 3 and all(l.startswith("+  // ") for l in changed),
              "%s: only the 3 N1 comment lines differ" % f)
    elif f.endswith("command_processor.cpp"):
        base_cp = blobs[f].decode().splitlines()
        check(len(changed) == 5, "%s: only hunk #5 differs (4 '-' + 1 '+')" % f)
        i = b.index("bool D3D12CommandProcessor::CanEndSubmissionImmediately() const {")
        j = base_cp.index("bool D3D12CommandProcessor::CanEndSubmissionImmediately() const {")
        check(b[i:i + 3] == base_cp[j:j + 3],
              "%s: CanEndSubmissionImmediately is byte-identical to 5350b1d" % f)
    else:
        check(not changed, "%s: identical" % f)

print("\nresult: %s" % ("PASS" if not fails else "FAIL (%d)" % len(fails)))
rc, st, _ = git(["status", "--porcelain", "--", "src", "include"], SDK)
check(rc == 0 and st.strip() == "", "live SDK src/include still clean afterwards")
sys.exit(1 if fails else 0)
