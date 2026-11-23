"""Check the added assertions catch single-line regressions of Agent 4's edits: each mutant is a copy of
the dev sources with one edit reverted or broken, and its fixture must FAIL on it."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

here = Path(__file__).resolve().parent
workspace = here.parents[2]
dev = workspace / 'DimensionsRecomp/rexlego/src/gpu_native'
out_root = workspace / 'build/agent4/fixtures-patched/mutants'
# (id, fixture, file, original text, replacement)
mutants = [
    ('constant-timer-on-workers', 'test_constant_timing', 'draw.cpp',
     'bool enabled = TimingEnabled() && !t_preparing_draw;', 'bool enabled = TimingEnabled();'),
    ('draw-timer-always-on', 'test_constant_timing', 'draw.cpp',
     'bool enabled = TimingEnabled();\r\n  size_t stage', 'bool enabled = true;\r\n  size_t stage'),
    ('draw-timer-serial-counts', 'test_constant_timing', 'draw.cpp',
     '++Select_g_draw_timing(preparation).calls;', '++Select_g_draw_timing(nullptr).calls;'),
    ('scope-no-fast-path', 'test_query_sample_pool', 'queries.cpp',
     'if (active_queries.load(std::memory_order_acquire) == 0) return;', ''),
    ('begin-not-counted', 'test_query_retirement', 'queries.cpp',
     'if (!slot || !slot->active) ++active_queries;', ''),
    ('end-uncounts-dropped', 'test_query_retirement', 'queries.cpp',
     'if (const auto it = queries.find(address); it != queries.end() && it->second == query) --active_queries;',
     '--active_queries;'),
    ('release-not-uncounted', 'test_query_retirement', 'queries.cpp',
     'if (released->active) --active_queries;', ''),
    ('reset-keeps-count', 'test_query_retirement', 'queries.cpp', 'active_queries.store(0);', ''),
]
results = {}
for name, fixture, file, old, new in mutants:
    tree = out_root / name / 'tree'
    sources = tree / 'rexlego/src/gpu_native'
    sources.mkdir(parents=True, exist_ok=True)
    for f in ['draw.cpp', 'draw.h', 'queries.cpp', 'device.cpp']:
        shutil.copyfile(dev / f, sources / f)
    text = (dev / file).read_bytes().decode('latin-1')  # Byte-exact round trip, CRLF kept.
    assert text.count(old) == 1, (name, text.count(old))
    (sources / file).write_bytes(text.replace(old, new).encode('latin-1'))
    run = subprocess.run([sys.executable, str(here / f'{fixture}.py'), '--tree', str(tree), str(out_root / name / 'out')],
                         capture_output=True, text=True, timeout=600)
    failed = re.findall(r'Assertion failed: .*', run.stderr)
    results[name] = {'fixture': fixture, 'caught': run.returncode != 0,
                     'reason': failed[0] if failed else run.stderr.strip().splitlines()[-1:]}
    print(f'{name} [{fixture}]: {"CAUGHT" if run.returncode else "MISSED"} {results[name]["reason"]}', flush=True)
(out_root / 'results.json').write_text(json.dumps(results, indent=2))
