import os
import sys
import subprocess

match os.name:
    case "posix":
        if not os.path.isdir("venv"):
            subprocess.run(["./venv.sh"])
    case "nt":
        if not os.path.isdir("venv"):
            subprocess.run(["venv.bat"])

match os.name:
    case "posix":
        python_path = "venv/bin/python"
    case "nt":
        python_path = "venv/Scripts/python.exe"

pd_builder_proc = [
    python_path,
    "product_database_builder.py",
]

if sys.argv[1:] is not None:
    pd_builder_proc.extend(sys.argv[1:])

subprocess.run(pd_builder_proc)
