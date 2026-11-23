#!/usr/bin/env python3
"""s4-estimate.py (Agent 2, task #30 for Agent 11): build-time estimate for S4.

Read-only. It parses <tree>/.ninja_log and <tree>/.ninja_deps of my snapshot
build trees. It runs no ninja and writes nothing in any tree. For each scenario
(a list of changed-file path suffixes) it finds the edges whose recorded deps
include a changed file, either directly or through another affected edge's
output (e.g. a PCH). It then sums the durations those edges took in their last
recorded build (measured under -j10 load). Link, custom and configure edges
have no deps records; they are listed separately from the log.
Writes build/agent2/s4-estimate.txt and prints a short summary.
"""
import collections
import datetime
import os
import struct

ROOT = r'<workspace>'
A2 = os.path.join(ROOT, 'build', 'agent2')
OUT = os.path.join(A2, 's4-estimate.txt')
TREES = ['snap1-sdk', 'snap1-off', 'snap1-on', 'snapB-off', 'snapB3-on']

SDK_CPP = ['/system/xmemory.cpp', '/graphics/shared_memory.cpp',
           '/graphics/d3d12/shared_memory.cpp', '/graphics/primitive_processor.cpp',
           '/graphics/command_processor.cpp', '/graphics/d3d12/command_processor.cpp',
           '/graphics/d3d12/deferred_command_list.cpp', '/graphics/d3d12/pipeline_cache.cpp',
           '/timer_queue.cpp']
SDK_H_XMEM = ['/system/xmemory.h']
SDK_H_GFX = ['/graphics/shared_memory.h', '/graphics/command_processor.h',
             '/graphics/d3d12/command_processor.h', '/graphics/d3d12/deferred_command_list.h',
             '/graphics/d3d12/pipeline_cache.h']
LEGO = ['/gpu_native/shaders.cpp', '/gpu_native/hooks_buffer.cpp',
        '/gpu_native/native_worker.cpp', '/gpu_native/native_recording.cpp',
        '/gpu_native/native_preparation.h']
FPRINT = ['/native_gpu_build_info.h']  # regenerated when a fingerprint input changes

SCEN = [
    ('A S4-1 as listed (incl. xmemory.h)', SDK_CPP + SDK_H_XMEM + SDK_H_GFX + LEGO + FPRINT),
    ('B S4-1 without the xmemory.h change', SDK_CPP + SDK_H_GFX + LEGO + FPRINT),
    ('C S4-1 .cpp only (no SDK header)', SDK_CPP + LEGO + FPRINT),
    ('D xmemory.h alone', SDK_H_XMEM),
    ('E item 2 runtime pack (+fingerprint)', ['/runtime-cache.cpp'] + FPRINT),
    ('F codegen builders/system.cpp', ['/codegen/builders/system.cpp']),
    ('G thread/timer_queue.h alone', ['/thread/timer_queue.h']),
    ('K1 calib S3d draw.cpp (+fingerprint)', ['/gpu_native/draw.cpp'] + FPRINT),
    ('K2 calib S3 SDK .cpp files', ['/rex_app.cpp', '/audio_system.cpp',
                                    '/settings_registry.cpp', '/settings_preferences.cpp']),
]

lines = []


def w(s=''):
    lines.append(s)


def norm(p):
    return p.replace('\\', '/').lower()


def ts_local(mt):
    # ninja 1.11 on Windows: FILETIME minus 12622770400 s, in 100 ns ticks; shown as CST
    if not mt or mt <= 0:
        return '-'
    try:
        t = datetime.datetime(1601, 1, 1) + datetime.timedelta(
            microseconds=(mt + 12622770400 * 10 ** 7) / 10)
        return (t - datetime.timedelta(hours=6)).strftime('%m-%d %H:%M')
    except (OverflowError, ValueError):
        return '?'


