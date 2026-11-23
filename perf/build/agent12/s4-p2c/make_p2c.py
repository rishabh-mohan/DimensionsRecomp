#!/usr/bin/env python3
# make_p2c.py (Agent 12, run-2 task #13): stage S4 P2's memexport full-buffer counter (one TU).
#   python build\agent12\s4-p2c\make_p2c.py
# Reads the live SDK src/graphics/d3d12/command_processor.cpp, which must be the expected base.
# Writes orig/ (a byte copy), new/ (the edit) and memexport-full-buffer-counter.diff (paths from
# the SDK root). Then it checks that:
#   - every anchor matches exactly once;
#   - the files are LF only;
#   - added lines have no trailing whitespace and are at most 100 columns;
#   - git apply --check passes on the live SDK (read-only);
#   - a scratch apply in %TEMP% reproduces new/ byte for byte;
#   - a joint apply --check with the three staged S4a diffs (#7 diag, #8 P2, #5 fix (i)) passes,
#     and none of them touches this file.
# Writes HASHES.txt. Writes nothing outside build/agent12/s4-p2c, apart from a %TEMP% scratch
# dir that it deletes.
import difflib
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SDK = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
REL = 'src/graphics/d3d12/command_processor.cpp'
LIVE = os.path.join(SDK, *REL.split('/'))
NAME = 'command_processor.cpp'
DIFF = 'memexport-full-buffer-counter.diff'
BASE_SHA = '3AB3AA5360D4E9875DCA8550346EE368EC9188BDC454C2EB93D9BB915BD1AD97'
S4A_STAGES = ['s4-diag', 's4-p2', 's4-fixi']  # #7, #8, #5: their HASHES.txt "diff" lines

EDITS = [
    # 1. The counter: file scope, in the anonymous namespace, just before ReportSlowFrame.
    ("PixelShaderFrameStats& FrameStats() {\n"
     "  static PixelShaderFrameStats stats;\n"
     "  return stats;\n"
     "}\n"
     "\n"
     "// Called on every swap from the command thread",
     "PixelShaderFrameStats& FrameStats() {\n"
     "  static PixelShaderFrameStats stats;\n"
     "  return stats;\n"
     "}\n"
     "\n"
     "// Memexporting draws with no known destination range: IssueDraw then marks all\n"
     "// of shared memory as written by the GPU. Counted (relaxed) on the command\n"
     "// thread; ReportSlowFrame takes the count each frame and prints it.\n"
     "std::atomic<uint64_t> memexport_full_buffer_draws{0};\n"
     "\n"
     "// Called on every swap from the command thread"),
    # 2. Take and reset it with the frame_stats counters, before the early return, so nothing is
    #    lost on frames that aren't logged; keep a running total.
    ("            c.extra.exchange(0, std::memory_order_relaxed)};\n"
     "  }\n"
     "  const bool first = last_swap == clock::time_point{};\n",
     "            c.extra.exchange(0, std::memory_order_relaxed)};\n"
     "  }\n"
     "  static uint64_t full_buffer_total = 0;\n"
     "  const uint64_t full_buffer = memexport_full_buffer_draws.exchange(0, std::memory_order_relaxed);\n"
     "  full_buffer_total += full_buffer;\n"
     "  const bool first = last_swap == clock::time_point{};\n"),
    # 3. A field at the very end of the slow-frame line (parsers match its start, not its end).
    ("      \"memexport syncs {} ({} KB), on demand {} ({} KB)\",\n",
     "      \"memexport syncs {} ({} KB), on demand {} ({} KB) | \"\n"
     "      \"memexport full-buffer {}x (total {})\",\n"),
    ("      s[kMemexportOnDemand].extra / 1024);\n}\n",
     "      s[kMemexportOnDemand].extra / 1024, full_buffer, full_buffer_total);\n}\n"),
    # 4. Count the fallback (the only full-buffer RangeWrittenByGpu call in the D3D12 backend).
    ("      shared_memory_->RangeWrittenByGpu(0, SharedMemory::kBufferSize);\n"
     "    }\n",
     "      shared_memory_->RangeWrittenByGpu(0, SharedMemory::kBufferSize);\n"
     "      memexport_full_buffer_draws.fetch_add(1, std::memory_order_relaxed);\n"
     "    }\n"),
]

problems = []


def check(ok, msg):
    print(('ok    ' if ok else 'FAIL  ') + msg)
    if not ok:
        problems.append(msg)
    return ok


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def wr(p, b):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b)


def git(args, cwd=None, env=None):
    r = subprocess.run(['git'] + args, cwd=cwd, env=env, capture_output=True)
    return r.returncode, (r.stdout + r.stderr).decode('utf-8', 'replace').strip()


def touched(diff_text):
    return sorted(set(re.findall(r'^\+\+\+ b/(\S+)', diff_text, re.M)))


stamp = time.strftime('%Y-%m-%d %H:%M:%S')
print(f'# make_p2c {stamp}')
live = rd(LIVE)
if not check(sha(live) == BASE_SHA, f'live {REL} sha {sha(live)[:16]}... is the base {BASE_SHA[:16]}...'):
    sys.exit(1)
