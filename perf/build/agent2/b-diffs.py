"""Agent 2 (session 3, 02:15): the build-B review diffs (Python difflib; no git) -> build/agent2/B-diffs/.
  python build\\agent2\\b-diffs.py
  preB-tools.diff     <f>.pre-B -> <f>: build-snap.ps1 and stage-snap-bin.ps1 (patch-b-tools.py's 7 + 12 edits),
                      gen-check.py and snap-gate.py (session-2 B options + tonight's docstrings), stop-snap.ps1
  prep-b.nolr.diff    prep-b.py.pre-nolr -> prep-b.py (tonight: batch-nolr only, refuses install/batch, pins)
  run-b.nolr.diff     run-b.ps1.pre-nolr -> run-b.ps1 (tonight: step-0 refusal and pins, devoffB-bin)
  nolr-comments.diff  patch-b-tools.py, gen-check.py, snap-gate.py: .pre-nolr -> current (text only)
  b-chain.new.diff    the new b-chain.ps1 (verify S2 -> prep-b.py -> run-b.ps1)
Checks (exit 1 if any fails):
  - build-snap.ps1 and stage-snap-bin.ps1 == their .pre-B with exactly patch-b-tools.py's EDITS applied (each once);
  - gen-check.py and snap-gate.py .pre-nolr -> current change no code (same AST once docstrings are dropped);
  - patch-b-tools.py .pre-nolr -> current: the same code and the same EDITS search texts; the replacement texts differ
    only in lines that start with '#' (PowerShell comments).
"""
import ast, difflib, hashlib, os, sys

A = r'<workspace>\build\agent2'
OUT = os.path.join(A, 'B-diffs')
fails, oks = [], []


def rd(p):
    return open(p, 'rb').read().decode('utf-8')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def udiff(old, new, la, lb):
    a = rd(old).splitlines() if old else []
    b = rd(new).splitlines()
    d = list(difflib.unified_diff(a, b, la, lb, lineterm='', n=3))
    plus = sum(1 for l in d if l.startswith('+') and not l.startswith('+++'))
    minus = sum(1 for l in d if l.startswith('-') and not l.startswith('---'))
    head = '# %s (%s) -> %s (%s): +%d -%d lines' % (la, sha(old)[:16] if old else 'new file', lb, sha(new)[:16], plus,
                                                    minus)
    return [head] + d, plus, minus


