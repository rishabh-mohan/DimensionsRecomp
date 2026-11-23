"""Agent 9, session 3: map a host crash address in legodimensions.exe to its public symbol (guest function).

The runtime's crash handler logs "[FATAL] That is legodimensions.exe+0x<RVA> (module base 0x...)"
(rexglue-sdk/src/core/exception_handler_win.cpp). This looks the RVA up in the build's link map (preferred base
0x140000000) and, for a recompiled function, prints where DEFINE_REX_FUNC(sub_XXXXXXXX) is in the generated source.

Usage:
  python build/agent9/addr2sub.py [--build B|A|<bin dir>] [--gen <generated/default dir>] [--log game.log ...] [ADDR ...]
  ADDR: legodimensions.exe+0x<RVA>, 0x<RVA>, or an Rva+Base value 0x14xxxxxxx.
  --build B (default): build/agent2/devoffB-bin, generated = build/agent9/install/batch-nolr/generated/default
  --build A: build/agent2/devoff2-bin, generated = baseline/DimensionsRecomp/rexlego/generated/default
Read-only, one thread.
"""
import argparse, bisect, os, re, sys

R = r'<workspace>'
BUILDS = {
    'B': (os.path.join(R, 'build', 'agent2', 'devoffB-bin'),
          os.path.join(R, 'build', 'agent9', 'install', 'batch-nolr', 'generated', 'default')),
    'A': (os.path.join(R, 'build', 'agent2', 'devoff2-bin'),
          os.path.join(R, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated', 'default')),
}
BASE = 0x140000000
TU = re.compile(r'^(legodimensions_recomp\.\d+\.cpp|legodimensions_init\.cpp|legodimensions_register\.cpp)\.obj$')
FATAL = re.compile(r'That is (\S+)\+0x([0-9A-Fa-f]+) \(module base')


def load_map(path):
    syms, state = [], 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            s = line.strip()
            if state == 0:
                if s.startswith('Address') and 'Publics by Value' in s:
                    state = 1
                continue
            if s.startswith('entry point at'):
                break
            p = s.split()
            if len(p) < 4 or ':' not in p[0]:
                continue
            try:
                va = int(p[2], 16)
            except ValueError:
                continue
            if p[0].startswith('0001:') and not p[1].startswith('__imp__'):
                syms.append((va, p[1], p[-1]))
    syms.sort()
    return syms


def find_def(gen, obj, name):
    m = TU.match(obj)
    if not m or not gen:
        return None
    src = os.path.join(gen, m[1])
    if not os.path.isfile(src):
        return None
    needle = 'DEFINE_REX_FUNC(%s)' % name
    with open(src, encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if line.startswith(needle):
                return '%s:%d' % (os.path.relpath(src, R), i)
    return None


def parse_addr(a):
    a = a.strip()
    m = re.fullmatch(r'(?:(\S+?)\+)?(0x)?([0-9A-Fa-f]+)', a)
    if not m:
        raise ValueError(a)
    mod, v = m[1], int(m[3], 16)
    if mod and mod.lower() != 'legodimensions.exe':
        return mod, v
    return 'legodimensions.exe', v - BASE if v >= BASE else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', default='B')
    ap.add_argument('--gen', default=None)
    ap.add_argument('--log', action='append', default=[])
    ap.add_argument('addr', nargs='*')
    a = ap.parse_args()
    if a.build in BUILDS:
        bindir, gen = BUILDS[a.build]
    else:
        bindir, gen = a.build, None
    gen = a.gen or gen
    addrs = list(a.addr)
    for lg in a.log:
        with open(lg, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = FATAL.search(line)
                if m:
                    addrs.append('%s+0x%s' % (m[1], m[2]))
    if not addrs:
        print('no addresses (and no "That is <module>+0x..." line in the logs)')
        return 1
    syms = load_map(os.path.join(bindir, 'legodimensions.map'))
    keys = [s[0] for s in syms]
    print('map %s: %d code publics; generated %s' % (os.path.relpath(os.path.join(bindir, 'legodimensions.map'), R),
                                                     len(syms), os.path.relpath(gen, R) if gen else '-'))
    for s in addrs:
        mod, rva = parse_addr(s)
        if mod != 'legodimensions.exe':
            print('%s: in %s, not legodimensions.exe (no map here)' % (s, mod))
            continue
        va = BASE + rva
        i = bisect.bisect_right(keys, va) - 1
        if i < 0:
            print('legodimensions.exe+0x%X: before the first code public' % rva)
            continue
        sva, name, obj = syms[i]
        nxt = syms[i + 1][0] if i + 1 < len(syms) else None
        where = find_def(gen, obj, name)
        print('legodimensions.exe+0x%X -> %s+0x%X (%s; next public at +0x%s)%s'
              % (rva, name, va - sva, obj, '%X' % (nxt - sva) if nxt else '?', ('; ' + where) if where else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
