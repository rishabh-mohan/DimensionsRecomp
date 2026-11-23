#!/usr/bin/env python3
# make_c1v2.py (Agent 12, run-2 task #13 step 5): C1 v2 = C1 v1 + gate D's kept-protect counter (b2r §24
# L1244, §28 L1536/L1548), on scratch. C1 v1 (build/agent12/s4-c1) is only read and stays byte-identical.
# v2 differs from v1 only in SDK src/system/xmemory.cpp:
#   V1  kInitOnly on C1's own cvar physical_protect_keep_watch, with a comment saying why;
#   V2  a kept-protect counter + its log lines, and a one-time "blocked" line (file-static, no header change);
#   V3  the counter at Protect's keep-watch return (under G);
#   V4  the "blocked" line at ProtectKeepWatch's latch check (under G; native only);
#   V5  a state line in Memory::Initialize, printed only with physical_protect_keep_watch on;
#   V6  kInitOnly on fix (i)'s physical_protect_hold_global_lock: an edit on top of #5's definition, inside
#       this diff (#5's staged diff is unchanged). Not kRequiresRestart: cvar.cpp applies that at once and
#       only marks a restart pending. kInitOnly makes both entries read-only in the settings overlay;
#       launch-time sets (toml, command line, env) still work since FinalizeInit is never called.
# Steps:
#   1. C1 v1's copies and diffs match its HASHES.txt, and the live bases are the expected ones;
#   2. the v2 edits on v1's new xmemory.cpp: each anchor exactly once, LF, added lines <= 100 columns,
#      no trailing space;
#   3. writes v1/sdk/src/system/xmemory.cpp (byte copy of v1's), orig/sdk/... (byte copies of v1's C1
#      bases = the S4a outputs), new/sdk/... (v1's 4 other files, unchanged, plus v2's xmemory.cpp);
#   4. diffs: v1-to-v2.diff (interdiff for Agent 10), keep-watch-v2.diff (S4a output -> C1 v2, 5 SDK
#      files; replaces v1's keep-watch.diff), chain-live-to-c1v2.diff (reference: live -> #7+#8+#5+C1 v2);
#      v1's keep-watch-rexlego.diff is reused unchanged;
#   5. git apply --check (read-only) on the live SDK (#7, #8, #5, chain-live-to-c1v2) and the live game
#      repo (keep-watch-rexlego.diff); on scratch, outside any work tree: v1-to-v2 on v1's copy, and the
#      4-step chain #7 -> #8 -> #5 -> keep-watch-v2 on copies of the live files, each result compared
#      with the staged copy;
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
SDK = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
GAME = os.path.join(ROOT, 'DimensionsRecomp')
SCRATCH = r'C:\Users\<user>\.gemini\antigravity-cli\brain\174e1574-a481-4854-9e25-c86c7eb78df3\scratch'
TEST = os.path.join(SCRATCH, 'applytest-c1v2')

D_DIAG = os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'upload-hash-log.diff')
D_P2 = os.path.join(ROOT, 'build', 'agent12', 's4-p2', 'single-hold-rearm.diff')
D_FIXI = os.path.join(ROOT, 'build', 'agent12', 's4-fixi', 'protect-hold-g.diff')
D_GAME = os.path.join(V1, 'keep-watch-rexlego.diff')
D_V2 = os.path.join(HERE, 'keep-watch-v2.diff')
D_INTER = os.path.join(HERE, 'v1-to-v2.diff')
D_COMB = os.path.join(HERE, 'chain-live-to-c1v2.diff')

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
V1_DIFF_WANT = {
    'keep-watch.diff': '1B2BA4E30BC05A1E7157B50DBC90BC819C93E4B16B419BAFE7E62CCF11A4AB70',
    'keep-watch-rexlego.diff': '4D0C10794188CF450046D42B249C9C46D009EE9F4F1B82116954857FA70838BD',
    'chain-live-to-c1.diff': '1D2CC1F3',
}
STAGED_WANT = {'diag': 'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587',
               'p2': '0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4',
               'fixi': '141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A'}

