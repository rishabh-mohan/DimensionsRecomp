# write_hashes.py (Agent 7, task #9): writes build/agent7/s4-r1r2/HASHES.txt for the S4 #18 / #20-1 staging.
# Re-run it after every make_new.py run. Read-only on the live SDK (hashes only). Exit 1 if a live file is not
# its orig copy (the staging then no longer sits on the live base).
#   python -B build\agent7\s4-r1r2\write_hashes.py
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SDK = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
RELS = [
    'src/graphics/d3d12/command_processor.cpp',
    'include/rex/graphics/d3d12/command_processor.h',
    'include/rex/graphics/d3d12/deferred_command_list.h',
    'src/graphics/d3d12/deferred_command_list.cpp',
]
DIFFS = ['r1-split.diff', 'r2-counters.diff', 's4-r1r2.diff']


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def info(p):
    with open(p, 'rb') as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest().upper(), len(b), b.count(b'\n'), b.count(b'\r')


def main():
    out = []
    out.append('# HASHES.txt - S4 #18 (R1 stage 1, d3d12_submit_split_kb) + #20 step 1 (R2 counters), staging only')
    out.append('# SDK base c5fe668e76853630ffc6df2761e9cd8ed5368476 (DimensionsRecomp/rexglue-sdk), game 08933a7')
    out.append('# produced by make_new.py (new/ from orig/, exact-once edits) + write_hashes.py; SHA-256 upper-case')
    out.append('# kind  sha256  path (SDK-relative for orig/new; stage-relative for diffs)  bytes  lines')
    bad = 0
    live_notes = []
    for rel in RELS:
        o = os.path.join(HERE, 'orig', 'sdk', *rel.split('/'))
        n = os.path.join(HERE, 'new', 'sdk', *rel.split('/'))
        lv = os.path.join(SDK, *rel.split('/'))
        oh, ob, ol, ocr = info(o)
        nh, nb, nl, ncr = info(n)
        lh = sha(lv)
        if ocr or ncr:
            print('CR bytes in %s: orig %d new %d' % (rel, ocr, ncr))
            bad += 1
        out.append('orig %s %s %d %d' % (oh, rel, ob, ol))
        out.append('new  %s %s %d %d' % (nh, rel, nb, nl))
        ok = (lh == oh)
        if not ok:
            bad += 1
        live_notes.append('# live %s %s (%s)' % (lh[:16], rel, '= orig' if ok else 'MISMATCH: live is not the orig copy'))
    for d in DIFFS:
        dh, db, dl, dcr = info(os.path.join(HERE, d))
        out.append('diff %s %s %d %d' % (dh, d, db, dl))
    out.append('# live SDK check at write time (read-only):')
    out.extend(live_notes)
    with open(os.path.join(HERE, 'HASHES.txt'), 'w', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
