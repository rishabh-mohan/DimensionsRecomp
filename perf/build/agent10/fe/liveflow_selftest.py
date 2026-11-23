import sys
sys.path.insert(0, r'build\agent10\fe')
import liveflow as F

H = 'DEFINE_REX_FUNC(sub_1) {\n\tREX_FUNC_PROLOGUE();\n'
CASES = [
    ('write, call, read -> S', H + '\tPPCCRRegister cr6{};\n\tcr6.compare<int32_t>(ctx.r3.s32, 0, {});\n'
     '\tsub_2(ctx, base);\n\tif (cr6.eq) goto loc_1;\nloc_1:\n\treturn;\n}', [('S', 'cr6', 'eq')]),
    ('call on a path that jumps away -> clean', H + '\tPPCCRRegister cr6{};\n\tcr6.compare<int32_t>(ctx.r3.s32, 0, {});\n'
     '\tif (cr6.lt) goto loc_2;\n\tsub_2(ctx, base);\n\tgoto loc_3;\nloc_2:\n\tif (cr6.eq) goto loc_3;\nloc_3:\n\treturn;\n}', []),
    ('tail call in a brace block -> clean', H + '\tPPCCRRegister cr6{};\n\tcr6.compare<int32_t>(ctx.r3.s32, 0, {});\n'
     '\tif (!cr6.eq) {\n\t\tsub_2(ctx, base);\n\t\treturn;\n\t}\n\tif (cr6.gt) return;\n\treturn;\n}', []),
    ('non-tail call in a brace block, fallthrough -> S', H + '\tPPCCRRegister cr6{};\n\tcr6.compare<int32_t>(ctx.r3.s32, 0, {});\n'
     '\tif (!cr6.eq) {\n\t\tsub_2(ctx, base);\n\t\tctx.r3.s64 = 0;\n\t}\n\tif (cr6.gt) return;\n\treturn;\n}', [('S', 'cr6', 'gt')]),
    ('read before any write -> U', H + '\tPPCCRRegister cr6{};\n\tif (cr6.lt) return;\n\treturn;\n}', [('U', 'cr6', 'lt')]),
    ('loop: read at the head, write later -> U on entry', H + '\tPPCCRRegister cr6{};\nloc_1:\n\tif (cr6.eq) goto loc_2;\n'
     '\tcr6.compare<int32_t>(ctx.r3.s32, 0, {});\n\tgoto loc_1;\nloc_2:\n\treturn;\n}', [('U', 'cr6', 'eq')]),
    ('ctr loop with a call inside -> S at --ctr', H + '\tPPCRegister ctr{};\n\tctr.u64 = ctx.r9.u64;\nloc_1:\n'
     '\tsub_2(ctx, base);\n\t--ctr.u64;\n\tif (ctr.u32 != 0) goto loc_1;\n\treturn;\n}', [('S', 'ctr', None)]),
    ('helper call (__savegprlr) -> clean', H + '\tPPCCRRegister cr6{};\n\tcr6.compare<int32_t>(ctx.r3.s32, 0, {});\n'
     '\t__savegprlr_28(ctx, base);\n\tif (cr6.eq) return;\n\treturn;\n}', []),
    ('self-update is a read then a write -> U once', H + '\tPPCCRRegister cr6{};\n\tcr6.eq = cr6.lt | cr6.eq;\n'
     '\tif (cr6.eq) return;\n\treturn;\n}', [('U', 'cr6', 'eq'), ('U', 'cr6', 'lt')]),
]
bad = 0
for name, body, want in CASES:
    got = sorted((k, v, f) for k, v, f, i, s, ss in F.analyse(body.split('\n')))
    ok = got == sorted(want, key=lambda t: (t[0], t[1], t[2] or ''))
    bad += not ok
    print('%s %-50s want %s got %s' % ('ok ' if ok else 'BAD', name, want, got))
print('liveflow selftest: %d bad of %d' % (bad, len(CASES)))
