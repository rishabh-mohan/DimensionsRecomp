import sys
sys.path.insert(0, r'build\agent10\fe')
import livein as L

T = [
    ('cr6', 'gt', 'cr6.compare(ctx.f1.f64, ctx.f6.f64);', 'W'),
    ('cr6', 'gt', 'if (!cr6.gt) return;', 'R'),
    ('cr6', 'lt', 'cr6.setFromMask(simde_mm_load_ps(ctx.v58.f32), 0xF);', 'W'),
    ('cr6', 'so', 'ctx.r11.u64 = (cr6.lt << 7) | (cr6.gt << 6) | (cr6.eq << 5) | (cr6.so << 4);', 'R'),
    ('cr6', 'eq', 'cr6.compare<uint32_t>(ctx.r9.u32, 0, {});', 'W'),
    ('cr0', 'eq', 'ctx.r4.u64 |= cr0.eq ? 0x20000000 : 0;', 'R'),
    ('cr0', 'so', 'ctx.r4.u64 |= cr0.eq ? 0x20000000 : 0;', None),
    ('ctr', None, 'ctr.u64 = ctx.r0.u64;', 'W'),
    ('ctr', None, 'REX_CALL_INDIRECT_FUNC(ctr.u32);', 'R'),
    ('cr6', 'eq', 'cr6.eq = cr6.lt | cr6.eq;', 'R'),
    ('cr6', 'lt', 'cr6.eq = cr6.gt;', None),
    ('cr6', 'eq', 'cr6.eq = cr6.gt;', 'W'),
    ('cr6', 'so', 'cr6.un = 0;', 'W'),
    ('cr6', 'so', 'if (cr6.un) goto loc_1;', 'R'),
    ('cr6', 'lt', 'cr6.set_raw(ctx.r12.u32 >> 4);', 'W'),
    ('cr6', 'lt', 'ctx.r3.u64 = cr6.raw();', 'R'),
    ('xer', 'ca', 'xer.ca = ctx.r3.u32 > ~ctx.r4.u32;', 'W'),
    ('xer', 'ca', 'ctx.r3.u64 = ctx.r3.u64 + xer.ca;', 'R'),
    ('xer', 'so', 'xer.ca = ctx.r3.u32 > ~ctx.r4.u32;', None),
    ('xer', 'ca', 'xer.ca = (ctx.r3.u64 + xer.ca) < xer.ca;', 'R'),
    ('cr6', 'gt', 'if (cr6.gt) goto loc_82FE7120;', 'R'),
    ('cr6', 'lt', 'ctx.cr6 = cr6;', 'R'),
    ('cr6', 'lt', 'ctx.cr6.lt = 1;', None),
    ('reserved', None, 'reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);', 'W'),
    ('reserved', None, 'cr0.eq = __sync_bool_compare_and_swap(p, reserved.s32, v);', 'R'),
]
bad = 0
for v, f, s, want in T:
    got = L.mk_classifier(v, f)(s)
    ok = got == want
    bad += not ok
    print('%s %s.%s %-75s want %s got %s' % ('ok ' if ok else 'BAD', v, f, s[:75], want, got))
C = [('sub_82A75FD8(ctx, base);', 'sub_82A75FD8'), ('[[clang::musttail]] return sub_82FE6F98(ctx, base);', 'sub_82FE6F98'),
     ('REX_CALL_INDIRECT_FUNC(ctr.u32);', 'REX_CALL_INDIRECT_FUNC'), ('__savegprlr_28(ctx, base);', '__savegprlr_28')]
for s, want in C:
    m = L.CALL.search(s)
    got = (m.group(1) or m.group(2)) if m else None
    bad += got != want
    print('%s CALL %-60s %s' % ('ok ' if got == want else 'BAD', s, got))
print('selftest: %d bad of %d' % (bad, len(T) + len(C)))
