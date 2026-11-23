#!/usr/bin/env python3
# make_c1v3.py (Agent 12, run-2 task #13 follow-up): C1 v3 = C1 v2 + the init latch Agent 10 asked for before
# default-ON or any landing beyond tests (b2r row 35, §34), plus §34's nit 2. Staged on scratch only.
# C1 v2 (build/agent12/s4-c1v2, rated SAFE in row 35) is only read and stays byte-identical; S4b tests use v2.
# v3 differs from v2 only in SDK src/system/xmemory.cpp:
#   L0  the cvar comment says both cvars are latched at init;
#   L1  two file-static constinit latches, physical_protect_hold_global_lock_latched and
#       physical_protect_keep_watch_latched (default false), at the top of namespace rex::memory;
#   L2  Memory::Initialize reads both cvars once, stores them in the latches (before any heap exists) and
#       prints v2's state line from the same values;
#   L3  PhysicalHeap::Protect's two runtime reads (fix (i)'s hold, C1's keep-watch gate) read the latches,
#       so a later set (the dev console can still set kInitOnly cvars: FinalizeInit has no caller) changes
#       nothing in this process;
#   N2  NoteKeepWatchBlocked loads the flag before its exchange (§34 nit 2: on native the exchange ran on
#       every protect).
# The kInitOnly lifecycles (v2's V1/V6) and V4's "blocked" semantics stay as they are.
# Steps:
#   1. C1 v2's copies and diffs match its HASHES.txt, and the live bases are the expected ones;
#   2. the v3 edits on v2's new xmemory.cpp: each anchor exactly once, LF, added lines <= 100 columns, no
#      trailing space; afterwards every REXCVAR_GET of the two cvars is inside Memory::Initialize, and no
#      other staged file reads them;
#   3. writes v2/sdk/src/system/xmemory.cpp (byte copy of v2's), orig/sdk/... (byte copies of v2's C1 bases =
#      the S4a outputs), new/sdk/... (v2's 4 other files, unchanged, plus v3's xmemory.cpp);
#   4. diffs: v2-to-v3.diff (interdiff for Agent 10), keep-watch-v3.diff (S4a output -> C1 v3, 5 SDK files;
#      would replace keep-watch-v2.diff), chain-live-to-c1v3.diff (reference: live -> #7+#8+#5+C1 v3);
#      v1's keep-watch-rexlego.diff is reused unchanged;
#   5. git apply --check (read-only) on the live SDK and the live game repo; on scratch, outside any work
#      tree: v2-to-v3 on v2's copy, and the 4-step chain #7 -> #8 -> #5 -> keep-watch-v3 on copies of the
#      live files, each result compared with the staged copy;
#   6. writes HASHES.txt. No live file is written, no git write.
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
V1 = os.path.join(ROOT, 'build', 'agent12', 's4-c1')
V2 = os.path.join(ROOT, 'build', 'agent12', 's4-c1v2')
SDK = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
GAME = os.path.join(ROOT, 'DimensionsRecomp')
SCRATCH = r'C:\Users\<user>\.gemini\antigravity-cli\brain\174e1574-a481-4854-9e25-c86c7eb78df3\scratch'
TEST = os.path.join(SCRATCH, 'applytest-c1v3')

D_DIAG = os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'upload-hash-log.diff')
D_P2 = os.path.join(ROOT, 'build', 'agent12', 's4-p2', 'single-hold-rearm.diff')
D_FIXI = os.path.join(ROOT, 'build', 'agent12', 's4-fixi', 'protect-hold-g.diff')
D_GAME = os.path.join(V1, 'keep-watch-rexlego.diff')
D_V3 = os.path.join(HERE, 'keep-watch-v3.diff')
D_INTER = os.path.join(HERE, 'v2-to-v3.diff')
D_COMB = os.path.join(HERE, 'chain-live-to-c1v3.diff')

