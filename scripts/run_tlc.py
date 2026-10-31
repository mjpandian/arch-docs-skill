#!/usr/bin/env python3
"""Run the TLC model checker on one spec and config, and write a result record.

Usage:
  run_tlc.py SPEC.tla CONFIG.cfg [--results DIR] [--scenario current|proposed]
             [--timeout SECONDS] [--jar PATH] [--download] [--workers N]

Writes, next to each other in --results (default: <spec dir>/results):
  <Spec>_<cfg>.txt   full TLC output, including any counterexample trace
  <Spec>_<cfg>.json  machine-readable record (status, tool version, hashes, counts)

Status values in the record:
  checked      TLC explored every reachable state within the bounds, no violation
  violated     an invariant, deadlock, or liveness property failed (see the trace)
  not-checked  TLC did not finish (parse error, evaluation error, timeout, no tool)

"checked" is a bounded result on a model. It is not a proof about the code.
Exit codes of this script: 0 checked, 1 violated, 2 not-checked.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

JAR_URL = "https://github.com/tlaplus/tlaplus/releases/latest/download/tla2tools.jar"
CACHE_JAR = pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")) / "arch-docs" / "tla2tools.jar"

# TLC exit codes (tlc2.output.EC). Unknown codes are treated as not-checked.
VIOLATIONS = {10: "assumption-violated", 11: "deadlock", 12: "invariant-violation", 13: "liveness-violation"}
ERRORS = {75: "spec-evaluation-error", 76: "invariant-evaluation-error", 77: "liveness-evaluation-error",
          150: "spec-parse-error", 151: "config-parse-error"}


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16]


def find_jar(explicit, allow_download):
    candidates = [explicit, os.environ.get("TLA2TOOLS"), CACHE_JAR]
    for c in candidates:
        if c and pathlib.Path(c).is_file():
            return str(c)
    if allow_download:
        CACHE_JAR.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading TLC to {CACHE_JAR} ...", file=sys.stderr)
        urllib.request.urlretrieve(JAR_URL, CACHE_JAR)  # honours HTTPS_PROXY
        return str(CACHE_JAR)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("config")
    ap.add_argument("--results", help="directory for output (default: <spec dir>/results)")
    ap.add_argument("--scenario", choices=["current", "proposed"], default="current",
                    help="'current' models behaviour found in the code; 'proposed' models a fix that is not implemented")
    ap.add_argument("--timeout", type=int, default=300, help="seconds before giving up (default 300)")
    ap.add_argument("--jar", help="path to tla2tools.jar (else $TLA2TOOLS, else the cache)")
    ap.add_argument("--download", action="store_true", help="download tla2tools.jar if none is found")
    ap.add_argument("--workers", default="auto")
    a = ap.parse_args()

    spec, cfg = pathlib.Path(a.spec).resolve(), pathlib.Path(a.config).resolve()
    for f in (spec, cfg):
        if not f.is_file():
            sys.exit(f"Not found: {f}")
    out_dir = pathlib.Path(a.results).resolve() if a.results else spec.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{spec.stem}_{cfg.stem.replace(spec.stem + '_', '', 1)}"

    record = {
        "spec": spec.stem, "config": cfg.name, "scenario": a.scenario,
        "spec_sha256": sha256(spec), "cfg_sha256": sha256(cfg),
        "status": "not-checked", "reason": None, "exit_code": None,
        "tlc_version": None, "java_version": None,
        "states_generated": None, "distinct_states": None, "depth": None,
        "output": f"{stem}.txt", "run_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    def finish(status, reason=None):
        record["status"], record["reason"] = status, reason
        (out_dir / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n")
        print(f"{stem}: {status}" + (f" ({reason})" if reason else ""))
        sys.exit({"checked": 0, "violated": 1}.get(status, 2))

    if not shutil.which("java"):
        finish("not-checked", "java not found")
    jar = find_jar(a.jar, a.download)
    if not jar:
        finish("not-checked", "tla2tools.jar not found (set TLA2TOOLS, pass --jar, or use --download)")

    try:
        v = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=30)
        line = next((ln for ln in (v.stderr or "").splitlines() if " version " in ln), None)
        record["java_version"] = line.strip() if line else None
    except Exception:
        pass

    meta = tempfile.mkdtemp(prefix="tlc-meta-")
    cmd = ["java", "-XX:+UseParallelGC", "-cp", jar, "tlc2.TLC", "-config", str(cfg),
           "-workers", str(a.workers), "-metadir", meta, "-cleanup", spec.name]
    try:
        p = subprocess.run(cmd, cwd=spec.parent, capture_output=True, text=True, timeout=a.timeout)
        text = p.stdout + (("\n" + p.stderr) if p.stderr.strip() else "")
        code = p.returncode
    except subprocess.TimeoutExpired as e:
        text = (e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""))
        (out_dir / f"{stem}.txt").write_text(text + f"\n[run_tlc] stopped after {a.timeout}s\n")
        shutil.rmtree(meta, ignore_errors=True)
        finish("not-checked", f"timeout after {a.timeout}s: state space too large; reduce constants or bounds")
    finally:
        shutil.rmtree(meta, ignore_errors=True)

    text = "\n".join(ln for ln in text.splitlines() if "JAVA_TOOL_OPTIONS" not in ln) + "\n"
    (out_dir / f"{stem}.txt").write_text(text)
    record["exit_code"] = code

    m = re.search(r"^(TLC2 Version .*)$", text, re.M)
    record["tlc_version"] = m.group(1).strip() if m else None
    m = re.search(r"(\d+) states generated, (\d+) distinct states found", text)
    if m:
        record["states_generated"], record["distinct_states"] = int(m.group(1)), int(m.group(2))
    m = re.search(r"depth of the complete state graph search is (\d+)", text)
    if m:
        record["depth"] = int(m.group(1))
    m = re.search(r"^Error: (Invariant|Temporal property|Deadlock)\b.*$", text, re.M)
    if m:
        record["violation"] = m.group(0).replace("Error: ", "").strip()

    if code == 0 and "No error has been found" in text:
        finish("checked")
    if code in VIOLATIONS:
        finish("violated", VIOLATIONS[code])
    finish("not-checked", ERRORS.get(code, f"tlc-exit-{code}"))


if __name__ == "__main__":
    main()
