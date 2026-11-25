import json, os, sys
d = json.load(open(sys.argv[1], encoding='utf-8-sig'))
for k, v in d.items():
    if isinstance(v, dict):
        print(k, '{', ', '.join(list(v.keys())[:40]), '}')
    elif isinstance(v, list):
        print(k, '[', len(v), ']', str(v)[:200])
    else:
        print(k, '=', str(v)[:200])
