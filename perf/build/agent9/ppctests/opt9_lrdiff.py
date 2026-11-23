# opt (10 keys, skip_lr) vs opt9 (9 keys = LEGO build B): T8 generated sources must differ only in ctx.lr lines.
import difflib, hashlib, os, re, sys
P = r'<workspace>\build\agent9\ppctests'
for f in ('ppc_test_cases.cpp', 'ppc_config.h', 'ppc_test_decls.h', 'ppc_test_functions.cpp'):
    a = open(os.path.join(P, 'opt', 'generated', f), 'rb').read()
    b = open(os.path.join(P, 'opt9', 'generated', f), 'rb').read()
    print('%-24s opt %s (%d B)  opt9 %s (%d B)  identical %s' % (f, hashlib.sha256(a).hexdigest()[:16], len(a),
          hashlib.sha256(b).hexdigest()[:16], len(b), a == b))
la = open(os.path.join(P, 'opt', 'generated', 'ppc_test_functions.cpp'), encoding='utf-8').read().splitlines()
lb = open(os.path.join(P, 'opt9', 'generated', 'ppc_test_functions.cpp'), encoding='utf-8').read().splitlines()
lr = re.compile(r'\bctx\.lr\b')
fa = [l for l in la if not lr.search(l)]
fb = [l for l in lb if not lr.search(l)]
print('ppc_test_functions.cpp lines: opt %d (%d with ctx.lr), opt9 %d (%d with ctx.lr)'
      % (len(la), len(la) - len(fa), len(lb), len(lb) - len(fb)))
print('without ctx.lr lines: identical %s' % (fa == fb))
# classify the ctx.lr lines
def kinds(ls):
    k = {}
    for l in ls:
        if lr.search(l):
            s = l.strip()
            key = ('store ctx.lr = imm' if re.match(r'ctx\.lr\s*=\s*0x[0-9A-Fa-f]+', s) else
                   'ctx.lr = reg' if re.match(r'ctx\.lr\s*=', s) else
                   'read ctx.lr' if '= ctx.lr' in s else 'other')
            k[key] = k.get(key, 0) + 1
    return k
print('opt  ctx.lr kinds:', kinds(la))
print('opt9 ctx.lr kinds:', kinds(lb))
if fa != fb:
    d = list(difflib.unified_diff(fa, fb, 'opt', 'opt9', n=1, lineterm=''))
    print('%d diff lines; first 40:' % len(d))
    print('\n'.join(d[:40]))
