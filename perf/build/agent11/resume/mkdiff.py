# mkdiff.py A B OUT - unified diff (n=0) of two UTF-8 text files, for review (Agent 11, task #25).
import difflib
import sys

a, b, out = sys.argv[1:4]
la = open(a, encoding='utf-8', newline='').read().split('\n')
lb = open(b, encoding='utf-8', newline='').read().split('\n')
d = list(difflib.unified_diff(la, lb, a, b, lineterm='', n=0))
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(d) + '\n')
print('hunks', sum(1 for x in d if x.startswith('@@')), 'minus', sum(1 for x in d if x.startswith('-') and not x.startswith('---')),
      'plus', sum(1 for x in d if x.startswith('+') and not x.startswith('+++')))
