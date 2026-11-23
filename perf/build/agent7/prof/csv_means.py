import csv, sys, statistics as st
cols = ["interval_ms","draw_calls","bindings_ms","begin_ms","pipeline_ms","issue_ms","tail_ms","present_cpu_ms","swap_present_cpu_ms","sync_ms","texture_ms","constants_ms","vertices_ms","detailed_timing_enabled"]
for path in sys.argv[1:]:
    rows = list(csv.DictReader(open(path, newline="")))
    rows = rows[len(rows)*2//5:]
    out = []
    for c in cols:
        vals = [float(r[c]) for r in rows if r.get(c) not in (None, "")]
        if vals: out.append(f"{c}={st.fmean(vals):.3f}")
    print(path.split("\\")[-2], f"rows={len(rows)}", " ".join(out))
