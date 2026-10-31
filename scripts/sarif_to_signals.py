#!/usr/bin/env python3
"""Turn SARIF output from any static analyzer into per-file issue signals.

Usage:
  sarif_to_signals.py RESULTS.sarif [MORE.sarif ...] [--repo NAME] [--root DIR]
                      [--out docs/signals.json] [--issues docs/issues.json] [--merge]

Many scanners can emit SARIF 2.1.0 (Semgrep, CodeQL, Trivy, ESLint and Bandit through formatters,
and others). This script reads them all and writes:
  signals.json  {"repo::path": {"issues": N, "issues_high": N}} for hotspots.py --signals
  issues.json   one record per finding: tool, rule, severity, path, line
                (never the message text or code snippet, so secrets are not copied)

--merge keeps other fields already in --out (for example fan_in from the code graph) and only
replaces the issue counts, so rerunning with the same inputs gives the same result.
--root makes absolute file paths relative to a repository checkout.

Severity: SARIF "error" is high, "warning" is medium, "note" and "none" are low.
A numeric security-severity (CVSS-like) on the result or its rule overrides: >= 7 high, >= 4 medium.
A rule-level score therefore applies to every result of that rule.
"""
import argparse
import json
import os
import pathlib
import re
import sys
import urllib.parse

SECRET_RULE = re.compile(r"secret|credential|password|passwd|token|api[-_]?key|private[-_]?key", re.I)


def severity(level, score):
    try:
        if score is not None:
            v = float(score)
            return "high" if v >= 7 else "medium" if v >= 4 else "low"
    except (TypeError, ValueError):
        pass
    return {"error": "high", "warning": "medium"}.get(level, "low")


def norm_path(uri, root):
    u = urllib.parse.unquote(uri)
    if u.startswith("file://"):
        u = u[len("file://"):]
    if re.match(r"^/[a-zA-Z]:", u):
        u = u[1:]
    u = u.replace("\\", "/")
    if root:
        r_norm = str(root).replace("\\", "/").rstrip("/") + "/"
        if re.match(r"^/[a-zA-Z]:", r_norm):
            r_norm = r_norm[1:]
        if u.lower().startswith(r_norm.lower()):
            u = u[len(r_norm):]
        else:
            r_res = str(pathlib.Path(root).resolve()).replace("\\", "/").rstrip("/") + "/"
            if re.match(r"^/[a-zA-Z]:", r_res):
                r_res = r_res[1:]
            if u.lower().startswith(r_res.lower()):
                u = u[len(r_res):]
    while u.startswith("./") or u.startswith("/"):
        u = u.lstrip("./").lstrip("/")
    return u


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sarif", nargs="+")
    ap.add_argument("--repo")
    ap.add_argument("--root")
    ap.add_argument("--out", default="docs/signals.json")
    ap.add_argument("--issues", default="docs/issues.json")
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()

    issues, skipped = [], 0
    for f in a.sarif:
        try:
            doc = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(f"Cannot read {f}: {e}")
        for run in doc.get("runs", []):
            driver = run.get("tool", {}).get("driver", {})
            tool = driver.get("name", "unknown")
            rules = {r.get("id"): r for r in driver.get("rules", []) if isinstance(r, dict)}
            for res in run.get("results", []):
                locs = res.get("locations") or []
                art = (locs[0].get("physicalLocation", {}) if locs else {})
                uri = art.get("artifactLocation", {}).get("uri")
                if not uri:
                    skipped += 1
                    continue
                rule_id = res.get("ruleId") or "unknown"
                rule = rules.get(rule_id, {})
                level = res.get("level") or rule.get("defaultConfiguration", {}).get("level") or "warning"
                score = (res.get("properties", {}) or {}).get("security-severity") \
                    or (rule.get("properties", {}) or {}).get("security-severity")
                rec = {"tool": tool, "rule": rule_id, "severity": severity(level, score),
                       "path": norm_path(uri, a.root), "line": art.get("region", {}).get("startLine")}
                if SECRET_RULE.search(rule_id):
                    rec["secret"] = True        # report the location only; never the value
                issues.append(rec)

    counts = {}
    for i in issues:
        key = f"{a.repo}::{i['path']}" if a.repo else i["path"]
        c = counts.setdefault(key, {"issues": 0, "issues_high": 0})
        c["issues"] += 1
        c["issues_high"] += i["severity"] == "high"

    out = pathlib.Path(a.out)
    signals = {}
    if a.merge and out.is_file():
        signals = json.loads(out.read_text())
    for key, c in counts.items():
        signals.setdefault(key, {}).update(c)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(signals, indent=2, sort_keys=True) + "\n")
    pathlib.Path(a.issues).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.issues).write_text(json.dumps(issues, indent=2) + "\n")

    by_sev = {s: sum(i["severity"] == s for i in issues) for s in ("high", "medium", "low")}
    print(f"{len(issues)} findings in {len(counts)} files ({by_sev['high']} high, {by_sev['medium']} medium, "
          f"{by_sev['low']} low); {skipped} without a file location skipped. Wrote {a.out} and {a.issues}")
    if any(i.get("secret") for i in issues):
        print("note: secret-related rules fired. Report their locations only; never copy values.", file=sys.stderr)


if __name__ == "__main__":
    main()