def load_log(tree):
    p = os.path.join(A2, tree, '.ninja_log')
    last, runs = {}, []
    cur, prev_end = None, None
    with open(p, 'r', encoding='utf-8', errors='replace') as f:
        head = f.readline().strip()
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 5:
                continue
            try:
                s, e, mt = int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                continue
            if prev_end is None or e < prev_end:
                cur = {'n': 0, 'start': s, 'end': e, 'sum': 0, 'mt': 0}
                runs.append(cur)
            cur['n'] += 1
            cur['start'] = min(cur['start'], s)
            cur['end'] = max(cur['end'], e)
            cur['sum'] += e - s
            cur['mt'] = max(cur['mt'], mt)
            prev_end = e
            last[norm(parts[3])] = (e - s, len(runs) - 1, parts[3], mt)
    return head, last, runs


def load_deps(tree):
    p = os.path.join(A2, tree, '.ninja_deps')
    with open(p, 'rb') as f:
        data = f.read()
    if data[:12] != b'# ninjadeps\n':
        raise SystemExit('%s: not a ninja deps log' % p)
    ver = struct.unpack_from('<i', data, 12)[0]
    pos, n = 16, len(data)
    paths, deps, bad = [], {}, 0
    while pos + 4 <= n:
        hdr = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        size = hdr & 0x7FFFFFFF
        if pos + size > n:
            bad += 1
            break
        if hdr & 0x80000000:
            out_id = struct.unpack_from('<i', data, pos)[0]
            first = pos + (12 if ver >= 4 else 8)
            cnt = (pos + size - first) // 4
            deps[out_id] = struct.unpack_from('<%di' % cnt, data, first)
        else:
            name = data[pos:pos + size - 4].rstrip(b'\0').decode('utf-8', 'replace')
            chk = struct.unpack_from('<I', data, pos + size - 4)[0]
            if (~chk & 0xFFFFFFFF) != len(paths):
                bad += 1
            paths.append(name)
        pos += size
    return ver, paths, deps, bad


def categorize(out):
    q = norm(out)
    if 'cmake_pch' in q:
        return 'pch'
    if '/generated/' in q or 'legodimensions_recomp' in q:
        return 'generated'
    if 'gpu_native' in q:
        return 'gpu_native'
    if 'legodimensions.dir/src/' in q:
        return 'rexlego-src'
    if 'thirdparty' in q or 'plume' in q:
        return 'thirdparty'
    if q.startswith('src/') or '/src/' in q:
        return 'sdk-src'
    return 'other'


def evaluate(low, deps, pats):
    changed = set(i for i, p in enumerate(low) if any(p.endswith(s) for s in pats))
    matched = sorted(set(low[i] for i in changed))
    aff, grew = set(), True
    while grew:
        grew = False
        for out, ins in deps.items():
            if out in aff:
                continue
            if not changed.isdisjoint(ins):
                aff.add(out)
                if out not in changed:
                    changed.add(out)
                    grew = True
    return matched, aff


def fmt_cats(rows):
    c, cn = collections.Counter(), collections.Counter()
    for d, p in rows:
        k = categorize(p)
        c[k] += d
        cn[k] += 1
    return ', '.join('%s %d/%.0fs' % (k, cn[k], c[k] / 1000.0) for k in sorted(c))