XM = 'src/system/xmemory.cpp'
D3D12 = 'src/graphics/d3d12/shared_memory.cpp'
SDK_C1 = [
    'include/rex/graphics/shared_memory.h',
    'include/rex/system/xmemory.h',
    'src/graphics/primitive_processor.cpp',
    'src/graphics/shared_memory.cpp',
    XM,
]
GAME_REL = 'rexlego/src/gpu_native/memory_watch.cpp'
LIVE_WANT = {
    D3D12: 'B120D07C6709D0D2',
    'src/graphics/shared_memory.cpp': '15C89EDB4B197C17487A9D45208D5CE624DE98ABE416F86942C5D14ED43EB282',
    XM: '6E8FA1BA80EF9271D4433DD1BB2CAD0403360E222B22CED78AA4C7951D811DB4',
    'include/rex/system/xmemory.h': '80100865A654AF04',
    'include/rex/graphics/shared_memory.h': '4D861738A94B556B',
    'src/graphics/primitive_processor.cpp': 'E07F690223B564AE',
}
GAME_WANT = '19AE1606C6DB727369A5F119EF3371A8D307F4B42088D5C064F0D2DF8D62D47A'
V2_XM_WANT = 'DC23757AC206FCC51F03B89C0A77F8EFCDB372B138C5D72600C230C295EC8CFD'
V2_DIFFS = ['v1-to-v2.diff', 'keep-watch-v2.diff', 'chain-live-to-c1v2.diff']
STAGED_WANT = {'diag': 'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587',
               'p2': '0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4',
               'fixi': '141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A'}

# ----------------------------------------------------------------------------- the v3 edits
EDITS = [
    ('L0 cvar comment',
     '''// PhysicalHeap::ProtectKeepWatch. Both cvars are init-only (C1 v2), so the settings
// overlay can't turn C1 on mid-run over page state from before fix (i) was on.
''',
     '''// PhysicalHeap::ProtectKeepWatch. Both cvars are init-only (C1 v2), so the settings
// overlay can't turn C1 on mid-run over page state from before fix (i) was on, and
// Memory::Initialize latches both (C1 v3), so no later set reaches the protect path.
'''),
    ('L1 latch storage',
     '''    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace rex::memory {
''',
     '''    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace rex::memory {

// S4 C1 v3: the two cvars above, latched once by Memory::Initialize before any heap
// exists. PhysicalHeap::Protect reads only these copies, so a set after that (the
// dev console still can, as nothing calls FinalizeInit) changes nothing in this
// process. Constant-initialized to off.
static constinit std::atomic<bool> physical_protect_hold_global_lock_latched{false};
static constinit std::atomic<bool> physical_protect_keep_watch_latched{false};
'''),
    ('L2 latch at init',
     '''  // S4 C1 v2: whether physical_protect_keep_watch can engage (set both cvars at
  // launch). Prints nothing while it is off.
  if (REXCVAR_GET(physical_protect_keep_watch)) {
    if (IsPhysicalProtectKeepWatchBlocked()) {
      REXSYS_INFO("C1 keep-watch: on, but blocked for this process (native renderer)");
    } else if (!REXCVAR_GET(physical_protect_hold_global_lock)) {
''',
     '''  // S4 C1 v3: latch fix (i)'s and C1's cvars here, once, before any heap exists;
  // PhysicalHeap::Protect reads only the latched copies.
  const bool hold_on = REXCVAR_GET(physical_protect_hold_global_lock);
  const bool keep_on = REXCVAR_GET(physical_protect_keep_watch);
  physical_protect_hold_global_lock_latched.store(hold_on, std::memory_order_relaxed);
  physical_protect_keep_watch_latched.store(keep_on, std::memory_order_relaxed);
  // S4 C1 v2: whether physical_protect_keep_watch can engage (set both cvars at
  // launch). Prints nothing while it is off.
  if (keep_on) {
    if (IsPhysicalProtectKeepWatchBlocked()) {
      REXSYS_INFO("C1 keep-watch: on, but blocked for this process (native renderer)");
    } else if (!hold_on) {
'''),
    ('N2 load before the exchange',
     '''  if (!physical_protect_keep_watch_block_logged.exchange(true, std::memory_order_relaxed)) {
''',
     '''  // C1 v3: load first, so after the first line a native protect only reads the flag.
  if (!physical_protect_keep_watch_block_logged.load(std::memory_order_relaxed) &&
      !physical_protect_keep_watch_block_logged.exchange(true, std::memory_order_relaxed)) {
'''),
    ('L3a fix (i) hold reads its latch',
     '''  if ((protect & memory::kMemoryProtectWrite) && REXCVAR_GET(physical_protect_hold_global_lock)) {
''',
     '''  if ((protect & memory::kMemoryProtectWrite) &&
      physical_protect_hold_global_lock_latched.load(std::memory_order_relaxed)) {
'''),
    ('L3b C1 gate reads its latch',
     '''  if (hold_global_lock.owns_lock() && !old_protect && REXCVAR_GET(physical_protect_keep_watch) &&
''',
     '''  if (hold_global_lock.owns_lock() && !old_protect &&
      physical_protect_keep_watch_latched.load(std::memory_order_relaxed) &&
'''),
]

