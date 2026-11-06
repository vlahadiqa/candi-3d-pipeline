"""Lab 3 step 5 / A6: reproduce-from-clean transcript.

Copies the project (or git-clones it) into a temp folder, builds a FRESH venv, then runs
  pip install -r requirements.txt  ->  python make_model.py  ->  python tests.py
and saves the real transcript (with exit codes and timings) to out/repro_transcript.txt.

  python repro_clean.py                                   # copy of this folder
  python repro_clean.py --repo https://github.com/<you>/<repo>.git --subdir Module3   # true clone
(`npx serve .` is interactive, so run it yourself and note what you saw.)
"""
from __future__ import annotations

import argparse
import datetime
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time


def run(cmd, cwd, log):
    t0 = time.time()
    log(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = (p.stdout + p.stderr).strip()
    tail = "\n".join(out.splitlines()[-40:])
    log(tail)
    log(f"[exit {p.returncode}  {time.time() - t0:.1f}s]")
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--subdir", default=".")
    a = ap.parse_args()
    here = os.getcwd()
    lines = []

    def log(s):
        print(s); lines.append(s)

    log(f"# clean-repro transcript  {datetime.datetime.now().isoformat(timespec='seconds')}")
    log(f"# host: {platform.platform()}   python {platform.python_version()}")
    tmp = tempfile.mkdtemp(prefix="m3_clean_")
    try:
        if a.repo:
            if run(["git", "clone", "--depth", "1", a.repo, os.path.join(tmp, "repo")], tmp, log) != 0:
                raise SystemExit("clone failed")
            proj = os.path.normpath(os.path.join(tmp, "repo", a.subdir))
        else:
            proj = os.path.join(tmp, "proj")
            shutil.copytree(here, proj, ignore=shutil.ignore_patterns("__pycache__", "out", ".venv", "venv", ".git", "node_modules", "*.pyc"))
            log(f"# copied {here} -> {proj} (excluding out/, __pycache__, venvs, .git)")
        venv = os.path.join(tmp, "venv")
        if run([sys.executable, "-m", "venv", venv], tmp, log) != 0:
            raise SystemExit("venv failed")
        py = os.path.join(venv, "Scripts" if os.name == "nt" else "bin", "python")
        codes = [
            run([py, "-m", "pip", "install", "-r", "requirements.txt"], proj, log),
            run([py, "make_model.py"], proj, log),
            run([py, "tests.py"], proj, log),
        ]
        log("\n# RESULT: " + ("ALL STEPS GREEN" if not any(codes) else f"FAILED (exit codes {codes})"))
    finally:
        os.makedirs(os.path.join(here, "out"), exist_ok=True)
        path = os.path.join(here, "out", "repro_transcript.txt")
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"\nsaved {path}")
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
