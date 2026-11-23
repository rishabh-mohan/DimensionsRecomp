"""Run patched fixture copies against the baseline and dev trees, one at a time; write diffs vs the originals."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
workspace = here.parents[2]
trees = {'base': workspace / 'baseline/DimensionsRecomp', 'dev': workspace / 'DimensionsRecomp'}
out_root = workspace / 'build/agent4/fixtures-patched'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('names', nargs='*', help='fixture stems (default: every test_*.py copy here)')
p.add_argument('--trees', nargs='*', default=list(trees))
p.add_argument('--tree-path', action='append', default=[], metavar='NAME=PATH',
               help='add a named tree for --trees, e.g. s32=build/agent4/s32tree/DimensionsRecomp (a scratch copy)')
p.add_argument('--diff-only', action='store_true', help='only rewrite the .diff files')
a = p.parse_args()
for spec in a.tree_path:
    tree_name, _, tree_path = spec.partition('=')
    trees[tree_name] = Path(tree_path).resolve()
names = a.names or sorted(f.stem for f in here.glob('test_*.py'))
results_path = out_root / 'results.json'
results = json.loads(results_path.read_text()) if results_path.exists() else {}
for name in names:
    copy = here / f'{name}.py'
    original = trees['dev'] / 'tools/gpu-aot' / f'{name}.py'
    diff = difflib.unified_diff(original.read_text().splitlines(), copy.read_text().splitlines(),
                                f'DimensionsRecomp/tools/gpu-aot/{name}.py',
                                f'bench/agent4/fixtures/{name}.py', lineterm='')
    (here / f'{name}.diff').write_text('\n'.join(diff) + '\n', newline='\n')
    for tree in [] if a.diff_only else a.trees:
        out = out_root / tree / name
        run = subprocess.run([sys.executable, str(copy), '--tree', str(trees[tree]), str(out)],
                             capture_output=True, text=True, timeout=600)
        log = out_root / tree / f'{name}.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f'rc={run.returncode}\n--- stdout\n{run.stdout}\n--- stderr\n{run.stderr}')
        status = 'PASS' if run.returncode == 0 else 'FAIL'
        results.setdefault(name, {})[tree] = status
        print(f'{name} [{tree}]: {status} ({log.relative_to(workspace)})', flush=True)
out_root.mkdir(parents=True, exist_ok=True)
results_path.write_text(json.dumps(results, indent=2))
