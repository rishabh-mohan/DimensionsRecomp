# c1_mkdiff.py (Agent 12, task #31): diffs and checks for S4 C1 (physical_protect_keep_watch).
#  1. live base hashes (SDK perf/opt c5fe668 work tree, game work tree) are the expected ones;
#  2. keep-watch.diff (SDK, 5 files, on top of diag -> P2 -> fix (i)) and keep-watch-rexlego.diff
#     (game repo, rexlego/src/gpu_native/memory_watch.cpp), LF;
#  3. git apply --check of the whole SDK chain on the live SDK, and of the game diff on the live
#     game repo (read-only checks);
#  4. the 4-step chain on scratch copies outside any work tree: diag -> P2 -> fix (i) -> C1 applied
#     in order to copies of the live files, each step's results compared with the staged copies;
#     the game diff applied to an LF copy of the live file and compared with the LF staged copy.
# Writes build/agent12/s4-c1/HASHES.txt. No live file is written; no git write.
import datetime
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SDK = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
GAME = os.path.join(ROOT, 'DimensionsRecomp')
SCRATCH = r'C:\Users\<user>\.gemini\antigravity-cli\brain\dc5d9ed1-da05-4dd5-ad9f-adf7f2db6488\scratch'
TEST = os.path.join(SCRATCH, 'applytest-c1')

D_DIAG = os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'upload-hash-log.diff')
D_P2 = os.path.join(ROOT, 'build', 'agent12', 's4-p2', 'single-hold-rearm.diff')
D_FIXI = os.path.join(ROOT, 'build', 'agent12', 's4-fixi', 'protect-hold-g.diff')
D_C1 = os.path.join(HERE, 'keep-watch.diff')
D_GAME = os.path.join(HERE, 'keep-watch-rexlego.diff')

D3D12 = 'src/graphics/d3d12/shared_memory.cpp'
SDK_C1 = [
    'include/rex/graphics/shared_memory.h',
    'include/rex/system/xmemory.h',
    'src/graphics/primitive_processor.cpp',
    'src/graphics/shared_memory.cpp',
    'src/system/xmemory.cpp',
]
GAME_REL = 'rexlego/src/gpu_native/memory_watch.cpp'
LIVE_WANT = {
    D3D12: 'B120D07C6709D0D2',
    'src/graphics/shared_memory.cpp': '15C89EDB4B197C17487A9D45208D5CE624DE98ABE416F86942C5D14ED43EB282',
    'src/system/xmemory.cpp': '6E8FA1BA80EF9271D4433DD1BB2CAD0403360E222B22CED78AA4C7951D811DB4',
    'include/rex/system/xmemory.h': '80100865A654AF04',
    'include/rex/graphics/shared_memory.h': '4D861738A94B556B',
    'src/graphics/primitive_processor.cpp': 'E07F690223B564AE',
}
GAME_WANT = '19AE1606C6DB727369A5F119EF3371A8D307F4B42088D5C064F0D2DF8D62D47A'
STAGED = {  # step -> {rel: staged copy}
    'diag': {D3D12: os.path.join(ROOT, 'build', 'agent12', 's4-diag', 'new', 'shared_memory.cpp')},
    'p2': {'src/graphics/shared_memory.cpp': os.path.join(ROOT, 'build', 'agent12', 's4-p2', 'new',
                                                          'shared_memory.cpp')},
    'fixi': {'src/system/xmemory.cpp': os.path.join(ROOT, 'build', 'agent12', 's4-fixi', 'new',
                                                    'xmemory.cpp')},
    'c1': {rel: os.path.join(HERE, 'new', 'sdk', rel) for rel in SDK_C1},
}
STAGED_WANT = {'diag': 'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587',
               'p2': '0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4',
               'fixi': '141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A'}

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


def run(args, cwd, ok=(0,)):
    r = subprocess.run(args, cwd=cwd, capture_output=True)
    text = (r.stdout + r.stderr).decode('utf-8', 'replace')
    return r.returncode, text


