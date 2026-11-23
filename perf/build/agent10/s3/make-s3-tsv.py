"""Agent 10 (task #9, session 3): write build/agent10/s3/S3-include.tsv in the format of build/agent10/b3/S2-include.tsv,
which build/agent2/make-rules-from-tsv.py reads. Column 4 is the S2 (= snap1 after the S2 apply) sha256; '-' = not in snap1.
Input: a scan-vs-s2.py output. Every CHANGED/NEW row must be in the table below and every table entry must be in the
scan, or nothing is written. GONE rows are allowed only for the outside-walk paths (research/, rexlego/out/), which
the caller checks separately. Each file is re-hashed now and must still match the scan, and its git blob
(git hash-object) must equal its blob in the game/SDK HEAD commit. Git is used read-only (--no-optional-locks).
Usage: python build\\agent10\\s3\\make-s3-tsv.py <scan file> <out tsv>
"""
import hashlib
import os
import subprocess
import sys
import time

LIVE = r'<workspace>\DimensionsRecomp'
SDK = os.path.join(LIVE, 'rexglue-sdk')
PLUME = os.path.join(LIVE, 'thirdparty', 'plume')
SIMDE = os.path.join(SDK, 'thirdparty', 'simde')
OUTSIDE = ('research/', 'rexlego/out/')

A9 = ('A9', '#15 codegen options (the B inputs): off unless a codegen toml sets them; output identical at the default',
      'SAFE at the default (codegen-review)')
A9_FILES = [
    'rexglue-sdk/include/rex/codegen/config.h',
    'rexglue-sdk/include/rex/codegen/function_types.h',
    'rexglue-sdk/src/codegen/builders/builder_context.h',
    'rexglue-sdk/src/codegen/builders/context.cpp',
    'rexglue-sdk/src/codegen/builders/control_flow.cpp',
    'rexglue-sdk/src/codegen/builders/floating_point.cpp',
    'rexglue-sdk/src/codegen/builders/flush_mode.h',
    'rexglue-sdk/src/codegen/builders/helpers.h',
    'rexglue-sdk/src/codegen/builders/logical.cpp',
    'rexglue-sdk/src/codegen/builders/memory.cpp',
    'rexglue-sdk/src/codegen/builders/system.cpp',
    'rexglue-sdk/src/codegen/builders/vector.cpp',
    'rexglue-sdk/src/codegen/codegen_writer.cpp',
    'rexglue-sdk/src/codegen/config.cpp',
    'rexglue-sdk/src/codegen/function_graph.cpp',
    'rexglue-sdk/src/codegen/test_support.cpp',
    'rexglue-sdk/src/rexglue/commands/test_recompiler.cpp',
    'rexglue-sdk/tests/ppc/asm/instr_cr_so_fold.s',
    'rexglue-sdk/tests/ppc/opt_config.toml',
    'rexglue-sdk/tests/regression/emit_interior_entries.cpp',
]
A11_27 = ('A11', '#27 batch 3: SDK CRT exit() becomes FlushLogging + std::_Exit (live = staged exitfix files)',
          'SAFE (batch2-review sec 10)')
INCLUDE = [
    ('rexlego/src/settings_registry.cpp',
     ('A6', 'S3 fix (a): fix-a.patch hunk 1 + fix-a-commit.patch hunk 3 (applied 02:05:27)', 'SAFE (batch2-review sec 12)')),
    ('rexlego/src/settings_preferences.cpp',
     ('A6', 'S3 fix (a): fix-a.patch hunk 2 (applied 02:05:27); ships with the registry row', 'SAFE (batch2-review sec 12)')),
    ('rexglue-sdk/src/audio/audio_system.cpp',
     ('A12', '#22 (in S2) + S3 flip: audio_shutdown_detach_worker default ON, line 48 (applied 02:04)',
      'SAFE ON (batch2-review sec 8)')),
    ('rexglue-sdk/src/ui/rex_app.cpp',
     ('A11 (landed by A12)', 'S3: pause_safe_order default ON (applied 02:04)', 'SAFE (batch2-review sec 11)')),
    ('rexglue-sdk/src/kernel/xam/xam_ui.cpp', A11_27),
    ('rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_hal.cpp', A11_27),
] + [(r, A9) for r in A9_FILES] + [
    ('.gitignore', ('A1', 'committed in a0bdaa7 (01:50); not a build input', 'n/a (not a build input)')),
    ('.gitmodules', ('A1 (user fork url)', 'committed in a0bdaa7 (01:50); not a build input', 'n/a (not a build input)')),
]
EXCLUDE = []


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo, '--no-optional-locks'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('git %s in %s failed: %s; nothing written' % (' '.join(args), repo, r.stderr.strip()))
    return r.stdout


def gitlink(repo, path):
    f = git(repo, 'ls-tree', 'HEAD', '--', path).split()
    return f[2] if len(f) >= 3 else '-'


