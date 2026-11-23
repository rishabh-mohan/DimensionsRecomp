# Generated functions of instr_cr_so_fold (default, opt, crso)

## default

default instr_cr_so_fold_82010000:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010000) {
	REX_FUNC_PROLOGUE();
	// lis r11,-32768
	ctx.r11.s64 = -2147483648;
	// mtxer r11
	ctx.xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	ctx.xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	ctx.xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// cmpw cr1,r4,r5
	ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
	// cmpwi cr6,r4,5
	ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
	// mfcr r3
	ctx.r3.u64 = ctx.cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= ctx.cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= ctx.cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= ctx.cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= ctx.cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= ctx.cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= ctx.cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= ctx.cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= ctx.cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= ctx.cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= ctx.cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= ctx.cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= ctx.cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= ctx.cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= ctx.cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= ctx.cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= ctx.cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= ctx.cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= ctx.cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= ctx.cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= ctx.cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= ctx.cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= ctx.cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= ctx.cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= ctx.cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= ctx.cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= ctx.cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= ctx.cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= ctx.cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= ctx.cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= ctx.cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= ctx.cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
default instr_cr_so_fold_8201001C:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_8201001C) {
	REX_FUNC_PROLOGUE();
	// mflr r12
	ctx.r12.u64 = ctx.lr;
	// lis r11,-32768
	ctx.r11.s64 = -2147483648;
	// mtxer r11
	ctx.xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	ctx.xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	ctx.xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// bl 0x82010050
	ctx.lr = 0x8201002C;
	instr_cr_so_fold_82010050(ctx, base);
	// mtlr r12
	ctx.lr = ctx.r12.u64;
	// blr 
	return;
}
```
default instr_cr_so_fold_82010034:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010034) {
	REX_FUNC_PROLOGUE();
	// li r11,0
	ctx.r11.s64 = 0;
	// mtxer r11
	ctx.xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	ctx.xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	ctx.xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// cmpw cr1,r4,r5
	ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
	// cmpwi cr6,r4,5
	ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
	// mfcr r3
	ctx.r3.u64 = ctx.cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= ctx.cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= ctx.cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= ctx.cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= ctx.cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= ctx.cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= ctx.cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= ctx.cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= ctx.cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= ctx.cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= ctx.cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= ctx.cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= ctx.cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= ctx.cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= ctx.cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= ctx.cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= ctx.cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= ctx.cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= ctx.cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= ctx.cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= ctx.cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= ctx.cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= ctx.cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= ctx.cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= ctx.cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= ctx.cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= ctx.cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= ctx.cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= ctx.cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= ctx.cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= ctx.cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= ctx.cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
default instr_cr_so_fold_82010050:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010050) {
	REX_FUNC_PROLOGUE();
	// cmpw cr1,r4,r5
	ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
	// cmpwi cr6,r4,5
	ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
	// mfcr r3
	ctx.r3.u64 = ctx.cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= ctx.cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= ctx.cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= ctx.cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= ctx.cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= ctx.cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= ctx.cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= ctx.cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= ctx.cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= ctx.cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= ctx.cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= ctx.cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= ctx.cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= ctx.cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= ctx.cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= ctx.cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= ctx.cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= ctx.cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= ctx.cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= ctx.cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= ctx.cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= ctx.cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= ctx.cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= ctx.cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= ctx.cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= ctx.cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= ctx.cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= ctx.cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= ctx.cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= ctx.cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= ctx.cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= ctx.cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
## opt

opt instr_cr_so_fold_82010000:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010000) {
	REX_FUNC_PROLOGUE();
	PPCXERRegister xer{};
	PPCCRRegister cr0{};
	PPCCRRegister cr1{};
	PPCCRRegister cr2{};
	PPCCRRegister cr3{};
	PPCCRRegister cr4{};
	PPCCRRegister cr5{};
	PPCCRRegister cr6{};
	PPCCRRegister cr7{};
	// lis r11,-32768
	ctx.r11.s64 = -2147483648;
	// mtxer r11
	xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// cmpw cr1,r4,r5
	cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, xer);
	// cmpwi cr6,r4,5
	cr6.compare<int32_t>(ctx.r4.s32, 5, xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	cr0.compare<int32_t>(ctx.r6.s32, 0, xer);
	// mfcr r3
	ctx.r3.u64 = cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
opt instr_cr_so_fold_8201001C:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_8201001C) {
	REX_FUNC_PROLOGUE();
	PPCXERRegister xer{};
	// mflr r12
	// lis r11,-32768
	ctx.r11.s64 = -2147483648;
	// mtxer r11
	xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// bl 0x82010050
	instr_cr_so_fold_82010050(ctx, base);
	// mtlr r12
	// blr 
	return;
}
```
opt instr_cr_so_fold_82010034:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010034) {
	REX_FUNC_PROLOGUE();
	PPCXERRegister xer{};
	PPCCRRegister cr0{};
	PPCCRRegister cr1{};
	PPCCRRegister cr2{};
	PPCCRRegister cr3{};
	PPCCRRegister cr4{};
	PPCCRRegister cr5{};
	PPCCRRegister cr6{};
	PPCCRRegister cr7{};
	// li r11,0
	ctx.r11.s64 = 0;
	// mtxer r11
	xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// cmpw cr1,r4,r5
	cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, xer);
	// cmpwi cr6,r4,5
	cr6.compare<int32_t>(ctx.r4.s32, 5, xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	cr0.compare<int32_t>(ctx.r6.s32, 0, xer);
	// mfcr r3
	ctx.r3.u64 = cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
opt instr_cr_so_fold_82010050:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010050) {
	REX_FUNC_PROLOGUE();
	PPCCRRegister cr0{};
	PPCCRRegister cr1{};
	PPCCRRegister cr2{};
	PPCCRRegister cr3{};
	PPCCRRegister cr4{};
	PPCCRRegister cr5{};
	PPCCRRegister cr6{};
	PPCCRRegister cr7{};
	// cmpw cr1,r4,r5
	cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, {});
	// cmpwi cr6,r4,5
	cr6.compare<int32_t>(ctx.r4.s32, 5, {});
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	cr0.compare<int32_t>(ctx.r6.s32, 0, {});
	// mfcr r3
	ctx.r3.u64 = cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
