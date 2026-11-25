"""Make s33-popin-nohunk5.patch from the rated s33-popin.patch (M6, session 3, S3T-6).

- Drops hunk #5 (CanEndSubmissionImmediately; Agent 10 S1): patch L82-93, from the
  `@@ -4368,7 +4388,10 @@` line up to, not including, the pipeline_cache.cpp `diff --git` line.
- Adds Agent 10's N1 threading rule (3 comment lines) to hunk #1's AwaitPipelineCreation()
  comment and fixes the two pipeline_cache.h hunk headers (+64,15 -> +64,18; +438,8 -> +441,8).
- Every other byte is copied. Refuses any input but the rated patch (sha256 0D23024484CCDEE1...).
Usage: python -B make_nohunk5.py   (writes s33-popin-nohunk5.patch next to this file)
"""
import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "s33-popin.patch"
DST = HERE / "s33-popin-nohunk5.patch"
RATED = "0D23024484CCDEE1"

N1 = [
    b"  // Call it only from the thread that drives pipeline creation: the GPU thread,\n",
    b"  // or the thread acting for it while the command processor is paused. Never\n",
    b"  // from two threads at once: the completion event has one waiter.\n",
]


def die(msg):
    print("make_nohunk5: " + msg)
    sys.exit(1)


data = SRC.read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
if not sha.startswith(RATED):
    die("input is not the rated patch: sha256 %s" % sha)
if b"\r" in data:
    die("input has CR bytes")
lines = data.splitlines(keepends=True)
if len(lines) != 220:
    die("expected 220 lines, got %d" % len(lines))

# 1-based checks of the anchors.
def at(n):
    return lines[n - 1]

checks = [
    (4, b"@@ -64,7 +64,15 @@ class PipelineCache {\n"),
    (11, b"+  // unless IsCreationNoWait().\n"),
    (12, b"+  void AwaitPipelineCreation();\n"),
    (20, b"@@ -430,6 +438,8 @@ class PipelineCache {\n"),
    (82, b"@@ -4368,7 +4388,10 @@ bool D3D12CommandProcessor::EndSubmission(bool is_swap) {\n"),
    (93, b" void D3D12CommandProcessor::MaybeSplitSubmission() {\n"),
    (94, b"diff --git a/src/graphics/d3d12/pipeline_cache.cpp b/src/graphics/d3d12/pipeline_cache.cpp\n"),
]
for n, want in checks:
    if at(n) != want:
        die("anchor mismatch at L%d: %r" % (n, at(n)))

out = []
for i, line in enumerate(lines, start=1):
    if 82 <= i <= 93:
        continue  # hunk #5
    if i == 4:
        line = b"@@ -64,7 +64,18 @@ class PipelineCache {\n"
    elif i == 20:
        line = b"@@ -430,6 +441,8 @@ class PipelineCache {\n"
    out.append(line)
    if i == 11:
        out.extend(b"+" + l for l in N1)

for l in out:
    if l.startswith(b"+") and not l.startswith(b"+++") and len(l.rstrip(b"\n")) > 101:
        # added source lines: 1 diff marker + at most 100 columns
        die("line over 100 columns: %r" % l)

res = b"".join(out)
DST.write_bytes(res)
print("wrote %s: %d bytes, %d lines, sha256 %s" % (
    DST.name, len(res), res.count(b"\n"), hashlib.sha256(res).hexdigest().upper()))
print("input sha256 %s (unchanged)" % hashlib.sha256(SRC.read_bytes()).hexdigest().upper())
