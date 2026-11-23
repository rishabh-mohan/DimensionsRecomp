"""Agent 2 - S3 prep (read only): diff the S2 (snap1) and live versions of the S3 runtime inputs and list the string
literals of 16+ chars that are new in S3, with whether the staged S2 binaries already contain them (they must not).
Run: python build\\agent2\\s3-strings.py
"""
import difflib
import os
import re

R = r'<workspace>'
LIVE = os.path.join(R, 'DimensionsRecomp')
SNAP = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp')
FILES = ['rexlego/src/settings_registry.cpp', 'rexlego/src/settings_preferences.cpp',
         'rexglue-sdk/src/audio/audio_system.cpp', 'rexglue-sdk/src/ui/rex_app.cpp',
         'rexglue-sdk/src/kernel/xam/xam_ui.cpp', 'rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_hal.cpp']
BINS = {k: os.path.join(R, 'build', 'agent2', v) for k, v in {
    'devoff2 exe': 'devoff2-bin/legodimensions.exe', 'devoff2 rexruntime': 'devoff2-bin/rexruntime.dll',
    'native2 exe': 'native2-bin/legodimensions.exe', 'native2 rexruntime': 'native2-bin/rexruntime.dll'}.items()}
LIT = re.compile(r'"((?:[^"\\\n]|\\.){16,})"')


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


blobs = {}
for k, p in BINS.items():
    with open(p, 'rb') as f:
        blobs[k] = f.read()
for rel in FILES:
    old, new = read(os.path.join(SNAP, rel)), read(os.path.join(LIVE, rel))
    print('=' * 100)
    print(rel)
    for ln in difflib.unified_diff(old.splitlines(), new.splitlines(), 'S2/' + rel, 'live/' + rel, n=1, lineterm=''):
        print('  ' + ln)
    olds = set(LIT.findall(old))
    for lit in sorted(set(LIT.findall(new)) - olds):
        b = lit.encode('utf-8').decode('unicode_escape').encode('latin-1', 'replace')
        hits = [k for k, v in blobs.items() if b in v]
        print('  NEW LITERAL (%d chars): %r  in S2 bins: %s' % (len(lit), lit, ', '.join(hits) or 'none'))