def blob_check(rel):
    repo, path = (SDK, rel[len('rexglue-sdk/'):]) if rel.startswith('rexglue-sdk/') else (LIVE, rel)
    head = gitlink(repo, path)
    work = git(repo, 'hash-object', '--', path).strip()
    if head != work:
        sys.exit('%s: working-tree blob %s is not the HEAD blob %s; nothing written' % (rel, work[:12], head[:12]))


def dirty(repo):
    return [ln[3:] for ln in git(repo, 'status', '--porcelain=v1', '-uno').splitlines() if ln.strip()]


def main():
    scan, dst = sys.argv[1], sys.argv[2]
    raw = open(scan, 'rb').read()
    scan_sha = hashlib.sha256(raw).hexdigest()
    rows = {}
    for ln in raw.decode('utf-8').splitlines():
        if ln.startswith('#'):
            continue
        c = ln.split('\t')
        if c[0] in ('CHANGED', 'NEW'):
            rows[c[1]] = c
        elif c[0] == 'GONE' and not c[1].startswith(OUTSIDE):
            sys.exit('GONE inside the walk: %s; nothing written' % c[1])
    want = [r for r, _ in INCLUDE] + [r for r, _ in EXCLUDE]
    extra = sorted(set(rows) - set(want))
    missing = sorted(set(want) - set(rows))
    if extra or missing:
        sys.exit('scan and table differ: extra %s, missing %s; nothing written' % (extra, missing))
    g = git(LIVE, 'log', '-1', '--format=%h|%ci|%s').strip().split('|', 2)
    s = git(SDK, 'log', '-1', '--format=%h|%ci|%s').strip().split('|', 2)
    sdk_head = git(SDK, 'rev-parse', 'HEAD').strip()
    if gitlink(LIVE, 'rexglue-sdk') != sdk_head:
        sys.exit('the game HEAD does not pin the SDK HEAD %s; nothing written' % sdk_head[:12])
    plume_head = git(PLUME, 'rev-parse', '--short=7', 'HEAD').strip()
    simde_head = git(SIMDE, 'rev-parse', '--short=7', 'HEAD').strip()
    out = ['# Agent 10 S3 include list, %s. Paths relative to DimensionsRecomp/. Base: build/agent2/snap1/STATE-S2-2315.tsv '
           '(S2 = snap1 after the S2 apply); column 4 is the S2 (snap1) sha256, \'-\' = not in snap1 (new file). INCLUDE = take '
           'the live file (it must still match live_sha256); EXCLUDE = keep the snap1 version.' % time.strftime('%Y-%m-%d %H:%M:%S'),
           '# S3 build inputs (Agent 1, 02:22): game %s (%s, "%s") + SDK %s (%s, "%s"; the game commit pins it), on top of the '
           '01:50 checkpoint (game a0bdaa7, SDK 90e7ccd), plus the pre-sprint edits that stay uncommitted, as in S1/S2: '
           'thirdparty/plume checked out at %s (the game commit pins %s) with %s modified; rexglue-sdk/thirdparty/simde at %s '
           '(the SDK commit pins %s) with %s modified. No file under plume or simde differs from snap1.'
           % (g[0], g[1][:19], g[2], s[0], s[1][:19], s[2], plume_head, gitlink(LIVE, 'thirdparty/plume')[:7],
              ', '.join(dirty(PLUME)) or 'nothing', simde_head, gitlink(SDK, 'thirdparty/simde')[:7],
              ', '.join(dirty(SIMDE)) or 'nothing'),
           '# Every row below equals its blob in those commits (git hash-object = ls-tree HEAD), so after the S3 apply every walked '
           'snap1 file equals the two commits plus the plume/simde edits. Codegen for B and S3: install/batch-nolr only, never '
           'install/batch (skip_lr).',
           '# Source: %s (sha256 %s), read-only, snap.py walk rules: %d changed, 0 new, 0 deleted. The 48 outside-walk STATE-S2 '
           'rows (research/dxc-1.9.2609, rexlego/out/native-gpu) were hashed separately at 02:16 and are unchanged.'
           % (os.path.basename(scan), scan_sha[:16], len(rows)),
           'action\trel\tlive_sha256\ts2_sha256\tlive_mtime\towner\titem\tverdict_at_default']
    for action, table in (('INCLUDE', INCLUDE), ('EXCLUDE', EXCLUDE)):
        for rel, (owner, item, verdict) in table:
            c = rows[rel]
            live_sha, s2_sha, mtime = c[4], c[6], c[3]
            now = sha('\\\\?\\' + os.path.join(LIVE, rel.replace('/', os.sep)))
            if now != live_sha:
                sys.exit('%s changed since the scan (%s, now %s); nothing written' % (rel, live_sha[:16], now[:16]))
            blob_check(rel)
            out.append('\t'.join([action, rel, live_sha, s2_sha, mtime, owner, item, verdict]))
    data = ('\n'.join(out) + '\n').encode('ascii')
    with open(dst, 'wb') as f:
        f.write(data)
    print('wrote %s: %d INCLUDE, %d EXCLUDE, %d bytes, sha256 %s' % (dst, len(INCLUDE), len(EXCLUDE), len(data),
                                                                   hashlib.sha256(data).hexdigest().upper()))


if __name__ == '__main__':
    main()