# ----------------------------------------------------------------------------- the v2 edits
EDITS = [
    ('V1 cvar lifecycle',
     '''// PhysicalHeap::ProtectKeepWatch.
REXCVAR_DEFINE_BOOL(physical_protect_keep_watch, false, "Memory",
                    "Keep the write watches on physical write protects that leave every "
                    "page's access unchanged (needs physical_protect_hold_global_lock)");
''',
     '''// PhysicalHeap::ProtectKeepWatch. Both cvars are init-only (C1 v2), so the settings
// overlay can't turn C1 on mid-run over page state from before fix (i) was on.
REXCVAR_DEFINE_BOOL(physical_protect_keep_watch, false, "Memory",
                    "Keep the write watches on physical write protects that leave every "
                    "page's access unchanged (needs physical_protect_hold_global_lock)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
'''),
    ('V6 fix (i) cvar lifecycle',
     '''REXCVAR_DEFINE_BOOL(physical_protect_hold_global_lock, false, "Memory",
                    "Hold the global lock across both host protects in PhysicalHeap::Protect");
''',
     '''REXCVAR_DEFINE_BOOL(physical_protect_hold_global_lock, false, "Memory",
                    "Hold the global lock across both host protects in PhysicalHeap::Protect")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
'''),
    ('V2 counter and log helpers',
     '''bool Memory::IsPhysicalProtectKeepWatchBlocked() {
  return physical_protect_keep_watch_blocked.load(std::memory_order_relaxed);
}
''',
     '''bool Memory::IsPhysicalProtectKeepWatchBlocked() {
  return physical_protect_keep_watch_blocked.load(std::memory_order_relaxed);
}

// S4 C1 v2: log lines that show whether the keep-watch path engaged. Both helpers
// run with the global critical region held; the logger's lock is a leaf. Kept
// protects log the first one, the powers of two below 4096, then every 4096th, so
// the last line gives the total to within 4096.
static constinit std::atomic<uint64_t> physical_protect_kept_count{0};
static constinit std::atomic<bool> physical_protect_keep_watch_block_logged{false};

static void NoteKeptProtect(uint32_t address, uint32_t size) {
  const uint64_t kept = physical_protect_kept_count.fetch_add(1, std::memory_order_relaxed) + 1;
  if (kept == 1) {
    REXSYS_INFO("C1 keep-watch: first kept protect at {:08X}, {} bytes", address, size);
  } else if (!(kept & (kept - 1)) || !(kept & 4095)) {
    REXSYS_INFO("C1 keep-watch: {} protects kept so far", kept);
  }
}

static void NoteKeepWatchBlocked() {
  if (!physical_protect_keep_watch_block_logged.exchange(true, std::memory_order_relaxed)) {
    REXSYS_INFO("C1 keep-watch: blocked for this process (native renderer); every protect "
                "takes the normal path");
  }
}
'''),
    ('V3 count at the keep-watch return',
     '''      ProtectKeepWatch(address, size, protect)) {
    return true;
  }
''',
     '''      ProtectKeepWatch(address, size, protect)) {
    NoteKeptProtect(address, size);
    return true;
  }
'''),
    ('V4 blocked line at the latch',
     '''  if (Memory::IsPhysicalProtectKeepWatchBlocked()) {
    return false;
  }
''',
     '''  if (Memory::IsPhysicalProtectKeepWatchBlocked()) {
    NoteKeepWatchBlocked();
    return false;
  }
'''),
    ('V5 state line at init',
     '''  // A breadcrumb: the arena is the first thing that can fail for reasons
''',
     '''  // S4 C1 v2: whether physical_protect_keep_watch can engage (set both cvars at
  // launch). Prints nothing while it is off.
  if (REXCVAR_GET(physical_protect_keep_watch)) {
    if (IsPhysicalProtectKeepWatchBlocked()) {
      REXSYS_INFO("C1 keep-watch: on, but blocked for this process (native renderer)");
    } else if (!REXCVAR_GET(physical_protect_hold_global_lock)) {
      REXSYS_WARN("C1 keep-watch: on, but physical_protect_hold_global_lock is off, so no "
                  "protect is kept");
    } else {
      REXSYS_INFO("C1 keep-watch: on (with physical_protect_hold_global_lock)");
    }
  }
  // A breadcrumb: the arena is the first thing that can fail for reasons
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
    say('S4 C1 v2 (physical_protect_keep_watch + the kept-protect counter; Agent 12, run-2 task #13). '
        'Staged %s on scratch. Not applied, not built. C1 v1 unchanged.' % stamp)
    code, head = run(['git', '--no-optional-locks', 'rev-parse', '--short', 'HEAD'], SDK)
    code2, ghead = run(['git', '--no-optional-locks', 'rev-parse', '--short', 'HEAD'], GAME)
    say('SDK: DimensionsRecomp/rexglue-sdk HEAD %s; game: DimensionsRecomp HEAD %s.'
        % (head.strip(), ghead.strip()))

    # 1. C1 v1 and the live bases
    v1h = {}
    for l in open(os.path.join(V1, 'HASHES.txt'), encoding='utf-8'):
        m = re.match(r'^(orig|new|diff)\s+([0-9A-F]{64})\s+(?:game )?(\S+?),?\s', l)
        if m:
            v1h[m.group(1) + '|' + m.group(3)] = m.group(2)
    for rel in SDK_C1:
        for side in ('orig', 'new'):
            h = sha(os.path.join(V1, side, 'sdk', rel))
            if h != v1h.get(side + '|' + rel):
                fail('v1 %s/sdk/%s is %s, v1 HASHES.txt says %s' % (side, rel, h[:16],
                                                                  v1h.get(side + '|' + rel, '?')[:16]))
    for side in ('orig', 'new'):
        h = sha(os.path.join(V1, side, 'game', GAME_REL))
        if h != v1h.get(side + '|' + GAME_REL):
            fail('v1 %s/game/%s is %s' % (side, GAME_REL, h[:16]))
    for name, want in V1_DIFF_WANT.items():
        h = sha(os.path.join(V1, name))
        if not h.startswith(want):
            fail('v1 %s is %s, want %s' % (name, h[:16], want[:16]))
    say('v1        build/agent12/s4-c1: 12 orig/new copies and 3 diffs = its HASHES.txt: %s'
        % ('yes' if not bad else 'NO'))
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

    # 2. the v2 edits
    v1_xm = open(os.path.join(V1, 'new', 'sdk', XM), 'rb').read()
    text = v1_xm.decode('utf-8')
    if '\r' in text:
        sys.exit('FAIL v1 xmemory.cpp has CR')
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
    v2_xm = text.encode('utf-8')

    # 3. the stage tree
    for d in ('v1', 'orig', 'new'):
        p = os.path.join(HERE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    copy(os.path.join(V1, 'new', 'sdk', XM), os.path.join(HERE, 'v1', 'sdk', XM))
    for rel in SDK_C1:
        copy(os.path.join(V1, 'orig', 'sdk', rel), os.path.join(HERE, 'orig', 'sdk', rel))
        if rel != XM:
            copy(os.path.join(V1, 'new', 'sdk', rel), os.path.join(HERE, 'new', 'sdk', rel))
    os.makedirs(os.path.dirname(os.path.join(HERE, 'new', 'sdk', XM)), exist_ok=True)
    open(os.path.join(HERE, 'new', 'sdk', XM), 'wb').write(v2_xm)
    say('v1        %s  %s (C1 v1 new, the interdiff base, %d B)' % (sha_bytes(v1_xm), XM, len(v1_xm)))
    for rel in SDK_C1:
        say('orig      %s  %s (C1 base = S4a output)' % (sha(os.path.join(HERE, 'orig', 'sdk', rel)), rel))
        p = os.path.join(HERE, 'new', 'sdk', rel)
        say('new       %s  %s (%d B%s)' % (sha(p), rel, os.path.getsize(p),
                                           ', C1 v2' if rel == XM else ', = v1'))

    # 4. diffs
    inter = mkdiff('v1/sdk/' + XM, 'new/sdk/' + XM, XM)
    open(D_INTER, 'wb').write(inter.encode('utf-8'))
    v2diff = ''.join(mkdiff('orig/sdk/' + rel, 'new/sdk/' + rel, rel) for rel in SDK_C1)
    open(D_V2, 'wb').write(v2diff.encode('utf-8'))
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    finals = {D3D12: os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'new', 'shared_memory.cpp')}
    finals.update({rel: os.path.join(HERE, 'new', 'sdk', rel) for rel in SDK_C1})
    for rel in finals:
        copy(os.path.join(SDK, rel), os.path.join(TEST, 'base', rel))
        copy(finals[rel], os.path.join(TEST, 'final', rel))
    comb = ''.join(mkdiff('base/' + rel, 'final/' + rel, rel, TEST) for rel in sorted(finals))
    open(D_COMB, 'wb').write(comb.encode('utf-8'))
    for name, d in (('v1-to-v2.diff', inter), ('keep-watch-v2.diff', v2diff),
                    ('chain-live-to-c1v2.diff', comb)):
        n, hunks, plus, minus = stats(d)
        say('diff      %s  %s, %d lines, %d hunks, +%d/-%d, LF' % (sha_bytes(d.encode('utf-8')), name, n,
                                                                 hunks, plus, minus))
    say('diff      %s  keep-watch-rexlego.diff (v1, reused unchanged)' % sha(D_GAME))
    for p in (D_DIAG, D_P2, D_FIXI):
        say('chain     %s  %s' % (sha(p), os.path.relpath(p, ROOT).replace('\\', '/')))

    # 5. checks
    for name, d in (('diag', D_DIAG), ('P2', D_P2), ('fix (i)', D_FIXI), ('chain-live-to-c1v2', D_COMB)):
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
    copy(os.path.join(HERE, 'v1', 'sdk', XM), os.path.join(it, XM))
    code, t = run(['git', 'rev-parse', '--is-inside-work-tree'], it)
    if code == 0:
        sys.exit('FAIL scratch dir is inside a work tree: ' + t)
    code, t = run(['git', '-c', 'core.autocrlf=false', 'apply', '--verbose', D_INTER], it)
    ok = code == 0 and sha(os.path.join(it, XM)) == sha_bytes(v2_xm)
    say('scratch   v1 xmemory.cpp + v1-to-v2.diff: exit %d; = C1 v2 new: %s' % (code, ok))
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
        'c1v2': {rel: os.path.join(HERE, 'new', 'sdk', rel) for rel in SDK_C1},
    }
    say('4-step chain on scratch copies of the live files (git -c core.autocrlf=false apply, outside any '
        'work tree):')
    for i, (step, d) in enumerate((('diag', D_DIAG), ('p2', D_P2), ('fixi', D_FIXI), ('c1v2', D_V2)), 1):
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
    say('script    %s  make_c1v2.py' % sha(os.path.abspath(__file__)))
    say('RESULT ' + ('PASS' if not bad else 'FAIL (%d)' % bad))
    open(os.path.join(HERE, 'HASHES.txt'), 'wb').write(('\n'.join(out) + '\n').encode('utf-8'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
