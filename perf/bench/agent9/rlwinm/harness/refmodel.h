// Independent reference model of the 64-bit-mode ISA text (PowerISA 2.07,
// Book I 3.3.14): no compute_mask, no __builtin_rotate*, no rotate_mask.h.
#pragma once
#include <cstdint>

namespace ref {

// MASK(mstart, mstop): bits mstart..mstop set, bit 0 = MSB; wraps if mstart > mstop.
inline uint64_t mask(unsigned mstart, unsigned mstop) {
  uint64_t m = 0;
  for (unsigned i = 0; i < 64; ++i) {
    bool in = mstart <= mstop ? (i >= mstart && i <= mstop) : (i >= mstart || i <= mstop);
    if (in)
      m |= uint64_t{1} << (63 - i);
  }
  return m;
}

inline uint64_t rotl64(uint64_t v, unsigned n) {
  n &= 63;
  return n == 0 ? v : (v << n) | (v >> (64 - n));
}

// ROTL32(x, n) = ROTL64(x[32:63] || x[32:63], n)
inline uint64_t rotl32(uint64_t rs, unsigned n) {
  uint64_t lo = rs & 0xFFFFFFFFull;
  return rotl64((lo << 32) | lo, n);
}

// m = mask(mb + 32, me + 32), precomputed by the caller.
inline uint64_t rlwinm(uint64_t rs, unsigned sh, uint64_t m) { return rotl32(rs, sh) & m; }
inline uint64_t rlwnm(uint64_t rs, uint64_t rb, uint64_t m) { return rotl32(rs, rb & 0x1F) & m; }
inline uint64_t rlwimi(uint64_t ra, uint64_t rs, unsigned sh, uint64_t m) {
  return (rotl32(rs, sh) & m) | (ra & ~m);
}

// CR0 field after a record form (as mfcr shows it, SO = 0): signed compare of the low word.
inline uint32_t cr0(uint64_t result) {
  int32_t v = static_cast<int32_t>(static_cast<uint32_t>(result));
  return v < 0 ? 0x80000000u : v > 0 ? 0x40000000u : 0x20000000u;
}

}  // namespace ref
