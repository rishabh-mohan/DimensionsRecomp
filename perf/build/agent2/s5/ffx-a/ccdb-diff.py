import json, os
A2 = r'<workspace>\build\agent2'
fw = lambda p: p.replace('\\', '/')
B = os.path.join(A2, 's5', 'ffx-a', 'b'); REF = os.path.join(A2, 'snap1-sdk')
cc = json.load(open(os.path.join(B, 'compile_commands.json')))
ref = json.load(open(os.path.join(REF, 'compile_commands.json')))
key = lambda e: fw(e['file']) + '|' + (e.get('output') or e['command'].split('CMAKE_INTDIR=')[-1][:12])
rmap = {key(e): e['command'] for e in ref}
n = 0
for e in cc:
    if '-DREX_HAS_FIDELITYFX_SDK=1' in e['command']:
        continue
    a = rmap.get(key(e), '').replace(fw(REF), '@')
    b = e['command'].replace(fw(B), '@')
    if a != b:
        n += 1
        if n <= 4:
            ta, tb = a.split(), b.split()
            print(e['file'], len(ta), len(tb))
            print('  only ref:', [x for x in ta if x not in tb][:6])
            print('  only new:', [x for x in tb if x not in ta][:6])
print('differ', n, 'files:', sorted({os.path.splitext(e['file'])[1] for e in cc if '-DREX_HAS_FIDELITYFX_SDK=1' not in e['command'] and rmap.get(key(e), '').replace(fw(REF), '@') != e['command'].replace(fw(B), '@')}))