## crso

crso instr_cr_so_fold_82010000:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010000) {
	REX_FUNC_PROLOGUE();
	// lis r11,-32768
	ctx.r11.s64 = -2147483648;
	// mtxer r11
	ctx.xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	ctx.xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	ctx.xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// cmpw cr1,r4,r5
	ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
	// cmpwi cr6,r4,5
	ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
	// mfcr r3
	ctx.r3.u64 = ctx.cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= ctx.cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= ctx.cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= ctx.cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= ctx.cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= ctx.cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= ctx.cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= ctx.cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= ctx.cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= ctx.cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= ctx.cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= ctx.cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= ctx.cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= ctx.cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= ctx.cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= ctx.cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= ctx.cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= ctx.cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= ctx.cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= ctx.cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= ctx.cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= ctx.cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= ctx.cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= ctx.cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= ctx.cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= ctx.cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= ctx.cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= ctx.cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= ctx.cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= ctx.cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= ctx.cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= ctx.cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
crso instr_cr_so_fold_8201001C:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_8201001C) {
	REX_FUNC_PROLOGUE();
	// mflr r12
	ctx.r12.u64 = ctx.lr;
	// lis r11,-32768
	ctx.r11.s64 = -2147483648;
	// mtxer r11
	ctx.xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	ctx.xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	ctx.xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// bl 0x82010050
	ctx.lr = 0x8201002C;
	instr_cr_so_fold_82010050(ctx, base);
	// mtlr r12
	ctx.lr = ctx.r12.u64;
	// blr 
	return;
}
```
crso instr_cr_so_fold_82010034:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010034) {
	REX_FUNC_PROLOGUE();
	// li r11,0
	ctx.r11.s64 = 0;
	// mtxer r11
	ctx.xer.so = (ctx.r11.u64 & 0x80000000) != 0;
	ctx.xer.ov = (ctx.r11.u64 & 0x40000000) != 0;
	ctx.xer.ca = (ctx.r11.u64 & 0x20000000) != 0;
	// cmpw cr1,r4,r5
	ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
	// cmpwi cr6,r4,5
	ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
	// mfcr r3
	ctx.r3.u64 = ctx.cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= ctx.cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= ctx.cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= ctx.cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= ctx.cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= ctx.cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= ctx.cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= ctx.cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= ctx.cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= ctx.cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= ctx.cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= ctx.cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= ctx.cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= ctx.cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= ctx.cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= ctx.cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= ctx.cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= ctx.cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= ctx.cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= ctx.cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= ctx.cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= ctx.cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= ctx.cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= ctx.cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= ctx.cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= ctx.cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= ctx.cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= ctx.cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= ctx.cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= ctx.cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= ctx.cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= ctx.cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
crso instr_cr_so_fold_82010050:
```cpp
DEFINE_REX_FUNC(instr_cr_so_fold_82010050) {
	REX_FUNC_PROLOGUE();
	// cmpw cr1,r4,r5
	ctx.cr1.compare<int32_t>(ctx.r4.s32, ctx.r5.s32, ctx.xer);
	// cmpwi cr6,r4,5
	ctx.cr6.compare<int32_t>(ctx.r4.s32, 5, ctx.xer);
	// andi. r6,r4,4
	ctx.r6.u64 = ctx.r4.u64 & 4;
	ctx.cr0.compare<int32_t>(ctx.r6.s32, 0, ctx.xer);
	// mfcr r3
	ctx.r3.u64 = ctx.cr0.lt ? 0x80000000 : 0;
	ctx.r3.u64 |= ctx.cr0.gt ? 0x40000000 : 0;
	ctx.r3.u64 |= ctx.cr0.eq ? 0x20000000 : 0;
	ctx.r3.u64 |= ctx.cr0.so ? 0x10000000 : 0;
	ctx.r3.u64 |= ctx.cr1.lt ? 0x8000000 : 0;
	ctx.r3.u64 |= ctx.cr1.gt ? 0x4000000 : 0;
	ctx.r3.u64 |= ctx.cr1.eq ? 0x2000000 : 0;
	ctx.r3.u64 |= ctx.cr1.so ? 0x1000000 : 0;
	ctx.r3.u64 |= ctx.cr2.lt ? 0x800000 : 0;
	ctx.r3.u64 |= ctx.cr2.gt ? 0x400000 : 0;
	ctx.r3.u64 |= ctx.cr2.eq ? 0x200000 : 0;
	ctx.r3.u64 |= ctx.cr2.so ? 0x100000 : 0;
	ctx.r3.u64 |= ctx.cr3.lt ? 0x80000 : 0;
	ctx.r3.u64 |= ctx.cr3.gt ? 0x40000 : 0;
	ctx.r3.u64 |= ctx.cr3.eq ? 0x20000 : 0;
	ctx.r3.u64 |= ctx.cr3.so ? 0x10000 : 0;
	ctx.r3.u64 |= ctx.cr4.lt ? 0x8000 : 0;
	ctx.r3.u64 |= ctx.cr4.gt ? 0x4000 : 0;
	ctx.r3.u64 |= ctx.cr4.eq ? 0x2000 : 0;
	ctx.r3.u64 |= ctx.cr4.so ? 0x1000 : 0;
	ctx.r3.u64 |= ctx.cr5.lt ? 0x800 : 0;
	ctx.r3.u64 |= ctx.cr5.gt ? 0x400 : 0;
	ctx.r3.u64 |= ctx.cr5.eq ? 0x200 : 0;
	ctx.r3.u64 |= ctx.cr5.so ? 0x100 : 0;
	ctx.r3.u64 |= ctx.cr6.lt ? 0x80 : 0;
	ctx.r3.u64 |= ctx.cr6.gt ? 0x40 : 0;
	ctx.r3.u64 |= ctx.cr6.eq ? 0x20 : 0;
	ctx.r3.u64 |= ctx.cr6.so ? 0x10 : 0;
	ctx.r3.u64 |= ctx.cr7.lt ? 0x8 : 0;
	ctx.r3.u64 |= ctx.cr7.gt ? 0x4 : 0;
	ctx.r3.u64 |= ctx.cr7.eq ? 0x2 : 0;
	ctx.r3.u64 |= ctx.cr7.so ? 0x1 : 0;
	// blr 
	return;
}
```