def write(name, blocks):
    p = os.path.join(OUT, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        for b in blocks:
            f.write('\n'.join(b) + '\n')
    return p


def is_edits(n):
    return isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EDITS' for t in n.targets)


def nodoc(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = node.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(
                    b[0].value.value, str):
                node.body = b[1:] or [ast.Pass()]
    return ast.dump(tree)


def edits_of(src):
    return next(ast.literal_eval(n.value) for n in ast.parse(src).body if is_edits(n))


def rest_of(src):
    t = ast.parse(src)
    t.body = [n for n in t.body if not is_edits(n)]
    return nodoc(t)


def main():
    os.makedirs(OUT, exist_ok=True)
    stats = []
    # 1. preB-tools.diff
    blocks = []
    for f in ('build-snap.ps1', 'stage-snap-bin.ps1', 'gen-check.py', 'snap-gate.py', 'stop-snap.ps1'):
        blk, p, m = udiff(os.path.join(A, f + '.pre-B'), os.path.join(A, f), f + '.pre-B', f)
        blocks.append(blk)
        stats.append('preB-tools.diff   %-20s +%d -%d' % (f, p, m))
    diffs = [write('preB-tools.diff', blocks)]
    # 2. prep-b / run-b
    for f, name in (('prep-b.py', 'prep-b.nolr.diff'), ('run-b.ps1', 'run-b.nolr.diff')):
        blk, p, m = udiff(os.path.join(A, f + '.pre-nolr'), os.path.join(A, f), f + '.pre-nolr', f)
        diffs.append(write(name, [blk]))
        stats.append('%-17s %-20s +%d -%d' % (name, f, p, m))
    # 3. nolr-comments.diff
    blocks = []
    for f in ('patch-b-tools.py', 'gen-check.py', 'snap-gate.py'):
        blk, p, m = udiff(os.path.join(A, f + '.pre-nolr'), os.path.join(A, f), f + '.pre-nolr', f)
        blocks.append(blk)
        stats.append('nolr-comments.diff %-19s +%d -%d' % (f, p, m))
    diffs.append(write('nolr-comments.diff', blocks))
    # 4. b-chain.new.diff
    blk, p, m = udiff(None, os.path.join(A, 'b-chain.ps1'), '/dev/null', 'b-chain.ps1')
    diffs.append(write('b-chain.new.diff', [blk]))
    stats.append('b-chain.new.diff  %-20s +%d -%d' % ('b-chain.ps1', p, m))

    # check: build-snap.ps1 / stage-snap-bin.ps1 == .pre-B + EDITS
    edits = edits_of(rd(os.path.join(A, 'patch-b-tools.py')))
    for name, pairs in edits.items():
        text = rd(os.path.join(A, name + '.pre-B'))
        bad = None
        for i, (old, new) in enumerate(pairs):
            n = text.count(old)
            if n != 1:
                bad = 'edit %d matches %d times in %s.pre-B' % (i, n, name)
                break
            text = text.replace(old, new)
        if bad is None and text != rd(os.path.join(A, name)):
            bad = '%s != %s.pre-B with the %d EDITS applied' % (name, name, len(pairs))
        (fails if bad else oks).append(bad or '%s == %s.pre-B + exactly patch-b-tools.py\'s %d EDITS' % (
            name, name, len(pairs)))
    # check: gen-check.py / snap-gate.py .pre-nolr -> current: docstrings only
    for f in ('gen-check.py', 'snap-gate.py'):
        same = nodoc(ast.parse(rd(os.path.join(A, f + '.pre-nolr')))) == nodoc(ast.parse(rd(os.path.join(A, f))))
        (oks if same else fails).append('%s .pre-nolr -> current: %s' % (
            f, 'docstring/comment changes only (same AST without docstrings)' if same else 'CODE CHANGED'))
    # check: patch-b-tools.py .pre-nolr -> current: '#' lines in the replacement texts only
    o_src, n_src = rd(os.path.join(A, 'patch-b-tools.py.pre-nolr')), rd(os.path.join(A, 'patch-b-tools.py'))
    oe, ne = edits_of(o_src), edits_of(n_src)
    probs = []
    if rest_of(o_src) != rest_of(n_src):
        probs.append('code outside EDITS changed')
    if list(oe) != list(ne):
        probs.append('EDITS file list changed')
    nlines = 0
    for name in oe:
        if name not in ne or len(oe[name]) != len(ne[name]):
            probs.append('%s: edit count changed' % name)
            continue
        for i, ((o_old, o_new), (n_old, n_new)) in enumerate(zip(oe[name], ne[name])):
            if o_old != n_old:
                probs.append('%s edit %d: search text changed' % (name, i))
            for l in difflib.unified_diff(o_new.splitlines(), n_new.splitlines(), lineterm='', n=0):
                if l.startswith(('---', '+++', '@@')):
                    continue
                nlines += 1
                if not l[1:].lstrip().startswith('#'):
                    probs.append('%s edit %d: non-comment line changed: %s' % (name, i, l[:80]))
    (fails if probs else oks).append('patch-b-tools.py .pre-nolr -> current: %s' % (
        '; '.join(probs) if probs else 'same code and search texts; %d changed replacement lines, all \'#\' '
                                       'comments' % nlines))

    for s in stats:
        print(s)
    for d in diffs:
        print('diff %-20s %6d B sha256 %s' % (os.path.basename(d), os.path.getsize(d), sha(d)))
    for f in ('prep-b.py', 'run-b.ps1', 'b-chain.ps1', 'patch-b-tools.py', 'build-snap.ps1', 'stage-snap-bin.ps1',
              'gen-check.py', 'snap-gate.py', 'stop-snap.ps1'):
        print('file %-20s sha256 %s' % (f, sha(os.path.join(A, f))))
    for s in oks:
        print('CHECK PASS ' + s)
    for s in fails:
        print('CHECK FAIL ' + s)
    print('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