check(b'\r' not in live, 'live file is LF only')
old_text = live.decode('utf-8')
text = old_text
for old, new in EDITS:
    n = text.count(old)
    check(n == 1, f'anchor found exactly once (found {n}): {old.splitlines()[0].strip()[:70]!r}')
    text = text.replace(old, new, 1)
newb = text.encode('utf-8')
check(b'\r' not in newb, 'new file is LF only')

added, removed = [], []
for line in difflib.unified_diff(old_text.split('\n'), text.split('\n'), lineterm='', n=0):
    if line.startswith('+') and not line.startswith('+++'):
        added.append(line[1:])
    elif line.startswith('-') and not line.startswith('---'):
        removed.append(line[1:])
long_or_ws = [l for l in added if len(l) > 100 or l != l.rstrip() or '\t' in l]
check(not long_or_ws, f'{len(added)} added lines: none over 100 columns, no trailing space, no tab'
      f' (longest {max(len(l) for l in added)})')
for l in long_or_ws:
    print(f'      bad added line ({len(l)}): {l!r}')

wr(os.path.join(HERE, 'orig', NAME), live)
wr(os.path.join(HERE, 'new', NAME), newb)
code, out = git(['-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', 'diff', '--no-index',
                 '--no-color', '--no-ext-diff', '-U3', 'orig/' + NAME, 'new/' + NAME], cwd=HERE)
check(code == 1, f'git diff --no-index found the change (exit {code})')
diff_text = out.replace('\r\n', '\n')
diff_text = diff_text.replace('a/orig/' + NAME, 'a/' + REL).replace('b/new/' + NAME, 'b/' + REL)
if not diff_text.endswith('\n'):
    diff_text += '\n'
diff_b = diff_text.encode('utf-8')
diff_path = os.path.join(HERE, DIFF)
wr(diff_path, diff_b)
hunks = len(re.findall(r'^@@ ', diff_text, re.M))
plus = len([l for l in diff_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
minus = len([l for l in diff_text.split('\n') if l.startswith('-') and not l.startswith('---')])
check(touched(diff_text) == [REL], f'the diff touches only {REL}')
print(diff_text)

code, out = git(['-C', SDK, 'apply', '--check', diff_path])
check(code == 0, f'git apply --check on the live SDK{": " + out if out else ""}')

tmp = tempfile.mkdtemp(prefix='a12-p2c-')
try:
    dst = os.path.join(tmp, *REL.split('/'))
    wr(dst, live)
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(tmp))
    code, out = git(['-c', 'core.autocrlf=false', 'apply', diff_path], cwd=tmp, env=env)
    check(code == 0 and rd(dst) == newb,
          f'scratch apply (outside any repo) reproduces new/ byte for byte{": " + out if out else ""}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

s4a = []
for st in S4A_STAGES:
    hp = os.path.join(ROOT, 'build', 'agent12', st, 'HASHES.txt')
    m = re.search(r'^diff\s+([0-9A-F]{64})\s+(\S+\.diff)', rd(hp).decode('utf-8', 'replace'), re.M)
    if not check(m is not None, f'{st}/HASHES.txt has a diff line'):
        continue
    p = os.path.join(ROOT, 'build', 'agent12', st, m.group(2))
    b = rd(p)
    check(sha(b) == m.group(1), f'{st}/{m.group(2)} sha {sha(b)[:16]}... = its HASHES.txt')
    files = touched(b.decode('utf-8', 'replace'))
    check(REL not in files, f'{st}/{m.group(2)} touches {", ".join(files)} (not {NAME})')
    s4a.append(p)
if len(s4a) == 3:
    code, out = git(['-C', SDK, 'apply', '--check'] + s4a + [diff_path])
    check(code == 0, 'joint git apply --check of #7 + #8 + #5 + the counter on the live SDK'
          f'{": " + out if out else ""}')

hashes = [
    f'# s4-p2c HASHES (Agent 12, run-2 task #13, {stamp}): S4 P2 memexport full-buffer counter, one TU',
    f'pristine {sha(live)}  orig/{NAME} = live DimensionsRecomp/rexglue-sdk/{REL} '
    f'({len(live)} B, {old_text.count(chr(10))} lines, LF, git clean, last commit 17e3675; SDK HEAD c5fe668)',
    f'staged   {sha(newb)}  new/{NAME} ({len(newb)} B, {text.count(chr(10))} lines, LF)',
    f'diff     {sha(diff_b)}  {DIFF} ({len(diff_b)} B, {hunks} hunks, +{plus}/-{minus}; paths from the SDK '
    f'root; git apply --check passes on the live SDK)',
    f'live     {sha(rd(LIVE))}  live {REL} when this file was written (= pristine)',
    f'script   {sha(rd(os.path.abspath(__file__)))}  make_p2c.py',
]
wr(os.path.join(HERE, 'HASHES.txt'), ('\n'.join(hashes) + '\n').encode('ascii'))
print('\n'.join(hashes))
print('RESULT: ' + (f'FAIL ({len(problems)})' if problems else 'PASS'))
sys.exit(1 if problems else 0)
