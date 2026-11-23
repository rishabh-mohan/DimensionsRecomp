"""Agent 9, session 3: compare one recompiled function between two generated trees (read-only, one thread).

Extracts the body from 'DEFINE_REX_FUNC(<name>)' to the next 'DEFINE_REX_FUNC(' line in each file and compares:
  - the ordered sequence of guest calls (sub_XXXXXXXX / __imp__* followed by '(')
  - the counts of guest memory macros (uppercase macro names containing LOAD or STORE)
  - other uppercase macro counts and 'ctx.' reference counts (expected to differ under register localization)
Usage: python build/agent9/fncmp.py NAME A_SRC B_SRC
Exit 0 if the call sequence and the memory-macro counts are equal, 1 if not, 2 on a missing definition.
"""
import collections, re, sys

CALL = re.compile(r'\b(sub_[0-9A-Fa-f]{8}|__imp__[A-Za-z_]\w*)\s*\(')
MACRO = re.compile(r'\b([A-Z][A-Z0-9_]{2,})\s*\(')


def body(path, name):
    needle = 'DEFINE_REX_FUNC(%s)' % name
    out, start = [], None
    with open(path, encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if start is None:
                if line.startswith(needle):
                    start = i
                    out.append(line)
                continue
            if line.startswith('DEFINE_REX_FUNC('):
                break
            out.append(line)
    return start, out


def stats(lines, name):
    calls, macros = [], collections.Counter()
    ctx = 0
    for ln in lines[1:]:  # skip the DEFINE line itself
        calls += [c for c in CALL.findall(ln) if c != name and c != '__imp__' + name]
        macros.update(MACRO.findall(ln))
        ctx += ln.count('ctx.')
    return calls, macros, ctx


def main():
    name, a_src, b_src = sys.argv[1:4]
    res = {}
    for tag, src in (('A', a_src), ('B', b_src)):
        start, lines = body(src, name)
        if start is None:
            print('%s: no DEFINE_REX_FUNC(%s) in %s' % (tag, name, src))
            return 2
        calls, macros, ctx = stats(lines, name)
        res[tag] = (calls, macros, ctx)
        print('%s: %s:%d, %d lines, %d calls, ctx. refs %d' % (tag, src, start, len(lines), len(calls), ctx))
    (ca, ma, xa), (cb, mb, xb) = res['A'], res['B']
    print('calls A: %s' % ' '.join(ca))
    print('calls B: %s' % ' '.join(cb))
    same_calls = ca == cb
    print('call sequence equal: %s' % same_calls)
    mem = sorted(k for k in set(ma) | set(mb) if 'LOAD' in k or 'STORE' in k)
    same_mem = all(ma[k] == mb[k] for k in mem)
    print('memory macros (A/B): %s' % ', '.join('%s %d/%d' % (k, ma[k], mb[k]) for k in mem))
    print('memory macro counts equal: %s' % same_mem)
    other = sorted(k for k in set(ma) | set(mb) if k not in mem and ma[k] != mb[k])
    print('other macros that differ (A/B): %s' % (', '.join('%s %d/%d' % (k, ma[k], mb[k]) for k in other) or 'none'))
    print('ctx. refs A/B: %d/%d' % (xa, xb))
    print('RESULT %s' % ('SAME-CALLS-AND-MEMORY' if same_calls and same_mem else 'DIFF'))
    return 0 if same_calls and same_mem else 1


if __name__ == '__main__':
    sys.exit(main())
