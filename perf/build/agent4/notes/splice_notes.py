"""Splice the session-2 block into perf-notes/agent4-draw-path.md (one-shot, idempotence-checked)."""
from pathlib import Path

notes = Path('perf-notes/agent4-draw-path.md')
lines = notes.read_text(encoding='utf-8').split('\n')
if any(l.startswith('## S2. Session 2') for l in lines):
    raise SystemExit('already spliced')
top = Path('build/agent4/notes/s2_top.md').read_text(encoding='utf-8').rstrip('\n').split('\n')
start = next(i for i, l in enumerate(lines) if l.startswith('> **RESUME (session 2, paused'))
end = next(i for i, l in enumerate(lines) if l.startswith('Every estimate below is a reasoned guess.'))
lines[start:end] = top + ['']

status = {
    '1': '**done**: 44 → 2.5 ns (N=0), 1,131 → 2.3 ns (N=256)',
    '2': 'diff for Agent 5 pending',
    '3': '**opt-in done** for index buffer + blend factor (§S2.5); the rest: measure with the CSV first',
    '4': '**done** (hoist): 92.6 → 23.5 ns; inline accessor is Agent 7\'s item (h)',
    '5': '**done**: 34.2 → 1.75 ns (1T), 157 → 1.8 ns (2T)',
    '6': '**done**: 47.0 → 15.2 ns per draw',
    '7': 'not started',
    '8': 'not started',
    '9': '**done**: SSE2 `#else`; v2 compiles, v3 codegen identical',
}
header = next(i for i, l in enumerate(lines) if l.startswith('| # | Opportunity |'))
lines[header] += ' Session 2 |'
lines[header + 1] += '---|'
i = header + 2
while lines[i].startswith('| '):
    key = lines[i].split('|')[1].strip()
    lines[i] += f' {status.pop(key)} |'
    i += 1
assert not status, status
notes.write_text('\n'.join(lines), encoding='utf-8', newline='\n')
print('spliced', start, end, header, i)
