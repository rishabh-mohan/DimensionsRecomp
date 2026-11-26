import importlib.util, sys
sys.dont_write_bytecode = True
A2 = r'<workspace>\build\agent2'
sys.path.insert(0, r'<workspace>\DimensionsRecomp\perf\bench\agent7')
spec = importlib.util.spec_from_file_location('n3', A2 + r'\s5\native-fsr1\f2\native3_boot_check.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for p in (A2 + r'\s5\rt-bin\b-fsr1\rt\link-on\rexruntime.dll', A2 + r'\s5\rt-bin\b-toml\rt\link-on\rexruntime.dll',
          A2 + r'\nativefinal2-bin\rexruntime.dll'):
    print(p[len(A2):], m.classify_present_sdk(open(p, 'rb').read()))
