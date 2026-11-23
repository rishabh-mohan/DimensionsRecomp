"""Run gpu-aot fixtures on the baseline tree and the dev tree and diff their compiler errors.

Both trees fail many fixtures already (stale fakes/anchors), so pass/fail alone cannot show
whether a dev edit added a new break. This keeps the full output and compares the sets of
normalised `error:` / `Assertion` lines (paths and line:col removed).

Usage (devshell): python bench/agent4/compare_fixture_errors.py <out-dir> [test.py ...]
"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TREES = {'base': ROOT / 'baseline/DimensionsRecomp', 'dev': ROOT / 'DimensionsRecomp'}
DEFAULT = [
    'test_query_retirement.py', 'test_query_sample_pool.py', 'test_constant_timing.py',
    'test_binding_caches.py', 'test_cull_state.py', 'test_shader_binding_failures.py',
    'test_draw_index_bounds.py', 'test_nonindexed_buffer_windows.py', 'test_quad_buffer_windows.py',
    'test_preparation_metadata.py', 'test_frame_cadence.py', 'test_buffer_view_generation.py',
    'test_draw_upload.py', 'test_frame_ring_transaction.py', 'test_texture_authority_probe.py',
    'test_texture_binding_failures.py', 'test_texture_prepare.py',
]
LOC = re.compile(r'^.*?[\\/]([^\\/:]+):\d+:\d+: ')


def errors(text: str) -> collections.Counter:
    out = collections.Counter()
    for line in text.splitlines():
        if 'error:' in line or 'AssertionError' in line:
            out[LOC.sub(r'\1: ', line.strip())] += 1
    return out


def run(tree: Path, test: str, work: Path) -> str:
    if work.exists():
        for p in sorted(work.rglob('*'), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    r = subprocess.run([sys.executable, str(tree / 'tools/gpu-aot' / test), str(work)],
                       capture_output=True, text=True, timeout=600)
    return f'rc={r.returncode}\n{r.stdout}{r.stderr}'


def main() -> int:
    out = Path(sys.argv[1]).resolve()
    tests = sys.argv[2:] or DEFAULT
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for test in tests:
        stem = test.removesuffix('.py')
        texts = {}
        for key, tree in TREES.items():
            texts[key] = run(tree, test, out / key / stem)
            (out / f'{stem}.{key}.log').write_text(texts[key])
        base, dev = errors(texts['base']), errors(texts['dev'])
        new = sorted((dev - base).elements())
        gone = sorted((base - dev).elements())
        report[test] = {'base_rc': texts['base'].split('\n', 1)[0],
                        'dev_rc': texts['dev'].split('\n', 1)[0],
                        'new_in_dev': new, 'gone_in_dev': gone}
        print(f"{test}: base {report[test]['base_rc']} dev {report[test]['dev_rc']} "
              f"new={len(new)} gone={len(gone)}", flush=True)
        for line in new[:12]:
            print(f'  + {line}', flush=True)
        for line in gone[:6]:
            print(f'  - {line}', flush=True)
    (out / 'compare.json').write_text(json.dumps(report, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
