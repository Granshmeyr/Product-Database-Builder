#!/usr/bin/python


import os
import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--script", "-s")
    args = parser.parse_args()

    script = args.script

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

    match script:
        case "product_database_builder":
            proc = [
                python_path,
                "product_database_builder.py",
            ]

            subprocess.run(proc)
        case "session_timeout":
            proc = [
                python_path,
                "session_timeout.py",
            ]

            subprocess.run(proc)


if __name__ == "__main__":
    main()
