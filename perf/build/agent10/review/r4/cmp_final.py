import difflib
import hashlib
import sys

R = r"<workspace>"
final = open(R + r"\bench\agent9\review\final-2316.patch", "rb").read()
norm = final.replace(b"\r\n", b"\n")
mine = (open(R + r"\build\agent10\review\agent9-chk3.patch", "rb").read()
        + open(R + r"\build\agent10\review\agent9-chk3-tests.patch", "rb").read())
print("final_len", len(final), "crlf", final.count(b"\r\n"), "norm_len", len(norm),
      "mine_len", len(mine), "equal", norm == mine)
print("norm_sha", hashlib.sha256(norm).hexdigest()[:16].upper(),
      "mine_sha", hashlib.sha256(mine).hexdigest()[:16].upper())
print("new_file", norm.count(b"new file mode"), "devnull", norm.count(b"/dev/null"))
if norm != mine:
    x = [l.decode("latin-1") for l in norm.split(b"\n")]
    y = [l.decode("latin-1") for l in mine.split(b"\n")]
    d = list(difflib.unified_diff(y, x, "mine", "final", lineterm="", n=0))
    print("difflines", len(d))
    print("\n".join(d[:80]))
sys.exit(0)
