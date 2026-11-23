# assemble_report.py - builds REPORT.md = report-head.md + verify-out.md + appendices; fills the end-of-run
# script hashes. Run from the workspace root after verify.py.
import hashlib, os

CHK = os.path.join('build', 'agent11', 's4a', 'slowstate3-check')


def rd(n):
    with open(os.path.join(CHK, n), encoding='utf-8-sig') as f:
        return f.read()


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


head = rd('report-head.md')
head = head.replace('{{SHA_3MODE_END}}', sha(os.path.join('bench', 'agent11', 'timerq_slowstate_3mode.ps1')))
head = head.replace('{{SHA_ORIG_END}}', sha(os.path.join('bench', 'agent11', 'timerq_slowstate.ps1')))
ver = rd('verify-out.md')
longtxt = '\n'.join(l.rstrip() for l in rd('synth-long.txt').splitlines()[:6])
probe = '\n'.join(l.rstrip() for l in rd('probe-out.txt').splitlines())
app = ('\n## Appendix A: column-width probe (synth-long.txt, first lines)\n\n```text\n' + longtxt + '\n```\n\n'
       '## Appendix B: probe.ps1 output (Windows PowerShell 5.1)\n\n```text\n' + probe + '\n```\n')
out = head.rstrip('\n') + '\n\n' + ver.rstrip('\n') + '\n' + app
with open(os.path.join(CHK, 'REPORT.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(out)
print('REPORT.md sha256', hashlib.sha256(out.encode('utf-8')).hexdigest().upper())
