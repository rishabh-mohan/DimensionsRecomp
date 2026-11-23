"""Agent 6: make and verify the fix A patches (scratch copies only; never touches the live tree).

Steps:
1. git diff --no-index orig -> new (fix-a.patch) and new -> new-commit (fix-a-commit.patch),
   with paths rewritten to be relative to DimensionsRecomp/ (a/rexlego/src/...).
2. git apply --check / apply / -R --check on fresh scratch copies of the live files; compare hashes.
3. clang -fsyntax-only of the patched files, using build/dev/compile_commands.json with the
   source swapped, outputs and dependency files stripped (nothing is written to build/dev).
"""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIVE = ROOT / "DimensionsRecomp"
FILES = ["rexlego/src/settings_registry.cpp", "rexlego/src/settings_preferences.cpp"]
# The ceiling stops git from finding an enclosing repository, so git apply works on the
# scratch files relative to the cwd (inside a work tree it would resolve paths from the top
# of that tree and silently skip them).
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_CEILING_DIRECTORIES=str(HERE / "apply-test"))
GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false"]


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest().upper()


def run(cmd, cwd, check=True):
    proc = subprocess.run(cmd, cwd=str(cwd), env=ENV, capture_output=True)
    if check and proc.returncode not in (0,):
        print("FAIL:", cmd, proc.returncode)
        print(proc.stdout.decode("utf-8", "replace")[-3000:])
        print(proc.stderr.decode("utf-8", "replace")[-3000:])
        sys.exit(1)
    return proc


def make_patch(old_tree, new_tree, out_name, rel=None):
    old_arg = old_tree if rel is None else old_tree + "/" + rel
    new_arg = new_tree if rel is None else new_tree + "/" + rel
    proc = subprocess.run(GIT + ["diff", "--no-index", "--no-color", "--no-ext-diff", old_arg, new_arg],
                          cwd=str(HERE), env=ENV, capture_output=True)
    if proc.returncode != 1:
        sys.exit("FAIL: git diff rc=%d %s" % (proc.returncode, proc.stderr.decode("utf-8", "replace")))
    data = proc.stdout
    data = data.replace(b"a/" + old_tree.encode() + b"/", b"a/").replace(b"b/" + new_tree.encode() + b"/", b"b/")
    # Index lines name scratch blobs only; drop them so the patch reads like a plain unified diff.
    data = re.sub(rb"(?m)^index [0-9a-f]+\.\.[0-9a-f]+ [0-9]+\n", b"", data)
    (HERE / out_name).write_bytes(data)
    print("%-20s sha256 %s bytes %d" % (out_name, hashlib.sha256(data).hexdigest().upper(), len(data)))
    return HERE / out_name


def fresh_copy(name):
    dst = HERE / "apply-test" / name
    if dst.exists():
        shutil.rmtree(dst)
    for rel in FILES:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LIVE / rel, dst / rel)
    return dst


p_a = make_patch("orig", "new", "fix-a.patch")
p_c = make_patch("new", "new-commit", "fix-a-commit.patch", FILES[0])
probe = run(GIT + ["rev-parse", "--is-inside-work-tree"], fresh_copy("probe"), check=False)
print("probe outside work tree:", probe.returncode != 0, probe.stdout.decode().strip())
if probe.returncode == 0:
    sys.exit("FAIL: apply-test is still inside a git work tree")

# fix-a on live copies
t = fresh_copy("a")
run(GIT + ["apply", "--check", "-v", str(p_a)], t)
run(GIT + ["apply", str(p_a)], t)
for rel in FILES:
    assert sha(t / rel) == sha(HERE / "new" / rel), rel
run(GIT + ["apply", "-R", "--check", str(p_a)], t)
print("fix-a.patch: apply --check OK, result == new/, -R --check OK")

# fix-a-commit on top of fix-a, and standalone on live copies
run(GIT + ["apply", "--check", str(p_c)], t)
run(GIT + ["apply", str(p_c)], t)
assert sha(t / FILES[0]) == sha(HERE / "new-commit" / FILES[0])
t2 = fresh_copy("c-only")
run(GIT + ["apply", "--check", str(p_c)], t2)
print("fix-a-commit.patch: OK on top of fix-a (== new-commit/), and standalone --check OK")

# live tree must still be untouched
for rel, want in zip(FILES, ["A37337001EBDC277B2B94D783939A47096423F0AE8962C8B879A6A60B4F8BA4B",
                             "C78112AA6E50F79D8E6154A37E47CC129C43EAD2E39EC066927374EFBF34B5F0"]):
    assert sha(LIVE / rel) == want, rel
print("live files unchanged")

# syntax-only compile of the patched files
entries = json.loads((ROOT / "build/dev/compile_commands.json").read_text(encoding="utf-8"))
targets = {str(LIVE / rel).lower(): HERE / "new-commit" / rel if rel == FILES[0] else HERE / "new" / rel
           for rel in FILES}
for entry in entries:
    src = os.path.normpath(entry["file"]).lower()
    if src not in targets:
        continue
    patched = targets.pop(src)
    for label, path in (("orig", HERE / "orig" / patched.relative_to(HERE).as_posix().split("/", 1)[1]),
                        ("patched", patched)):
        cmd = entry["command"]
        cmd = re.sub(r"\s-o\s+\S+", " ", cmd)
        cmd = re.sub(r"\s-M(?:F|T|Q)\s+\S+", " ", cmd)
        cmd = re.sub(r"\s-M(?:M)?D(?=\s)", " ", cmd)
        cmd = re.sub(r"\s-c(?=\s)", " ", cmd)
        raw_file = entry["file"]
        if raw_file not in cmd:
            alt = raw_file.replace("\\", "/")
            if alt not in cmd:
                sys.exit("FAIL: source path not found in command for " + raw_file)
            raw_file = alt
        cmd = cmd.replace(raw_file, '-I"%s" -fsyntax-only "%s"' % (str(LIVE / "rexlego/src"), str(path)))
        proc = subprocess.run(cmd, cwd=entry["directory"], capture_output=True)
        err = proc.stderr.decode("utf-8", "replace")
        lines = sorted(set(re.sub(r"^.*?[\\/]rexlego[\\/]", "", l) for l in err.splitlines() if "warning:" in l))
        print("syntax-only %-8s %s rc=%d warnings=%d errors=%d" % (label, path.relative_to(HERE), proc.returncode,
                                                                  err.count("warning:"), err.count("error:")))
        for l in lines:
            print("    " + l[:200])
        if proc.returncode != 0:
            print(err[-4000:])
            sys.exit(1)
if targets:
    print("WARN: no compile_commands entry for", list(targets))
print("ALL OK")
