#!/usr/bin/env python3
"""S5 source scan (read-only, 1 thread; Agent 9, follow-up to task #23).

Group T: users of HighResolutionTimer / TimerQueue (the S4.1.2 / S4.1.3 (d) check for Agent 10).
Group C: where the host-timer cvars are defined and used.
Trees: SDK include/, src/, tests/; rexlego src/ (and include/ if present); plus the rexlego config
toml. Skips thirdparty, out, build, generated and .git directories.
"""
import os
import re
import time

ROOT = r'<workspace>'
SDK = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
LEGO = os.path.join(ROOT, 'DimensionsRecomp', 'rexlego')
HERE = os.path.dirname(os.path.abspath(__file__))
TREES = [('sdk/include', os.path.join(SDK, 'include')), ('sdk/src', os.path.join(SDK, 'src')),
         ('sdk/tests', os.path.join(SDK, 'tests')), ('lego/src', os.path.join(LEGO, 'src')),
         ('lego/include', os.path.join(LEGO, 'include'))]
FILES = [('lego', os.path.join(LEGO, 'legodimensions_config.toml'))]
SKIP = {'thirdparty', 'third_party', 'out', 'build', 'generated', '.git', 'node_modules'}
EXT = {'.h', '.hpp', '.hh', '.hxx', '.inl', '.inc', '.ipp', '.c', '.cc', '.cpp', '.cxx'}
GROUPS = [('T', re.compile(r'HighResolutionTimer|TimerQueue|CreateRepeating|CreateOneShot|QueueTimer|timer_queue')),
          ('C', re.compile(r'host_timer_resolution_ms|host_timer_throttling_optout|timer_resolution_ms'
                           r'|REX_TIMER_WAIT_BLOCKING'))]


def main():
    t0 = time.time()
    hits = []
    errors = []
    stats = {'files': 0, 'chars': 0}
    per_tree = {}

    def scan(tag, path):
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                text = f.read()
        except OSError as e:
            errors.append('%s %s: %s' % (tag, path, e))
            return
        stats['files'] += 1
        stats['chars'] += len(text)
        per_tree[tag] = per_tree.get(tag, 0) + 1
        if not any(g.search(text) for _, g in GROUPS):
            return
        for i, line in enumerate(text.splitlines(), 1):
            for name, g in GROUPS:
                if g.search(line):
                    hits.append((name, tag, path, i, line.strip()))

    missing = []
    for tag, top in TREES:
        if not os.path.isdir(top):
            missing.append(tag)
            continue
        for dp, dns, fns in os.walk(top):
            dns[:] = sorted(d for d in dns if d.lower() not in SKIP)
            for fn in sorted(fns):
                if os.path.splitext(fn)[1].lower() in EXT:
                    scan(tag, os.path.join(dp, fn))
    for tag, p in FILES:
        if os.path.isfile(p):
            scan(tag, p)

    def rel(p):
        return os.path.relpath(p, ROOT).replace('\\', '/')

    out = ['S5 source scan: %d files (%s), %d chars, %.1f s; missing trees: %s'
           % (stats['files'], ', '.join('%s %d' % kv for kv in sorted(per_tree.items())), stats['chars'],
              time.time() - t0, ', '.join(missing) or 'none')]
    for name, _ in GROUPS:
        gh = [h for h in hits if h[0] == name]
        out.append('## group %s: %d hits in %d files' % (name, len(gh), len({h[2] for h in gh})))
        for h in gh:
            out.append('%s %s:%d: %s' % (h[1], rel(h[2]), h[3], h[4][:170]))
    if errors:
        out.append('## errors: %d' % len(errors))
        out.extend(errors)
    with open(os.path.join(HERE, 's5-src-report.txt'), 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