def main():
    w('s4-estimate.py report, generated %s (read-only; durations = last recorded build, '
      'under -j10 load)' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    summary = []
    fp = os.path.join(A2, 'snap1-on', 'generate-native-gpu-fingerprint.cmake')
    if os.path.exists(fp):
        with open(fp, encoding='utf-8', errors='replace') as f:
            txt = norm(f.read())
        for nm in ['shaders.cpp', 'hooks_buffer.cpp', 'native_worker.cpp', 'native_recording.cpp',
                   'native_preparation.h', 'runtime-cache.cpp', 'draw.cpp']:
            w('fingerprint input %-22s %s' % (nm, 'yes' if ('/' + nm) in txt else 'NO'))
    for tree in TREES:
        if not os.path.isdir(os.path.join(A2, tree)):
            w('%s: missing' % tree)
            continue
        head, last, runs = load_log(tree)
        ver, paths, deps, bad = load_deps(tree)
        low = [norm(p) for p in paths]
        w('')
        w('=' * 100)
        w('%s: log "%s", %d outputs, %d runs; deps v%d, %d paths, %d records, %d bad'
          % (tree, head, len(last), len(runs), ver, len(paths), len(deps), bad))
        w('  runs (last 10): idx edges wall_s sum_s par last_edge_start')
        for k, r in list(enumerate(runs))[-10:]:
            wall = (r['end'] - r['start']) / 1000.0
            par = (r['sum'] / 1000.0 / wall) if wall > 0 else 0.0
            w('   %3d %5d %8.1f %9.1f %5.2f %s' % (k, r['n'], wall, r['sum'] / 1000.0, par,
                                                  ts_local(r['mt'])))
        allrows = [(v[0], v[2]) for v in last.values()]
        w('  latest-entry totals by category: ' + fmt_cats(allrows))
        w('  longest edges (latest):')
        for d, ri, out, mt in sorted(last.values(), key=lambda v: -v[0])[:10]:
            w('   %7.1f s  run %d  %s' % (d / 1000.0, ri, out))
        w('  .exe/.dll/.lib outputs (latest, top 8):')
        links = [v for v in last.values() if norm(v[2]).endswith(('.exe', '.dll', '.lib'))]
        for d, ri, out, mt in sorted(links, key=lambda v: -v[0])[:8]:
            w('   %7.1f s  run %d  %s' % (d / 1000.0, ri, out))
        keys = ('runtime', 'prelink', 'dxil-cache', 'linked-bank', 'microcode', 'fingerprint',
                'build_info', 'hooks_', 'build.ninja', 'native_worker', 'native_recording',
                'shaders.cpp')
        w('  special edges (latest):')
        for v in sorted(last.values(), key=lambda v: norm(v[2])):
            if any(k in norm(v[2]) for k in keys):
                w('   %7.1f s  run %d  %s' % (v[0] / 1000.0, v[1], v[2]))
        for name, pats in SCEN:
            pats = [norm(s) for s in pats]
            matched, aff = evaluate(low, deps, pats)
            rows, unknown = [], 0
            for o in aff:
                e = last.get(low[o])
                if e is None:
                    unknown += 1
                    continue
                rows.append((e[0], paths[o]))
            rows.sort(key=lambda r: -r[0])
            work = sum(r[0] for r in rows) / 1000.0
            pch = sum(r[0] for r in rows if 'cmake_pch' in norm(r[1])) / 1000.0
            longest = max([r[0] for r in rows if 'cmake_pch' not in norm(r[1])] or [0]) / 1000.0
            est = pch + max((work - pch) / 10.0, longest)
            w('  [%s] %d dep paths matched; %d edges (+%d no log entry); work %.0f s; pch %.0f s;'
              ' longest %.0f s; compile wall at -j10 ~%.0f s' % (name, len(matched), len(rows),
                                                                  unknown, work, pch, longest, est))
            w('     by category: ' + fmt_cats(rows))
            for m in matched[:10]:
                w('     dep: ' + m)
            if len(matched) > 10:
                w('     dep: ... %d more' % (len(matched) - 10))
            for d, p in rows[:5]:
                w('     top: %6.1f s %s' % (d / 1000.0, p))
            summary.append((tree, name, len(rows), work, est))
    tmp = OUT + '.new'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    os.replace(tmp, OUT)
    print('%-10s %-40s %6s %8s %7s' % ('tree', 'scenario', 'edges', 'work_s', 'wall_s'))
    for t, n, k, wk, es in summary:
        print('%-10s %-40s %6d %8.0f %7.0f' % (t, n[:40], k, wk, es))
    print('report: %s (%d lines)' % (OUT, len(lines)))


if __name__ == '__main__':
    main()
