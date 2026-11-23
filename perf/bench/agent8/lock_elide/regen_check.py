"""Agent 8: dry run of tools/native-cpu/gen_lock_elide.py against the current generated tree.

Writes the generator output to build/agent8/lock_elide/native_lock_elide.gen.cpp (never to rexlego/src), then
reports, per hooked function, whether the current codegen body matches the digest in the checked-in file, and
lists the direct callees the generator now declares. Exit 0 = every body matches.

usage: python bench/agent8/lock_elide/regen_check.py [checked-in file, default rexlego/src/native_lock_elide.cpp]
"""
import importlib.util, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
GEN_PY = ROOT / 'DimensionsRecomp/tools/native-cpu/gen_lock_elide.py'
OUT = ROOT / 'build/agent8/lock_elide/native_lock_elide.gen.cpp'


def main():
    spec = importlib.util.spec_from_file_location('gen_lock_elide', GEN_PY)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    checked = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else gen.OUT
    old_text = checked.read_text()
    old_digest = dict(re.findall(r'^// (sub_[0-9A-F]+)(?: from \S+)?, body sha256 ([0-9a-f]{16})\.$', old_text, re.M))
    t0 = time.time()
    all_bodies = gen.bodies()
    print('parsed %d global-lock users from %s in %.1f s' % (len(all_bodies), gen.GEN, time.time() - t0))
    same = True
    for f in gen.FUNCS:
        name = 'sub_' + f
        if name not in all_bodies:
            print('%s: MISSING from the codegen output' % name); same = False; continue
        path, body = all_bodies[name]
        why = gen.validate(body)
        digest = gen.hashlib.sha256(body.encode()).hexdigest()[:16]
        match = digest == old_digest.get(name)
        same &= match and why is None
        print('%s: %s now in %s, sha256 %s vs checked-in %s -> %s' % (
            name, 'validates' if why is None else 'REJECTED (%s)' % why, path.name, digest, old_digest.get(name),
            'same body' if match else 'BODY DIFFERS'))
    callees = sorted({c for f in gen.FUNCS if 'sub_' + f in all_bodies
                      for c in gen.RE_CALL.findall(all_bodies['sub_' + f][1])})
    print('%d direct callees: %s' % (len(callees), ' '.join(callees)))
    text = gen.generate(all_bodies)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print('wrote %s; identical to %s: %s' % (OUT, checked, text == old_text))
    return 0 if same else 1


if __name__ == '__main__':
    sys.exit(main())