out = []
bad = 0


def say(s):
    print(s)
    out.append(s)


def fail(s):
    global bad
    bad += 1
    say('FAIL ' + s)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest().upper()


def sha(p):
    return sha_bytes(open(p, 'rb').read())


def run(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True)
    return r.returncode, (r.stdout + r.stderr).decode('utf-8', 'replace')


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)


def mkdiff(orig, new, rel, cwd=HERE):
    code, text = run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', '--no-color',
                      '--no-ext-diff', '-U3', '--', orig, new], cwd)
    if code != 1:
        sys.exit('FAIL git diff %s: exit %d\n%s' % (rel, code, text))
    o = orig.replace('\\', '/').lstrip('/')
    n = new.replace('\\', '/').lstrip('/')
    res = []
    for l in text.replace('\r\n', '\n').split('\n'):
        if l.startswith('diff --git ') or l.startswith('--- ') or l.startswith('+++ '):
            l = l.replace('a/' + o, 'a/' + rel).replace('b/' + n, 'b/' + rel)
            if ('a/' + rel not in l) and ('b/' + rel not in l):
                sys.exit('FAIL header rewrite for %s: %s' % (rel, l))
        if l.startswith('warning:'):
            continue
        res.append(l)
    while res and res[-1] == '':
        res.pop()
    return '\n'.join(res) + '\n'


def stats(d):
    ls = d.split('\n')
    return (len(ls) - 1, sum(1 for l in ls if l.startswith('@@')),
            sum(1 for l in ls if l.startswith('+') and not l.startswith('+++')),
            sum(1 for l in ls if l.startswith('-') and not l.startswith('---')))


