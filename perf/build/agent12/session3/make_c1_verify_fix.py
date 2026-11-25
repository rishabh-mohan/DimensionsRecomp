"""S3T-12: stage the C1 verify-only fix (RESUME s6 item 2 option (b)) and apply-check it.
Read-only on DimensionsRecomp; writes only under build/agent12/session3/c1-verify-fix/.
Steps: copy live file -> orig/, make new/ by one exact anchor insert, write the diff
(git diff --no-index, repo-relative a/ b/ headers), then apply it to a fresh scratch copy
in a throwaway git repo and check the result is byte-identical to new/."""
import hashlib, os, shutil, subprocess, sys

WS = r"<workspace>"
REL = "src/graphics/shared_memory.cpp"
LIVE = os.path.join(WS, "DimensionsRecomp", "rexglue-sdk", *REL.split("/"))
OUT = os.path.join(WS, "build", "agent12", "session3", "c1-verify-fix")
EXPECT_LIVE = "A4A31038ABDFF94A1B97D28A13EE2ACBB67F44DC596F7A964C8C7493050390C6"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


src = open(LIVE, "rb").read()
assert hashlib.sha256(src).hexdigest().upper() == EXPECT_LIVE, "live file changed since the read"
nl = b"\r\n" if b"\r\n" in src else b"\n"

anchor = nl.join([
    b"      system_page_flags_valid_[i] |= valid_bits;",
    b"      uint64_t& gpu_written = system_page_flags_valid_and_gpu_written_[i];",
    b"      gpu_written = written_by_gpu ? (gpu_written | valid_bits) : (gpu_written & ~valid_bits);",
    b"    }",
    b"  }",
]) + nl
insert = nl.join([
    b"      system_page_flags_valid_[i] |= valid_bits;",
    b"      uint64_t& gpu_written = system_page_flags_valid_and_gpu_written_[i];",
    b"      gpu_written = written_by_gpu ? (gpu_written | valid_bits) : (gpu_written & ~valid_bits);",
    b"    }",
    b"",
    b"    // S4 C1 verify: a page that turns valid has no upload hash until",
    b"    // KeepWatchVerifyRecord below re-hashes it. Without P2, G is released between",
    b"    // here and that re-hash, and the watch is armed in between, so a write fault in",
    b"    // the gap would run the F check (and a keep-watch protect the K check) against",
    b"    // the page's previous upload. Hash 0 makes both checks skip the page until the",
    b"    // re-hash. With P2, G is held throughout, so nothing observable changes. Valid",
    b"    // bits are set only above, so a valid page's hash is 0 or from its latest upload.",
    b"    if (keep_watch_verify_hashes_) {",
    b"      std::fill_n(&keep_watch_verify_hashes_[valid_page_first],",
    b"                  valid_page_last - valid_page_first + 1, uint64_t(0));",
    b"    }",
    b"  }",
]) + nl
assert src.count(anchor) == 1, "anchor not unique"
new = src.replace(anchor, insert)

for sub in ("orig", "new"):
    d = os.path.join(OUT, sub, *os.path.dirname(REL).split("/"))
    os.makedirs(d, exist_ok=True)
open(os.path.join(OUT, "orig", *REL.split("/")), "wb").write(src)
open(os.path.join(OUT, "new", *REL.split("/")), "wb").write(new)

# diff with repo-relative headers (run from OUT so the paths are orig/... and new/...)
r = subprocess.run(["git", "diff", "--no-index", "--no-color", "--src-prefix=a/", "--dst-prefix=b/",
                    "orig/" + REL, "new/" + REL], cwd=OUT, capture_output=True)
assert r.returncode == 1, r.stderr
diff = r.stdout.replace(b"a/orig/", b"a/").replace(b"b/new/", b"b/")
open(os.path.join(OUT, "c1-verify-fix.diff"), "wb").write(diff)

# apply check on a fresh scratch copy inside its own throwaway repo
scratch = os.path.join(OUT, "scratch-apply")
if os.path.exists(scratch):
    shutil.rmtree(scratch, onerror=lambda f, p, e: (os.chmod(p, 0o666), f(p)))
os.makedirs(os.path.join(scratch, *os.path.dirname(REL).split("/")))
shutil.copyfile(LIVE, os.path.join(scratch, *REL.split("/")))
env = dict(os.environ, GIT_CEILING_DIRECTORIES=OUT)
subprocess.run(["git", "init", "-q"], cwd=scratch, check=True, env=env)
subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=scratch, check=True, env=env)
dp = os.path.join(OUT, "c1-verify-fix.diff")
c = subprocess.run(["git", "apply", "--check", "-v", dp], cwd=scratch, capture_output=True, text=True, env=env)
print("apply --check rc", c.returncode, c.stderr.strip())
a = subprocess.run(["git", "apply", "-v", dp], cwd=scratch, capture_output=True, text=True, env=env)
print("apply rc", a.returncode, a.stderr.strip())
got = sha(os.path.join(scratch, *REL.split("/")))
want = sha(os.path.join(OUT, "new", *REL.split("/")))
print("scratch result == new:", got == want)
rv = subprocess.run(["git", "apply", "-R", "--check", dp], cwd=scratch, capture_output=True, text=True, env=env)
print("reverse --check on result rc", rv.returncode)
print("orig ", sha(os.path.join(OUT, "orig", *REL.split("/"))))
print("new  ", want)
print("diff ", sha(dp))
print("live unchanged:", sha(LIVE) == EXPECT_LIVE)
sys.exit(0 if (c.returncode == 0 and a.returncode == 0 and got == want and rv.returncode == 0) else 1)