def mkdiff(orig, new, rel, cwd=HERE):
    code, text = run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', '--no-color',
                      '--no-ext-diff', '-U3', '--', orig, new], cwd)
    if code != 1:
        sys.exit('FAIL git diff %s: exit %d\n%s' % (rel, code, text))
    lines = text.replace('\r\n', '\n').split('\n')
    o = orig.replace('\\', '/').lstrip('/')
    n = new.replace('\\', '/').lstrip('/')
    res = []
    for l in lines:
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


def main():
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    say('S4 C1 physical_protect_keep_watch (Agent 12, task #31, from Agent 5\'s #28). Staged %s. '
        'Not applied, not built.' % stamp)
    code, head = run(['git', '--no-optional-locks', 'rev-parse', '--short', 'HEAD'], SDK)
    code2, ghead = run(['git', '--no-optional-locks', 'rev-parse', '--short', 'HEAD'], GAME)
    say('SDK: DimensionsRecomp/rexglue-sdk HEAD %s; game: DimensionsRecomp HEAD %s.'
        % (head.strip(), ghead.strip()))

    # 1. live bases
    for rel, want in LIVE_WANT.items():
        h = sha(os.path.join(SDK, rel))
        say('live      %s  %s%s' % (h, rel, '' if h.startswith(want) else '  MISMATCH want ' + want[:16]))
        if not h.startswith(want):
            fail('live base %s' % rel)
    gh = sha(os.path.join(GAME, GAME_REL))
    say('live      %s  game %s (CRLF work tree)%s' % (gh, GAME_REL, '' if gh == GAME_WANT else '  MISMATCH'))
    if gh != GAME_WANT:
        fail('live base %s' % GAME_REL)
    for rel in SDK_C1:
        say('orig      %s  %s (C1 base)' % (sha(os.path.join(HERE, 'orig', 'sdk', rel)), rel))
        say('new       %s  %s (%d B)' % (sha(os.path.join(HERE, 'new', 'sdk', rel)), rel,
                                         os.path.getsize(os.path.join(HERE, 'new', 'sdk', rel))))
    say('orig      %s  game %s (CRLF)' % (sha(os.path.join(HERE, 'orig', 'game', GAME_REL)), GAME_REL))
    say('new       %s  game %s (CRLF, %d B)' % (sha(os.path.join(HERE, 'new', 'game', GAME_REL)), GAME_REL,
                                                os.path.getsize(os.path.join(HERE, 'new', 'game', GAME_REL))))

    # 2. diffs
    parts = [mkdiff('orig/sdk/' + rel, 'new/sdk/' + rel, rel) for rel in SDK_C1]
    sdk_diff = ''.join(parts)
    open(D_C1, 'wb').write(sdk_diff.encode('utf-8'))
    lf = os.path.join(SCRATCH, 'c1-game-lf')
    if os.path.exists(lf):
        shutil.rmtree(lf)
    for side in ('orig', 'new'):
        p = os.path.join(lf, side, GAME_REL)
        os.makedirs(os.path.dirname(p))
        data = open(os.path.join(HERE, side, 'game', GAME_REL), 'rb').read().replace(b'\r\n', b'\n')
        open(p, 'wb').write(data)
    game_diff = mkdiff('orig/' + GAME_REL, 'new/' + GAME_REL, GAME_REL, lf)
    open(D_GAME, 'wb').write(game_diff.encode('utf-8'))
    for name, d in (('keep-watch.diff', sdk_diff), ('keep-watch-rexlego.diff', game_diff)):
        ls = d.split('\n')
        hunks = sum(1 for l in ls if l.startswith('@@'))
        plus = sum(1 for l in ls if l.startswith('+') and not l.startswith('+++'))
        minus = sum(1 for l in ls if l.startswith('-') and not l.startswith('---'))
        say('diff      %s  %s, %d lines, %d hunks, +%d/-%d, LF'
            % (sha_bytes(d.encode('utf-8')), name, len(ls) - 1, hunks, plus, minus))
    for p in (D_DIAG, D_P2, D_FIXI):
        say('chain     %s  %s' % (sha(p), os.path.relpath(p, ROOT).replace('\\', '/')))

    # 3. apply --check on the live trees (read-only). git apply does not chain two patch files
    # that touch the same file within one call (each is checked against the work tree), so: each
    # earlier step alone (they touch different files), then one combined diff, live -> C1 final
    # state, built from the staged copies (chain-live-to-c1.diff; reference only, the 4 diffs
    # stay the canonical form).
    if os.path.exists(TEST):
        shutil.rmtree(TEST)
    finals = {D3D12: STAGED['diag'][D3D12]}
    finals.update(STAGED['c1'])
    for rel in finals:
        for side, src in (('base', os.path.join(SDK, rel)), ('final', finals[rel])):
            p = os.path.join(TEST, side, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(src, p)
    combined = ''.join(mkdiff('base/' + rel, 'final/' + rel, rel, TEST) for rel in sorted(finals))
    d_comb = os.path.join(HERE, 'chain-live-to-c1.diff')
    open(d_comb, 'wb').write(combined.encode('utf-8'))
    say('diff      %s  chain-live-to-c1.diff (diag + P2 + fix (i) + C1 as one diff on live; reference)'
        % sha_bytes(combined.encode('utf-8')))
    for name, d in (('diag', D_DIAG), ('P2', D_P2), ('fix (i)', D_FIXI), ('chain-live-to-c1', d_comb)):
        code, text = run(['git', '--no-optional-locks', 'apply', '--check', d], SDK)
        say('git apply --check (live SDK, %s): exit %d' % (name, code))
        if code:
            say('    | ' + text.strip().replace('\n', '\n    | '))
            fail('apply --check %s' % name)
    code, text = run(['git', '--no-optional-locks', 'apply', '--check', D_GAME], GAME)
    say('git apply --check (live game repo, keep-watch-rexlego.diff): exit %d' % code)
    if code:
        say('    | ' + text.strip().replace('\n', '\n    | '))
        fail('game apply --check')

    # 4. the 4-step chain on scratch copies
    sdk_t = os.path.join(TEST, 'sdk')
    for rel in list(LIVE_WANT):
        p = os.path.join(sdk_t, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        shutil.copyfile(os.path.join(SDK, rel), p)
    code, text = run(['git', 'rev-parse', '--is-inside-work-tree'], sdk_t)
    if code == 0:
        sys.exit('FAIL scratch dir is inside a work tree: ' + text)
    steps = []
    for step, d in (('diag', D_DIAG), ('p2', D_P2), ('fixi', D_FIXI), ('c1', D_C1)):
        code, text = run(['git', '-c', 'core.autocrlf=false', 'apply', '--verbose', d], sdk_t)
        res = []
        for rel, staged in STAGED[step].items():
            got = sha(os.path.join(sdk_t, rel))
            want = sha(staged)
            if step in STAGED_WANT and want != STAGED_WANT[step]:
                fail('staged copy for %s is %s' % (step, want[:16]))
            res.append('%s %s (= staged: %s)' % (rel, got[:16], got == want))
            if got != want:
                fail('step %s: %s is %s, staged %s' % (step, rel, got[:16], want[:16]))
        if code:
            fail('step %s apply exit %d: %s' % (step, code, text.strip()))
        steps.append('  %d. %-4s exit %d; %s' % (len(steps) + 1, step, code, '; '.join(res)))
    say('4-step chain on scratch copies of the live files (git -c core.autocrlf=false apply, outside any work tree):')
    for s in steps:
        say(s)
    game_t = os.path.join(TEST, 'game')
    p = os.path.join(game_t, GAME_REL)
    os.makedirs(os.path.dirname(p))
    open(p, 'wb').write(open(os.path.join(GAME, GAME_REL), 'rb').read().replace(b'\r\n', b'\n'))
    code, text = run(['git', '-c', 'core.autocrlf=false', 'apply', '--verbose', D_GAME], game_t)
    got = sha(p)
    want = sha(os.path.join(lf, 'new', GAME_REL))
    say('  game: LF copy of the live memory_watch.cpp + keep-watch-rexlego.diff: exit %d; %s (= LF staged: %s)'
        % (code, got[:16], got == want))
    if code or got != want:
        fail('game scratch apply')
    say('RESULT ' + ('PASS' if not bad else 'FAIL (%d)' % bad))
    open(os.path.join(HERE, 'HASHES.txt'), 'wb').write(('\n'.join(out) + '\n').encode('utf-8'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
