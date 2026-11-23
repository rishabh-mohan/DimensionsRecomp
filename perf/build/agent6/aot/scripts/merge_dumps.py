#!/usr/bin/env python3
"""Merge per-shard gradient_compiler HLSL dump dirs into one dir with single-process semantics (Agent 6 / subagent A).

gradient_compiler writes "<dumpdir>/<sourceName>.hlsl" for every unique shader in ascending XXH3 hash order, so when
several unique shaders share a sourceName the file of the LARGEST hash survives. Shard inputs that collided inside one
shard dir were named "<sourceName>~N.bin" (scan_shaders.py shard); their dump stems are mapped back through the shard
manifest (manifest.tsv) when given, else by stripping a trailing "~N".

usage: merge_dumps.py <out-dir> <shard-dump-dir>... [--manifest shards/manifest.tsv] [--compare <reference-dump-dir>]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys

HDR = re.compile(rb'^// (?:pixel|vertex) shader\s+hash=0x([0-9A-Fa-f]+)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('dumps', nargs='+')
    ap.add_argument('--manifest')
    ap.add_argument('--compare')
    a = ap.parse_args()
    stem_to_name = {}
    if a.manifest:
        with open(a.manifest, encoding='utf-8') as fh:
            next(fh)
            for line in fh:
                shard, fname, source_name = line.rstrip('\n').split('\t')[:3]
                stem_to_name[(shard, os.path.splitext(fname)[0])] = source_name
    best = {}
    files = 0
    for d in a.dumps:
        shard = os.path.basename(os.path.dirname(os.path.normpath(d)))
        for e in os.scandir(d):
            if not e.is_file() or not e.name.endswith('.hlsl'):
                continue
            files += 1
            stem = e.name[:-5]
            name = stem_to_name.get((shard, stem)) if a.manifest else None
            if name is None:
                name = re.sub(r'~\d+$', '', stem)
            with open(e.path, 'rb') as fh:
                m = HDR.match(fh.readline())
            if not m:
                raise SystemExit(f'no shader header in {e.path}')
            h = int(m.group(1), 16)
            cur = best.get(name)
            if cur is None or h > cur[0]:
                best[name] = (h, e.path)
            elif h == cur[0]:
                raise SystemExit(f'hash 0x{h:016X} dumped twice: {cur[1]} and {e.path}')
    os.makedirs(a.out, exist_ok=False)
    for name, (h, p) in sorted(best.items()):
        shutil.copyfile(p, os.path.join(a.out, name + '.hlsl'))
    total = sum(os.path.getsize(os.path.join(a.out, n + '.hlsl')) for n in best)
    result = {'shard_dump_files': files, 'merged_files': len(best), 'merged_bytes': total,
              'collisions_resolved': files - len(best)}
    if a.compare:
        ref = sorted(n for n in os.listdir(a.compare) if n.endswith('.hlsl'))
        got = sorted(n + '.hlsl' for n in best)
        diff = [n for n in sorted(set(ref) & set(got))
                if open(os.path.join(a.compare, n), 'rb').read() != open(os.path.join(a.out, n), 'rb').read()]
        result.update({'reference_files': len(ref), 'only_reference': sorted(set(ref) - set(got))[:20],
                       'only_merged': sorted(set(got) - set(ref))[:20], 'content_diffs': diff[:20],
                       'identical': ref == got and not diff})
    print(json.dumps(result, indent=2))
    return 0 if not a.compare or result['identical'] else 1


if __name__ == '__main__':
    sys.exit(main())
