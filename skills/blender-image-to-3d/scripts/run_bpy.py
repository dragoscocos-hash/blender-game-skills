#!/usr/bin/env python3
"""Run a skill script with the `bpy` Python module instead of a Blender binary.

Use on headless machines where Blender is not installed as an app (cloud containers):
    python3 -m pip install bpy          # wheel matches one Python version; check PyPI
    python3 scripts/run_bpy.py scripts/validate.py --blend X.blend --budget-tris 4000

Everything after the script path is passed as if it followed `--` on a blender command line,
so the scripts' own argument parsing works unchanged. Workbench needs a GPU context that the
module may not have; pass --engine cycles to review_render.py when it fails.
"""
import os
import runpy
import sys

if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    print(__doc__)
    sys.exit(0)

script = os.path.abspath(sys.argv[1])
rest = sys.argv[2:]
sys.argv = ["blender", "--background", "--python", script, "--"] + rest
sys.path.insert(0, os.path.dirname(script))
try:
    import bpy  # noqa: F401
except ImportError:
    sys.exit("bpy module not installed: python3 -m pip install bpy (or set BLENDER_BIN and use the binary)")
runpy.run_path(script, run_name="__main__")
