"""Batch-2 edit (i) for task #20 (Agent 7): FPS meter clears touching cells as one rect.

fps_counter.h: add MergeTouchingRects (joins rects that share a full edge; the union is unchanged).
device.cpp:    after the digit loop, merge the cell rects and rebuild the shadows (= cell + 1 px),
               unless LEGO_NATIVE_FPS_CELL_RECTS is set (one clear per cell, the old path).

Usage: python batch2_fps_edit.py [gpu_native dir]   (default: the live tree)
Run after batch2_edits.py. Refuses unless fps_counter.h matches its pre-session hash and every
anchor matches exactly once. CRLF preserved.
"""
import hashlib
import os
import sys

LIVE = r"<workspace>\DimensionsRecomp\rexlego\src\gpu_native"
FPS_H_BEFORE = "79FC841E3180CA0D"


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def replace_once(data, old, new, what):
    n = data.count(old)
    if n != 1:
        sys.exit("%s: expected 1 match, found %d" % (what, n))
    return data.replace(old, new, 1)


def crlf(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


HELPER = crlf("""
// Joins rects that share a whole edge: first along rows (same top and bottom, left meets the
// previous right), then down columns (same left and right, top meets an earlier bottom). Each
// join replaces two rects by their union, which is a rect, so the covered pixels don't change.
// Returns the new count. The FPS meter uses it to clear touching digit cells together.
template <typename Rect>
uint32_t MergeTouchingRects(Rect* rects, uint32_t count) {
  uint32_t rows = 0;
  for (uint32_t i = 0; i < count; ++i) {
    if (rows && rects[rows - 1].top == rects[i].top && rects[rows - 1].bottom == rects[i].bottom &&
        rects[rows - 1].right == rects[i].left)
      rects[rows - 1].right = rects[i].right;
    else
      rects[rows++] = rects[i];
  }
  uint32_t merged = 0;
  for (uint32_t i = 0; i < rows; ++i) {
    uint32_t j = 0;
    while (j < merged && !(rects[j].left == rects[i].left && rects[j].right == rects[i].right &&
                           rects[j].bottom == rects[i].top))
      ++j;
    if (j < merged)
      rects[j].bottom = rects[i].bottom;
    else
      rects[merged++] = rects[i];
  }
  return merged;
}
""")

DEVICE_OLD = crlf("""        x += 12;
        divisor /= 10;
      } while (divisor);
      static const bool batched = std::getenv("LEGO_NATIVE_FPS_OVERLAY_BATCHED") != nullptr;
""")

DEVICE_NEW = crlf("""        x += 12;
        divisor /= 10;
      } while (divisor);
      // Touching cells clear as one rect: the same pixels in each colour, fewer clears.
      // LEGO_NATIVE_FPS_CELL_RECTS=1 keeps one clear per cell.
      static const bool cell_rects = std::getenv("LEGO_NATIVE_FPS_CELL_RECTS") != nullptr;
      if (!cell_rects) {
        used = MergeTouchingRects(pixels.data(), used);
        for (u32 i = 0; i < used; ++i)
          shadows[i] = plume::RenderRect(pixels[i].left + 1, pixels[i].top + 1,
                                         pixels[i].right + 1, pixels[i].bottom + 1);
      }
      static const bool batched = std::getenv("LEGO_NATIVE_FPS_OVERLAY_BATCHED") != nullptr;
""")

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else LIVE
    fh = os.path.join(src, "fps_counter.h")
    dc = os.path.join(src, "device.cpp")
    f = open(fh, "rb").read()
    c = open(dc, "rb").read()
    if not sha(f).startswith(FPS_H_BEFORE):
        sys.exit("%s changed (%s); not editing" % (fh, sha(f)[:16]))
    if b"MergeTouchingRects" in c:
        sys.exit("device.cpp already has MergeTouchingRects; not editing")

    # The helper goes after the class, before the namespace close (one blank line before it).
    end = b"  bool started_ = false;\r\n};\r\n}  // namespace legodimensions::gpu_native"
    new_f = replace_once(f, end, end.replace(b"};\r\n", b"};\r\n" + HELPER, 1), "fps_counter.h end")
    new_c = replace_once(c, DEVICE_OLD, DEVICE_NEW, "device.cpp digit loop end")

    open(fh, "wb").write(new_f)
    open(dc, "wb").write(new_c)
    print("fps_counter.h", sha(f)[:16], "->", sha(new_f)[:16])
    print("device.cpp   ", sha(c)[:16], "->", sha(new_c)[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