def main():
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    say('S4 C1 v3 (C1 v2 + the init latch for both cvars + the load-first blocked flag; Agent 12, run-2 '
        'task #13 follow-up). Staged %s on scratch. Not applied, not built. C1 v1 and v2 unchanged.' % stamp)
    code, head = run(['git', '--no-optional-locks', 'rev-parse', '--short', 'HEAD'], SDK)
    code2, ghead = run(['git', '--no-optional-locks', 'rev-parse', '--short', 'HEAD'], GAME)
    say('SDK: DimensionsRecomp/rexglue-sdk HEAD %s; game: DimensionsRecomp HEAD %s.'
        % (head.strip(), ghead.strip()))

    # 1. C1 v2 and the live bases
    v2h = {}
    for l in open(os.path.join(V2, 'HASHES.txt'), encoding='utf-8'):
        m = re.match(r'^(v1|orig|new|diff)\s+([0-9A-F]{64})\s+(?:game )?(\S+?),?\s', l)
        if m:
            v2h[m.group(1) + '|' + m.group(3)] = m.group(2)
    if v2h.get('new|' + XM) != V2_XM_WANT:
        fail('v2 HASHES.txt new|%s is %s, want %s' % (XM, v2h.get('new|' + XM, '?')[:16], V2_XM_WANT[:16]))
    for rel in SDK_C1:
        for side in ('orig', 'new'):
            h = sha(os.path.join(V2, side, 'sdk', rel))
            if h != v2h.get(side + '|' + rel):
                fail('v2 %s/sdk/%s is %s, v2 HASHES.txt says %s' % (side, rel, h[:16],
                                                                  v2h.get(side + '|' + rel, '?')[:16]))
    h = sha(os.path.join(V2, 'v1', 'sdk', XM))
    if h != v2h.get('v1|' + XM):
        fail('v2 v1/sdk/%s is %s' % (XM, h[:16]))
    for name in V2_DIFFS:
        h = sha(os.path.join(V2, name))
        if h != v2h.get('diff|' + name):
            fail('v2 %s is %s, v2 HASHES.txt says %s' % (name, h[:16], v2h.get('diff|' + name, '?')[:16]))
    h = sha(D_GAME)
    if h != v2h.get('diff|keep-watch-rexlego.diff'):
        fail('v1 keep-watch-rexlego.diff is %s' % h[:16])
    say('v2        build/agent12/s4-c1v2: 11 v1/orig/new copies and 3 diffs (+ v1\'s rexlego diff) = its '
        'HASHES.txt: %s' % ('yes' if not bad else 'NO'))
    for rel, want in LIVE_WANT.items():
        h = sha(os.path.join(SDK, rel))
        say('live      %s  %s%s' % (h, rel, '' if h.startswith(want) else '  MISMATCH want ' + want[:16]))
        if not h.startswith(want):
            fail('live base %s' % rel)
    gh = sha(os.path.join(GAME, GAME_REL))
    say('live      %s  game %s (CRLF work tree)%s' % (gh, GAME_REL, '' if gh == GAME_WANT else '  MISMATCH'))
    if gh != GAME_WANT:
        fail('live base %s' % GAME_REL)
    if bad:
        say('RESULT FAIL (%d)' % bad)
        sys.exit(1)

    # 2. the v3 edits
    v2_xm = open(os.path.join(V2, 'new', 'sdk', XM), 'rb').read()
    text = v2_xm.decode('utf-8')
    if '\r' in text:
        sys.exit('FAIL v2 xmemory.cpp has CR')
    added = []
    for name, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            fail('%s: anchor found %d times' % (name, n))
            continue
        text = text.replace(old, new)
        old_lines = old.split('\n')
        added.extend(l for l in new.split('\n') if l not in old_lines)
        say('edit      %s: anchor once, +%d line(s)' % (name, len(new.split('\n')) - len(old_lines)))
    long_lines = [l for l in added if len(l) > 100 or l != l.rstrip() or '\t' in l]
    for l in long_lines:
        fail('added line (%d cols, trailing space or tab): %r' % (len(l), l))
    say('edit      %d added/changed lines checked: none over 100 columns, no trailing space, no tab; '
        'longest %d' % (len(added), max(len(l) for l in added)))
    # every cvar read is now at init; the runtime paths read the latches
    i0 = text.index('bool Memory::Initialize() {')
    i1 = text.index('\n}\n', i0)
    reads = [m.start() for m in re.finditer(r'REXCVAR_GET\(physical_protect_(hold_global_lock|keep_watch)\)',
                                            text)]
    inside = all(i0 < p < i1 for p in reads)
    say('check     REXCVAR_GET of the two cvars: %d, all inside Memory::Initialize: %s; latch loads %d, '
        'stores %d' % (len(reads), inside, text.count('_latched.load(std::memory_order_relaxed)'),
                       text.count('_latched.store(')))
    if len(reads) != 2 or not inside or text.count('_latched.load(std::memory_order_relaxed)') != 2 \
            or text.count('_latched.store(') != 2:
        fail('latch read sites')
    # a read or declaration: REXCVAR_*(name...) or cvars::name. \b keeps out physical_protect_keep_watch_verify
    # (shared_memory.cpp's own kRequiresRestart cvar); the other plain-name hits are comments.
    use = re.compile(r'(REXCVAR_\w+\(\s*|cvars::)physical_protect_(hold_global_lock|keep_watch)\b')
    others = [os.path.join(V2, 'new', 'sdk', rel) for rel in SDK_C1 if rel != XM]
    others.append(os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'new', 'shared_memory.cpp'))
    hits = sum(len(use.findall(open(p, encoding='utf-8', errors='replace').read())) for p in others)
    say('check     the other 5 staged files read or declare neither cvar (REXCVAR_*(name) or cvars::name): '
        '%s (%d hits)' % (hits == 0, hits))
    if hits:
        fail('another staged file reads a latched cvar')
    v3_xm = text.encode('utf-8')

    # 3. the stage tree
    for d in ('v2', 'orig', 'new'):
        p = os.path.join(HERE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    copy(os.path.join(V2, 'new', 'sdk', XM), os.path.join(HERE, 'v2', 'sdk', XM))
    for rel in SDK_C1:
        copy(os.path.join(V2, 'orig', 'sdk', rel), os.path.join(HERE, 'orig', 'sdk', rel))
        if rel != XM:
            copy(os.path.join(V2, 'new', 'sdk', rel), os.path.join(HERE, 'new', 'sdk', rel))
    os.makedirs(os.path.dirname(os.path.join(HERE, 'new', 'sdk', XM)), exist_ok=True)
    open(os.path.join(HERE, 'new', 'sdk', XM), 'wb').write(v3_xm)
    say('v2        %s  %s (C1 v2 new, the interdiff base, %d B)' % (sha_bytes(v2_xm), XM, len(v2_xm)))
    for rel in SDK_C1:
        say('orig      %s  %s (C1 base = S4a output)' % (sha(os.path.join(HERE, 'orig', 'sdk', rel)), rel))
        p = os.path.join(HERE, 'new', 'sdk', rel)
        say('new       %s  %s (%d B%s)' % (sha(p), rel, os.path.getsize(p),
                                           ', C1 v3' if rel == XM else ', = v1 and v2'))

    # 4. diffs
    inter = mkdiff('v2/sdk/' + XM, 'new/sdk/' + XM, XM)
    open(D_INTER, 'wb').write(inter.encode('utf-8'))
    v3diff = ''.join(mkdiff('orig/sdk/' + rel, 'new/sdk/' + rel, rel) for rel in SDK_C1)
    open(D_V3, 'wb').write(v3diff.encode('utf-8'))
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    finals = {D3D12: os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'new', 'shared_memory.cpp')}
    finals.update({rel: os.path.join(HERE, 'new', 'sdk', rel) for rel in SDK_C1})
    for rel in finals:
        copy(os.path.join(SDK, rel), os.path.join(TEST, 'base', rel))
        copy(finals[rel], os.path.join(TEST, 'final', rel))
    comb = ''.join(mkdiff('base/' + rel, 'final/' + rel, rel, TEST) for rel in sorted(finals))
    open(D_COMB, 'wb').write(comb.encode('utf-8'))
    for name, d in (('v2-to-v3.diff', inter), ('keep-watch-v3.diff', v3diff),
                    ('chain-live-to-c1v3.diff', comb)):
        n, hunks, plus, minus = stats(d)
        say('diff      %s  %s, %d lines, %d hunks, +%d/-%d, LF' % (sha_bytes(d.encode('utf-8')), name, n,
                                                                 hunks, plus, minus))
    say('diff      %s  keep-watch-rexlego.diff (v1, reused unchanged)' % sha(D_GAME))
    for p in (D_DIAG, D_P2, D_FIXI):
        say('chain     %s  %s' % (sha(p), os.path.relpath(p, ROOT).replace('\\', '/')))

    # 5. checks
    for name, d in (('diag', D_DIAG), ('P2', D_P2), ('fix (i)', D_FIXI), ('chain-live-to-c1v3', D_COMB)):
        code, t = run(['git', '--no-optional-locks', 'apply', '--check', d], SDK)
        say('git apply --check (live SDK, %s): exit %d' % (name, code))
        if code:
            say('    | ' + t.strip().replace('\n', '\n    | '))
            fail('apply --check %s' % name)
    code, t = run(['git', '--no-optional-locks', 'apply', '--check', D_GAME], GAME)
    say('git apply --check (live game repo, keep-watch-rexlego.diff): exit %d' % code)
    if code:
        fail('game apply --check')
    it = os.path.join(TEST, 'inter')
    copy(os.path.join(HERE, 'v2', 'sdk', XM), os.path.join(it, XM))
    code, t = run(['git', 'rev-parse', '--is-inside-work-tree'], it)
    if code == 0:
        sys.exit('FAIL scratch dir is inside a work tree: ' + t)
    code, t = run(['git', '-c', 'core.autocrlf=false', 'apply', '--verbose', D_INTER], it)
    ok = code == 0 and sha(os.path.join(it, XM)) == sha_bytes(v3_xm)
    say('scratch   v2 xmemory.cpp + v2-to-v3.diff: exit %d; = C1 v3 new: %s' % (code, ok))
    if not ok:
        fail('interdiff scratch apply')
    sdk_t = os.path.join(TEST, 'sdk')
    for rel in LIVE_WANT:
        copy(os.path.join(SDK, rel), os.path.join(sdk_t, rel))
    staged = {
        'diag': {D3D12: finals[D3D12]},
        'p2': {'src/graphics/shared_memory.cpp': os.path.join(ROOT, 'build', 'agent12', 's4-p2', 'new',
                                                              'shared_memory.cpp')},
        'fixi': {XM: os.path.join(ROOT, 'build', 'agent12', 's4-fixi', 'new', 'xmemory.cpp')},
        'c1v3': {rel: os.path.join(HERE, 'new', 'sdk', rel) for rel in SDK_C1},
    }
    say('4-step chain on scratch copies of the live files (git -c core.autocrlf=false apply, outside any '
        'work tree):')
    for i, (step, d) in enumerate((('diag', D_DIAG), ('p2', D_P2), ('fixi', D_FIXI), ('c1v3', D_V3)), 1):
        code, t = run(['git', '-c', 'core.autocrlf=false', 'apply', '--verbose', d], sdk_t)
        res = []
        for rel, sp in staged[step].items():
            got, want = sha(os.path.join(sdk_t, rel)), sha(sp)
            if step in STAGED_WANT and want != STAGED_WANT[step]:
                fail('staged copy for %s is %s' % (step, want[:16]))
            res.append('%s %s (= staged: %s)' % (rel, got[:16], got == want))
            if got != want:
                fail('step %s: %s is %s, staged %s' % (step, rel, got[:16], want[:16]))
        if code:
            fail('step %s apply exit %d: %s' % (step, code, t.strip()))
        say('  %d. %-4s exit %d; %s' % (i, step, code, '; '.join(res)))
    shutil.rmtree(TEST, ignore_errors=True)
    say('script    %s  make_c1v3.py' % sha(os.path.abspath(__file__)))
    say('RESULT ' + ('PASS' if not bad else 'FAIL (%d)' % bad))
    open(os.path.join(HERE, 'HASHES.txt'), 'wb').write(('\n'.join(out) + '\n').encode('utf-8'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
