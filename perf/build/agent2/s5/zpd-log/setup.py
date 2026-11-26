# Copies the a7e79c0 blob of d3d12/command_processor.cpp to base/ and (once)
# to ov/ as LF, for the zpd-log diag diff. Static only.
import subprocess, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SDK = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "DimensionsRecomp", "rexglue-sdk"))
REL = "src/graphics/d3d12/command_processor.cpp"
blob = subprocess.run(["git", "show", "a7e79c0:" + REL], cwd=SDK, capture_output=True, check=True).stdout
blob = blob.replace(b"\r\n", b"\n")
os.makedirs(os.path.join(HERE, "base"), exist_ok=True)
open(os.path.join(HERE, "base", "command_processor.cpp"), "wb").write(blob)
ov = os.path.join(HERE, "ov", *REL.split("/"))
os.makedirs(os.path.dirname(ov), exist_ok=True)
if not os.path.exists(ov):
    open(ov, "wb").write(blob)
print("base sha256", hashlib.sha256(blob).hexdigest().upper()[:16], "lines", blob.count(b"\n"))
