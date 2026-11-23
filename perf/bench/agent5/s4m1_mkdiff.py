#!/usr/bin/env python3
"""s4m1_mkdiff.py (Agent 5): stage S4 M1 (S4-DRAFT #11, cvar shared_memory_upload_nontemporal_copy,
default OFF) as a diff against SDK src/graphics/d3d12/shared_memory.cpp after #7 (BB0838CE...).

No git writes. The live SDK file is only read; every git apply runs in a scratch dir outside any
work tree (checked with git rev-parse), the way build/agent12/s4-c1/c1_mkdiff.py does it.
 1. orig = live file (must be B120D07C...); base = orig + #7 (build/agent12/s4-diag/
    upload-hash-log.diff) applied in scratch (must be BB0838CE...).
 2. new = base + the M1 edits below, by exact text replacement (each target must occur once).
 3. m1-nontemporal-copy.diff = git diff --no-index base new, headers rewritten to
    a/src/graphics/d3d12/shared_memory.cpp and b/..., LF (apply with cwd = SDK root).
 4. Chain checks in fresh scratch copies: orig -> #7 -> M1 must give new byte for byte; M1 must
    apply to base; M1 must NOT apply to orig without #7 (it needs #7's context).
Usage: python bench/agent5/s4m1_mkdiff.py [scratch_dir]   (prints the values for HASHES.txt)
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SDK = ROOT / 'DimensionsRecomp' / 'rexglue-sdk'
REL = 'src/graphics/d3d12/shared_memory.cpp'
LIVE = SDK / REL
DIFF7 = ROOT / 'build' / 'agent12' / 's4-diag' / 'upload-hash-log.diff'
STAGE = ROOT / 'build' / 'agent5' / 's4-m1'
DIFF = STAGE / 'm1-nontemporal-copy.diff'
SCRATCH = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                       r'C:\Users\<user>\.gemini\antigravity-cli\brain'
                       r'\dfa71e3d-71bf-461c-b650-c2bad68c09ad\scratch\s4m1')
PRISTINE = 'B120D07C6709D0D2A7836B532ED06B2032A418CBD4A71808CD318C7E6EB6CFBC'
BASE = 'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587'

EDITS = [
    ('includes', r'''#include <rex/math.h>
#include <rex/ui/d3d12/d3d12_util.h>

REXCVAR_DEFINE_BOOL(d3d12_tiled_shared_memory, true, "GPU/D3D12",
''', r'''#include <rex/math.h>
#include <rex/platform.h>
#include <rex/ui/d3d12/d3d12_util.h>

#if REX_ARCH_AMD64
#include <emmintrin.h>
#endif

REXCVAR_DEFINE_BOOL(d3d12_tiled_shared_memory, true, "GPU/D3D12",
'''),
    ('cvar', r'''                    "every uploaded byte on the GPU thread)");

namespace rex::graphics::d3d12 {
''', r'''                    "every uploaded byte on the GPU thread)");

// S4 M1 (default off). When on, UploadRanges copies the guest pages into the
// upload buffer (write-combined memory on discrete GPUs) with SSE2 non-temporal
// stores and an sfence instead of std::memcpy (x86-64 only, std::memcpy
// elsewhere). Same bytes, same order of MakeRangeValid, copy and copy command.
// Off: the original std::memcpy plus one cvar load per UploadRanges call.
REXCVAR_DEFINE_BOOL(shared_memory_upload_nontemporal_copy, false, "GPU/D3D12",
                    "Copy shared memory uploads into the write-combined upload buffer with "
                    "non-temporal (streaming) SSE2 stores and an sfence instead of memcpy");

namespace rex::graphics::d3d12 {
'''),
    ('helper', r'''  log.pages += page_count;
}

}  // namespace
''', r'''  log.pages += page_count;
}

// S4 M1 (shared_memory_upload_nontemporal_copy): std::memcpy replacement for
// copying guest memory into the upload buffer mapping, which is write-combined
// on discrete GPUs and never read back here. UploadRanges passes a page-aligned
// dst and a whole number of pages, so normally only the streaming loop runs;
// the head and tail keep it correct for any alignment and size:
// - head: plain copy up to the first 64-byte boundary of dst, because
//   _mm_stream_si128 needs 16-byte alignment (it faults otherwise), and so no
//   cache line gets both plain and streaming stores;
// - body: whole 64-byte lines, unaligned loads from src, aligned streaming
//   stores to dst (4 x 16 bytes fill one write-combining buffer);
// - tail: plain copy of the last size % 64 bytes.
// Streaming stores (and plain stores to write-combined memory) are weakly
// ordered: the sfence makes them all globally visible before returning, so
// before the copy command is recorded and long before ExecuteCommandLists lets
// the GPU read them.
void CopyToUploadBufferNonTemporal(uint8_t* dst, const uint8_t* src, size_t size) {
#if REX_ARCH_AMD64
  size_t head = (64 - (reinterpret_cast<uintptr_t>(dst) & 63)) & 63;
  if (head > size) {
    head = size;
  }
  if (head) {
    std::memcpy(dst, src, head);
    dst += head;
    src += head;
    size -= head;
  }
  size_t body = size & ~size_t(63);
  for (size_t offset = 0; offset < body; offset += 64) {
    __m128i data0 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset));
    __m128i data1 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 16));
    __m128i data2 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 32));
    __m128i data3 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 48));
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset), data0);
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset + 16), data1);
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset + 32), data2);
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset + 48), data3);
  }
  if (size > body) {
    std::memcpy(dst + body, src + body, size - body);
  }
  _mm_sfence();
#else
  std::memcpy(dst, src, size);
#endif
}

}  // namespace
'''),
    ('flag', r'''  auto& command_list = command_processor_.GetDeferredCommandList();
  for (auto upload_range : upload_page_ranges) {
''', r'''  auto& command_list = command_processor_.GetDeferredCommandList();
  const bool nontemporal_copy = REXCVAR_GET(shared_memory_upload_nontemporal_copy);
  for (auto upload_range : upload_page_ranges) {
'''),
    ('copy', r'''      MakeRangeValid(upload_range_start << page_size_log2(), uint32_t(upload_buffer_size), false);
      std::memcpy(upload_buffer_mapping,
                  memory().TranslatePhysical(upload_range_start << page_size_log2()),
                  upload_buffer_size);
''', r'''      MakeRangeValid(upload_range_start << page_size_log2(), uint32_t(upload_buffer_size), false);
      if (nontemporal_copy) {
        CopyToUploadBufferNonTemporal(
            upload_buffer_mapping,
            memory().TranslatePhysical(upload_range_start << page_size_log2()),
            upload_buffer_size);
      } else {
        std::memcpy(upload_buffer_mapping,
                    memory().TranslatePhysical(upload_range_start << page_size_log2()),
                    upload_buffer_size);
      }
'''),
]


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def fresh(name):
    d = SCRATCH / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    r = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=d,
                       capture_output=True, text=True)
    if r.returncode == 0:
        sys.exit(f'FAIL: scratch dir {d} is inside a git work tree')
    return d


def apply(name, data, diffs, check_only=False):
    d = fresh(name)
    (d / REL).parent.mkdir(parents=True)
    (d / REL).write_bytes(data)
    log = []
    for diff in diffs:
        args = ['git', '-c', 'core.autocrlf=false', 'apply', '--verbose']
        if check_only:
            args.append('--check')
        r = subprocess.run(args + [str(diff)], cwd=d, capture_output=True, text=True)
        log.append((diff.name, r.returncode, ' / '.join((r.stdout + r.stderr).split('\n')).strip(' /')))
        if r.returncode:
            break
    return (d / REL).read_bytes(), log


def main():
    fail = 0
    orig = LIVE.read_bytes()
    print(f'live   {sha(orig)} {len(orig)} B  {LIVE}')
    if sha(orig) != PRISTINE:
        sys.exit('FAIL: the live file is not the pristine B120D07C...')
    base, log = apply('base', orig, [DIFF7])
    for entry in log:
        print('  apply #7: %s exit %d: %s' % entry)
    print(f'base   {sha(base)} {len(base)} B  (live + #7, diff7 {sha(DIFF7.read_bytes())})')
    if sha(base) != BASE:
        sys.exit('FAIL: live + #7 is not BB0838CE...')

    text = base.decode('utf-8')
    if '\r' in text:
        sys.exit('FAIL: base has CR')
    for name, target, replacement in EDITS:
        count = text.count(target)
        if count != 1:
            sys.exit(f'FAIL: edit {name}: target found {count} times')
        text = text.replace(target, replacement)
    new = text.encode('utf-8')

    for sub, data in (('orig', orig), ('base', base), ('new', new)):
        (STAGE / sub).mkdir(parents=True, exist_ok=True)
        (STAGE / sub / 'shared_memory.cpp').write_bytes(data)
    print(f'new    {sha(new)} {len(new)} B  (base + M1, {len(EDITS)} edits)')

    d = fresh('diff')
    for sub, data in (('base', base), ('new', new)):
        (d / sub).mkdir()
        (d / sub / 'shared_memory.cpp').write_bytes(data)
    r = subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', '--no-color',
                        '--no-ext-diff', '-U3', '--', 'base/shared_memory.cpp',
                        'new/shared_memory.cpp'], cwd=d, capture_output=True)
    if r.returncode != 1:
        sys.exit(f'FAIL: git diff --no-index exit {r.returncode}: {r.stderr!r}')
    out = []
    for line in r.stdout.decode('utf-8').split('\n'):
        if line.startswith('warning:'):
            continue
        if line.startswith('diff --git '):
            line = f'diff --git a/{REL} b/{REL}'
        elif line.startswith('--- a/'):
            line = f'--- a/{REL}'
        elif line.startswith('+++ b/'):
            line = f'+++ b/{REL}'
        out.append(line)
    patch = '\n'.join(out).encode('utf-8')
    DIFF.write_bytes(patch)
    body = [l for l in out if not l.startswith(('diff --git', 'index ', '--- a/', '+++ b/'))]
    hunks = sum(1 for l in body if l.startswith('@@ '))
    plus = sum(1 for l in body if l.startswith('+'))
    minus = sum(1 for l in body if l.startswith('-'))
    print(f'diff   {sha(patch)} {len(patch)} B  {hunks} hunks +{plus} -{minus}  {DIFF}')

    chain, log = apply('chain', orig, [DIFF7, DIFF])
    for entry in log:
        print('  chain live -> #7 -> M1: %s exit %d: %s' % entry)
    ok = all(e[1] == 0 for e in log) and len(log) == 2 and chain == new
    print(f'  chain result {sha(chain)} {"== new" if chain == new else "!= new"}: {"OK" if ok else "FAIL"}')
    fail += not ok
    _, log = apply('check-base', base, [DIFF], check_only=True)
    ok = log[0][1] == 0
    print('  M1 --check on base: exit %d: %s' % (log[0][1], log[0][2]), 'OK' if ok else 'FAIL')
    fail += not ok
    _, log = apply('check-orig', orig, [DIFF], check_only=True)
    ok = log[0][1] != 0
    print('  M1 --check on live without #7 (must fail): exit %d: %s' % (log[0][1], log[0][2]),
          'OK' if ok else 'FAIL')
    fail += not ok
    print('RESULT:', 'FAIL' if fail else 'PASS')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
