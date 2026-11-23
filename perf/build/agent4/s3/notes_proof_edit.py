"""One-shot edit of perf-notes/agent4-draw-path.md (04:02): the VS-0 proof is complete.

Replaces the 4-line "Proof work done ahead" block in S3.2 and two one-line references.
Every target must occur exactly once. Keeps LF line endings and no BOM; prints SHA256.
"""
import hashlib
import pathlib
import sys

NOTES = pathlib.Path(__file__).resolve().parents[3] / "perf-notes" / "agent4-draw-path.md"

R1_OLD = ("If hash=0 lines remain, suspect address-0 vertex shaders (§S3.2). Then prepare the `|| !vs` "
          "follow-up with a proof that the recorder drops VS-0 draws too, run the step-1 protocol on "
          "scratch copies, and send it to Agents 10 and 1. Don't apply it (Agent 1, 03:35).")
R1_NEW = ("If hash=0 lines remain, suspect address-0 vertex shaders (§S3.2). Then prepare the `|| !vs` "
          "follow-up, run the step-1 protocol on scratch copies, and send it with its proof to Agents 10 "
          "and 1. Don't apply it (Agent 1, 03:35). The proof that the recorder drops VS-0 draws too is "
          "complete (§S3.2, \"Not covered\", 04:02).")

R3_OLD = ("If hash=0 remains: prepare `|| !vs` with its proof (the open items under \"Not covered\"), "
          "but don't apply it (Agent 1, 03:35).")
R3_NEW = ("If hash=0 remains: prepare `|| !vs` and run the step-1 protocol on it. Its proof is complete "
          "(\"Not covered\" above). Don't apply it (Agent 1, 03:35).")

R2_FIRST = "  - Proof work done ahead (read-only, 03:25; batch-2 lines):"
R2_LAST_PREFIX = "    - Still open:"
R2_NEW = """  - Proof, done ahead (read-only, 03:25-04:02). It is complete, so `|| !vs` needs only the step-1 protocol if native3d still logs hash=0. Line numbers here are from the live batch-3 file (`5EA1F357…`):
    - **Only `FindDxil` warns** (shader_archive.cpp:432). GetPipeline's variant lookups use their own tables and never call it: `FindFloatBlendIndicesDxil`/`FindPositionPrecisionDxil` (float_blend_indices.cpp:27-34), `SelectIntegerInputShader` (integer_inputs.cpp:100) and `ResolveInstancedConstantsShader` (instanced_constants.cpp:35). DispatchDraw's uses of the VS hash between its failed-bind drop and the pipeline (2766, 2816, 2839, 2883) don't call it either. So n0's zero count says nothing about VS-0 draws.
    - **Address 0 never has an owner.** `BindShader(stage, 0)` stores the address with a null owner (shaders.cpp:579-581), and the refresh skips address 0 (600). The failed-adopt path (568-569) stores a nonzero address, and the only other writes reset owners (732, 894-895). The N2 capture `CaptureShaderBindings()` copies owners and addresses under one lock (611-612). The N3 capture `CaptureShaderBindings(v, p)` adopts nothing for 0 (620), and it is the only code that writes a snapshot's owners (628, 630). So for a VS-0 draw:
      - `BoundShaderHash` is 0 (813-821), so preparation warns;
      - `binding_failed` is false (685), so the current guard lets the draw through;
      - `ResolveBoundShader(kVertex)` returns null (653-655).
    - **No variant table has a hash-0 entry** in native3d's banks (Agent 2's snap1 tree). Float blend indices and position precision share one table (386 entries); instanced constants have 2,542 entries and integer inputs 7. Their shader caches hold only entries that were found.
    - **No VS-0 key ever gets a pipeline.** Key equality (265-279) and the key hash (287) use `vertex_shader_hash` and `bool(vertex_shader)`, so any equal key is also VS-0. GetPipeline (1696) returns a cached or in-flight pipeline (1700, 1705, 1710, 1713). It posts a compile (1860-1864) or caches a new pipeline (1879) only after its `!vs` check (1737). For a VS-0 key, `vs` (1731-1735) is always null, because every variant lookup misses on hash 0 and `ResolveBoundShader` has no owner. By induction, GetPipeline returns nullptr for every VS-0 key.
    - **The prepared-pipeline path gives the same result.** `PreparedValue::Resolve` (draw_preparation.h:17-24) returns the value cached for an equal key, or calls `prepare()` (GetPipeline, 2888) and caches that. `Reset` stores nullptr. Neither depends on `geometry_ready`.
    - **So the recorder drops every VS-0 draw** at the null pipeline (2891-2900, long-probe event `draw_pipeline_unavailable`). That is before its own geometry lookups (3102-3125), DispatchDraw's only `FindDxil` calls on the VS hash. (GetPipeline reaches `FindDxil` only through `ResolveBoundShader`, shaders.cpp:664, which needs an owner.) Skipping preparation for these draws can't change what is drawn, because `geometry_ready=false` is an ordinary preparation miss that the recorder handles itself. Their warnings stop instead of moving to the recorder.
    - Side effects (a)-(c) above apply to VS-0 draws the same way. In (b), the drop can move from the null pipeline (2891-2900) to the index check (2680). In (c), N3's VS-0 template repeats carry the same address 0."""


def main() -> int:
    raw = NOTES.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw:
        print("FATAL: notes are not LF/no-BOM")
        return 2
    text = raw.decode("utf-8")
    for name, old in (("R1", R1_OLD), ("R3", R3_OLD)):
        if text.count(old) != 1:
            print(f"FATAL: {name} target count {text.count(old)}")
            return 2
    text = text.replace(R1_OLD, R1_NEW).replace(R3_OLD, R3_NEW)
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line == R2_FIRST]
    if len(starts) != 1:
        print(f"FATAL: R2 start count {len(starts)}")
        return 2
    i = starts[0]
    if not lines[i + 3].startswith(R2_LAST_PREFIX) or not lines[i + 1].startswith("    - The hash=0 warning"):
        print("FATAL: R2 block shape changed")
        return 2
    lines[i:i + 4] = R2_NEW.split("\n")
    out = "\n".join(lines).encode("utf-8")
    NOTES.write_bytes(out)
    print(f"OK block at line {i + 1}; {len(out)} B; sha256 {hashlib.sha256(out).hexdigest().upper()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
