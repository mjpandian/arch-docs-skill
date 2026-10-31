#!/usr/bin/env python3
"""Rank code hotspots from git history, with optional extra signals.

Usage:
  hotspots.py REPO [REPO ...] [--out DIR] [--since "12 months ago"] [--signals FILE.json]
              [--top N] [--embed-top N] [--min-commits N] [--max-files-per-commit N]
              [--threshold 0.8] [--min-shared N] [--bugfix-regex RE] [--ticket-regex RE]
              [--exclude GLOB ...] [--include-docs] [--include-tests] [--code-only]

Writes DIR/hotspots.json, DIR/hotspots.md and DIR/hotspots.embed.js (default DIR: docs).

Stacks (Python, Node/TypeScript, .NET, Java/Kotlin, Go, Ruby, PHP, Rust, Terraform, YAML/Config and others)
are detected per repo from build files and extensions. Stack-specific generated and test paths
are excluded only when the stack is present. Config files (YAML, JSON, TOML, XML, Terraform,
Dockerfiles, protobuf and similar) are ranked among themselves, with size in lines standing
in for complexity, because indentation says little about config. Use --code-only to leave them out.

Signals per file (all from git history unless noted):
  churn       commits touching the file in the window
  complexity  indentation-based proxy (sum of indent levels), or a supplied value
  bugfix      commits whose subject matches the bug-fix regex (a heuristic)
  coupling    count of strong co-change partners (files that change together)
  owner       single-owner concentration, stronger if that owner is no longer active
  fan_in, issues, runtime   supplied through --signals (see below)

A file is a "hotspot" when churn AND complexity are both high, or when three or more
signals are high. It is "watch" when two are. Scores rank files; they are heuristics,
not defect findings. Authors are never named: only counts and shares are reported.

--signals FILE.json maps "repo::path" (or a bare "path") to any of:
  {"fan_in": N, "fan_out": N, "complexity": N, "issues": N, "issues_high": N, "runtime": 0..1}
"""
import argparse
import collections
import datetime
import fnmatch
import itertools
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import time

DEFAULT_EXCLUDES = [
    "node_modules/*", "*/node_modules/*", "vendor/*", "*/vendor/*", "dist/*", "*/dist/*",
    "build/*", "*/build/*", "target/*", "*/target/*", ".git/*",
    "*.min.js", "*.min.css", "*.map", "*.lock", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "go.sum", "poetry.lock", "Cargo.lock", "Gemfile.lock",
    "*.snap", "*.svg", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.pdf",
    "*.woff", "*.woff2", "*.ttf", "*.zip", "*.gz", "*.jar",
    "*_pb2.py", "*_pb2_grpc.py", "*.pb.go", "*.generated.*", "*/generated/*", "*/__generated__/*",
    "*.Designer.cs", "*.g.cs", "*.g.i.cs", "*.AssemblyInfo.cs", "*.generated.cs",
    "*.g.ts", "*.tsbuildinfo", "*.class", "*.pyc", "*.dll", "*.pdb", "*.iml",
    "*.tfstate", "*.tfstate.backup", ".terraform.lock.hcl", "*.tgz",
    "packages.lock.json", "*.csproj.user", "gradle/wrapper/*", "*/generated-sources/*",
    ".idea/*", "*/.idea/*", ".vscode/*", "*/.vscode/*", ".DS_Store", "*/.DS_Store",
    "bin/*", "*/bin/*", "obj/*", "*/obj/*"
]
DOC_EXCLUDES = ["*.md", "*.rst", "*.txt"]
TEST_EXCLUDES = ["tests/*", "*/tests/*", "test/*", "*/test/*", "__tests__/*", "*/__tests__/*", "test_*.py", "*/test_*.py",
                 "*_test.py", "*_test.go", "*/*_test.go", "*.test.js", "*.test.ts", "*.test.tsx", "*.spec.js", "*.spec.ts",
                 "*Test.java", "*Tests.java", "*Test.kt", "*Tests.cs", "conftest.py", "*/conftest.py"]
WEIGHTS = {"core": 0.30, "bugfix": 0.15, "coupling": 0.10, "fan_in": 0.10,
           "issues": 0.15, "runtime": 0.10, "owner": 0.10}
HIT_SIGNALS = ["churn", "complexity", "bugfix", "coupling", "fan_in", "issues", "runtime"]
NOT_TICKETS = {"UTF", "SHA", "ISO", "MD", "CVE", "RFC", "TLS", "SSL", "HTTP", "AES", "RSA", "X", "V"}

STACK_MARKERS = {
    "python": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "poetry.lock"],
    "typescript": ["package.json", "tsconfig.json", "jsconfig.json"],
    "csharp": ["*.sln", "*.csproj", "*.fsproj", "*.vbproj", "Directory.Build.props", "web.config", "packages.config", "App.config", "host.json", "local.settings.json"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
    "go": ["go.mod", "go.sum"],
    "ruby": ["Gemfile", "*.gemspec"],
    "php": ["composer.json"],
    "rust": ["Cargo.toml"],
    "terraform": ["*.tf", "*.tfvars", ".terraform.lock.hcl"],
    "yaml": ["*.yaml", "*.yml", "kustomization.yaml", "Chart.yaml"],
}

STACK_EXCLUDES = {
    "python": ["*.pyc", "__pycache__/*", "*/__pycache__/*", ".pytest_cache/*", "*/.pytest_cache/*", ".venv/*", "*/.venv/*", ".mypy_cache/*", "*/.mypy_cache/*", ".tox/*", "*/.tox/*"],
    "typescript": ["node_modules/*", "*/node_modules/*", "dist/*", "*/dist/*", ".next/*", "*/.next/*", ".nuxt/*", "*/.nuxt/*", "*.tsbuildinfo", ".yarn/*", "*/.yarn/*"],
    "csharp": ["bin/*", "*/bin/*", "obj/*", "*/obj/*", "*.Designer.cs", "*.g.cs", "*.g.i.cs", "*.AssemblyInfo.cs", "*.generated.cs", "packages/*", "*/packages/*", "*.csproj.user", "App_Data/*", "*/App_Data/*", ".vs/*", "*/.vs/*"],
    "java": ["target/*", "*/target/*", "build/*", "*/build/*", ".gradle/*", "*/.gradle/*", "*.class", "*.jar", "*.war", "gradle/wrapper/*", "*/generated-sources/*"],
    "go": ["vendor/*", "*/vendor/*", "*.pb.go"],
    "ruby": [".bundle/*", "*/.bundle/*", "vendor/bundle/*"],
    "php": ["vendor/*", "*/vendor/*"],
    "rust": ["target/*", "*/target/*"],
    "terraform": [".terraform/*", "*/.terraform/*", "*.tfstate", "*.tfstate.*"],
}

STACK_TEST_EXCLUDES = {
    "python": ["tests/*", "*/tests/*", "test/*", "*/test/*", "test_*.py", "*/test_*.py", "*_test.py", "*/conftest.py", "conftest.py"],
    "typescript": ["__tests__/*", "*/__tests__/*", "*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx", "*.test.js", "*.spec.js", "tests/*", "*/tests/*"],
    "csharp": ["*Test.cs", "*Tests.cs", "*UnitTest.cs", "tests/*", "*/tests/*", "test/*", "*/test/*", "*.Tests/*", "*/[Tt]ests/*"],
    "java": ["*Test.java", "*Tests.java", "*TestCase.java", "*Test.kt", "*Tests.kt", "src/test/*", "*/src/test/*"],
    "go": ["*_test.go", "*/*_test.go"],
    "ruby": ["spec/*", "*/spec/*", "*_spec.rb", "test/*", "*/test/*"],
    "php": ["*Test.php", "tests/*", "*/tests/*"],
    "rust": ["tests/*", "*/tests/*"],
}

BUILD_MARKERS = [
    "*.csproj", "*.fsproj", "pom.xml", "build.gradle", "build.gradle.kts",
    "package.json", "pyproject.toml", "setup.py", "go.mod", "Cargo.toml", "composer.json"
]

EXT_LANG = {
    ".py": "python", ".pyi": "python",
    ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".cs": "csharp",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".rs": "rust",
    ".yaml": "yaml", ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".tf": "terraform", ".tfvars": "terraform", ".hcl": "terraform",
    ".proto": "protobuf",
    ".sql": "sql",
    ".sh": "shell", ".bash": "shell",
    ".ps1": "powershell",
    ".md": "markdown",
}

CONFIG_EXTS = {".yaml", ".yml", ".json", ".toml", ".xml", ".tf", ".tfvars", ".hcl", ".proto", ".ini", ".cfg", ".conf", ".properties"}
CONFIG_NAMES = {"dockerfile", "containerfile", "vagrantfile", "makefile", "gemfile", "procfile", "caddyfile"}


def lang_and_kind(p):
    path_obj = pathlib.PurePosixPath(p)
    name_lower = path_obj.name.lower()
    ext = path_obj.suffix.lower()
    if name_lower in CONFIG_NAMES or "dockerfile" in name_lower:
        return "docker" if "dockerfile" in name_lower else "config", "config"
    lang = EXT_LANG.get(ext, "other")
    kind = "config" if ext in CONFIG_EXTS else "code"
    return lang, kind


def detect_stacks(repo_path, all_files):
    detected = set()
    for stack, markers in STACK_MARKERS.items():
        for m in markers:
            if any(fnmatch.fnmatch(f, m) or fnmatch.fnmatch(f, f"*/{m}") for f in all_files):
                detected.add(stack)
                break
    for f in all_files:
        ext = pathlib.PurePosixPath(f).suffix.lower()
        if ext in (".py",): detected.add("python")
        elif ext in (".ts", ".tsx", ".js", ".jsx"): detected.add("typescript")
        elif ext in (".cs",): detected.add("csharp")
        elif ext in (".java", ".kt"): detected.add("java")
        elif ext in (".go",): detected.add("go")
        elif ext in (".rb",): detected.add("ruby")
        elif ext in (".php",): detected.add("php")
        elif ext in (".rs",): detected.add("rust")
        elif ext in (".tf", ".tfvars"): detected.add("terraform")
        elif ext in (".yaml", ".yml"): detected.add("yaml")
    return sorted(detected)


def find_modules(all_files):
    """Find directories containing build markers."""
    marker_dirs = set()
    for f in all_files:
        p = pathlib.PurePosixPath(f)
        for m in BUILD_MARKERS:
            if fnmatch.fnmatch(p.name, m):
                marker_dirs.add(str(p.parent) if str(p.parent) != "." else "")
                break
    return marker_dirs


def module_for(p, marker_dirs):
    """Return the nearest ancestor directory that is a build marker dir, else fallback."""
    parts = p.split("/")[:-1]
    for d in range(len(parts), 0, -1):
        cand = "/".join(parts[:d])
        if cand in marker_dirs:
            return cand
    if "" in marker_dirs and len(parts) >= 1:
        if parts[0] in SOURCE_ROOTS and len(parts) >= 2:
            return "/".join(parts[:2])
        return parts[0]
    return module_of(p)


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=false", *args],
                       capture_output=True, text=True, errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} failed in {repo}: {p.stderr.strip()[:200]}")
    return p.stdout


def read_history(repo, since, max_files, excluded):
    """Return (commits, skipped_large). Merge commits and binary files are ignored."""
    fmt = "%x1e%H%x1f%ae%x1f%at%x1f%s"
    out = git(repo, "log", "--no-merges", "--no-renames", "--numstat", f"--since={since}", f"--format={fmt}")
    commits, skipped = [], 0
    for rec in out.split("\x1e"):
        if not rec.strip():
            continue
        head, _, body = rec.partition("\n")
        f = head.split("\x1f")
        if len(f) < 4:
            continue
        files = []
        for line in body.splitlines():
            t = line.split("\t")
            if len(t) != 3 or not t[0].isdigit() or excluded(t[2]):
                continue
            files.append((t[2], int(t[0]), int(t[1])))
        if not files:
            continue
        if len(files) > max_files:      # mass reformat, rename, or import: distorts churn and coupling
            skipped += 1
            continue
        commits.append({"author": f[1], "ts": int(f[2]), "subject": "\x1f".join(f[3:]), "files": files})
    return commits, skipped


def read_blobs(repo, paths):
    paths = [p for p in paths if "\n" not in p]
    req = b"".join(f"HEAD:{p}\n".encode() for p in paths)
    data = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], input=req, capture_output=True).stdout
    out, pos = {}, 0
    for path in paths:
        nl = data.find(b"\n", pos)
        if nl < 0:
            break
        parts = data[pos:nl].decode(errors="replace").split()
        pos = nl + 1
        if len(parts) == 3 and parts[1] == "blob":
            size = int(parts[2])
            out[path] = data[pos:pos + size]
            pos += size + 1
    return out


def measure(blob):
    """Return (loc, complexity) for a text blob, or None for binary. Complexity is the sum of
    indent levels over non-blank lines: a language-neutral proxy for nesting depth."""
    if b"\0" in blob[:8000]:
        return None
    widths = []
    for ln in blob.decode("utf-8", errors="replace").splitlines():
        s = ln.lstrip(" \t")
        if s:
            widths.append(len(ln[:len(ln) - len(s)].expandtabs(4)))
    if not widths:
        return 0, 0
    pos = collections.Counter(w for w in widths if w > 0)
    total = sum(pos.values())
    common = [w for w, n in pos.items() if n >= max(2, 0.05 * total)]
    unit = min(common) if common else (min(pos) if pos else 1)
    unit = max(2, min(unit, 8))
    return len(widths), sum(w // unit for w in widths)


def percentiles(values):
    """Average-rank percentile in [0, 1]. A signal that is zero everywhere stays zero."""
    n = len(values)
    if n == 0 or max(values) == 0:
        return [0.0] * n
    if n == 1:
        return [1.0]
    order = sorted(range(n), key=lambda i: values[i])
    pct, i = [0.0] * n, 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            pct[order[k]] = ((i + j) / 2) / (n - 1)
        i = j + 1
    return pct


SOURCE_ROOTS = {"src", "lib", "app", "apps", "packages", "pkg", "internal", "cmd", "services", "modules", "source", "main"}


def module_of(p):
    """Module a file belongs to: its first directory, or the first two inside a common source root."""
    dirs = p.split("/")[:-1]
    if not dirs:
        return ""
    return "/".join(dirs[:2]) if dirs[0] in SOURCE_ROOTS and len(dirs) >= 2 else dirs[0]


def analyze_repo(name, path, a, bug_re, signals):
    warnings = []
    if git(path, "rev-parse", "--is-shallow-repository").strip() == "true":
        warnings.append("Shallow clone: history is truncated, so churn and ownership are understated. Fetch full history.")
    head = git(path, "rev-parse", "--short", "HEAD").strip()
    all_files = git(path, "ls-files").splitlines()
    stacks = detect_stacks(path, all_files)
    marker_dirs = find_modules(all_files)

    repo_pats = list(DEFAULT_EXCLUDES) + a.exclude
    if not a.include_docs:
        repo_pats += DOC_EXCLUDES
    for s in stacks:
        if s in STACK_EXCLUDES:
            repo_pats += STACK_EXCLUDES[s]
        if not a.include_tests and s in STACK_TEST_EXCLUDES:
            repo_pats += STACK_TEST_EXCLUDES[s]
    if not a.include_tests:
        repo_pats += TEST_EXCLUDES
    excluded = lambda p: any(fnmatch.fnmatch(p, g) for g in repo_pats)

    commits, skipped = read_history(path, a.since, a.max_files_per_commit, excluded)
    in_head = {p for p in all_files if not excluded(p)}

    st = {}
    now = time.time()
    for c in commits:
        is_fix = bool(bug_re.search(c["subject"]))
        for f, add, dele in c["files"]:
            if f not in in_head:
                continue
            s = st.setdefault(f, {"commits": 0, "added": 0, "deleted": 0, "bugfix": 0,
                                  "authors": collections.Counter(), "last": 0, "last_by": {}})
            s["commits"] += 1
            s["added"] += add
            s["deleted"] += dele
            s["bugfix"] += is_fix
            s["authors"][c["author"]] += 1
            s["last"] = max(s["last"], c["ts"])
            s["last_by"][c["author"]] = max(s["last_by"].get(c["author"], 0), c["ts"])

    paths = [p for p, s in st.items() if s["commits"] >= a.min_commits]
    dropped = len(st) - len(paths)
    blobs = read_blobs(path, paths)
    rows = []
    for p in paths:
        lang, kind = lang_and_kind(p)
        if a.code_only and kind == "config":
            continue
        m = measure(blobs[p]) if p in blobs else None
        if m is None:
            continue
        s = st[p]
        top_author, top_n = s["authors"].most_common(1)[0]
        share = top_n / s["commits"]
        single = share >= 0.8 and s["commits"] >= 5
        inactive = (now - s["last_by"][top_author]) > a.recent_days * 86400
        complexity = m[0] if kind == "config" else m[1]
        rows.append({
            "repo": name, "path": p, "lang": lang, "kind": kind,
            "commits": s["commits"], "added": s["added"], "deleted": s["deleted"],
            "bugfix_commits": s["bugfix"], "authors": len(s["authors"]), "top_author_share": round(share, 2),
            "single_owner": single, "owner_inactive": bool(single and inactive),
            "loc": m[0], "complexity": complexity,
            "last_change": datetime.date.fromtimestamp(s["last"]).isoformat(),
        })

    keep = {r["path"] for r in rows}
    per, shared = collections.Counter(), collections.Counter()
    tickets = collections.defaultdict(set)
    for c in commits:
        fs = sorted({f for f, _, _ in c["files"] if f in keep})
        for f in fs:
            per[f] += 1
        for pair in itertools.combinations(fs, 2):
            shared[pair] += 1
        if fs:
            for t in set(a.ticket_re.findall(c["subject"])):
                if t.split("-")[0] not in NOT_TICKETS:
                    tickets[t].update(fs)
    pairs = []
    for (x, y), n in shared.items():
        if n >= a.min_shared:
            deg = n / ((per[x] + per[y]) / 2)
            pairs.append({"repo": name, "a": x, "b": y, "shared": n, "degree": round(deg, 2),
                          "crosses_module": module_for(x, marker_dirs) != module_for(y, marker_dirs)})
    pairs.sort(key=lambda q: (-q["degree"], -q["shared"]))
    partners = collections.Counter()
    for q in pairs:
        if q["degree"] >= 0.5:
            partners[q["a"]] += 1
            partners[q["b"]] += 1

    for r in rows:
        r["coupling_partners"] = partners.get(r["path"], 0)
        sig = signals.get(f"{name}::{r['path']}") or signals.get(r["path"]) or {}
        for k in ("fan_in", "fan_out", "issues", "issues_high", "runtime"):
            if k in sig:
                r[k] = sig[k]
        if "complexity" in sig:
            r["complexity"] = sig["complexity"]
            r["complexity_source"] = "supplied"
    if len(rows) < a.min_files:
        warnings.append(f"Only {len(rows)} files qualify in {name}: percentile ranks are noisy, so no file there is called a hotspot (capped at watch).")
    if rows and not any(r["bugfix_commits"] for r in rows):
        warnings.append(f"No commit subjects in {name} matched the bug-fix pattern: the bug-fix signal is empty.")
    info = {"name": name, "path": str(path), "head": head, "stacks": stacks, "commits_analyzed": len(commits),
            "skipped_large_commits": skipped, "files_ranked": len(rows), "files_below_min_commits": dropped}
    return rows, pairs, tickets, info, warnings


def score_rows(rows, a):
    """Per-repo, per-kind percentile scoring. Mutates rows."""
    by_group = collections.defaultdict(list)
    for r in rows:
        by_group[(r["repo"], r.get("kind", "code"))].append(r)
    for (repo, kind), rs in by_group.items():
        cols = {
            "churn": [r["commits"] for r in rs],
            "complexity": [r["complexity"] for r in rs],
            "bugfix": [r["bugfix_commits"] for r in rs],
            "coupling": [r["coupling_partners"] for r in rs],
            "fan_in": [r.get("fan_in", 0) for r in rs],
            "issues": [r.get("issues_high", 0) * 3 + r.get("issues", 0) for r in rs],
            "runtime": [r.get("runtime", 0) for r in rs],
        }
        pct = {k: percentiles(v) for k, v in cols.items()}
        available = {"core", "owner"} | {k for k in ("bugfix", "coupling", "fan_in", "issues", "runtime") if max(cols[k]) > 0}
        for i, r in enumerate(rs):
            core = math.sqrt(pct["churn"][i] * pct["complexity"][i])
            owner = 1.0 if r["owner_inactive"] else 0.6 if r["single_owner"] else 0.0
            parts = {"core": core, "owner": owner, **{k: pct[k][i] for k in available - {"core", "owner"}}}
            total_w = sum(WEIGHTS[k] for k in available)
            r["score"] = round(100 * sum(WEIGHTS[k] * parts[k] for k in available) / total_w, 1)
            hit = [k for k in HIT_SIGNALS if cols[k][i] > 0 and pct[k][i] >= a.threshold]
            if r["single_owner"]:
                hit.append("owner")
            r["signals"] = hit
            strong = "churn" in hit and "complexity" in hit
            r["class"] = "hotspot" if strong or len(hit) >= 3 else "watch" if len(hit) == 2 else "none"
            if len(rs) < a.min_files and r["class"] == "hotspot":
                r["class"], r["small_repo"] = "watch", True
    rows.sort(key=lambda r: (-r["score"], -r["commits"], r["path"]))
    for n, r in enumerate(rows, 1):
        r["rank"] = n


def directory_rollup(rows):
    groups = collections.defaultdict(list)
    for r in rows:
        parts = r["path"].split("/")[:-1]
        for d in range(1, min(len(parts), 4) + 1):
            groups[(r["repo"], "/".join(parts[:d]) + "/")].append(r)
    out = []
    for (repo, d), rs in groups.items():
        top3 = sorted((r["score"] for r in rs), reverse=True)[:3]
        hot = sum(r["class"] == "hotspot" for r in rs)
        watch = sum(r["class"] == "watch" for r in rs)
        cls = "hotspot" if hot >= 2 or (hot >= 1 and len(rs) <= 3) else "watch" if hot == 1 or watch >= 2 else "none"
        out.append({"repo": repo, "path": d, "files": len(rs), "hotspot_files": hot, "watch_files": watch,
                    "score": round(sum(top3) / len(top3), 1), "class": cls})
    out.sort(key=lambda d: (-d["score"], d["path"]))
    return out


def cross_repo(all_tickets):
    """all_tickets: {repo: {ticket: set(files)}}. Pair repos that share ticket ids."""
    by_ticket = collections.defaultdict(dict)
    for repo, ts in all_tickets.items():
        for t, files in ts.items():
            by_ticket[t][repo] = files
    pair_t, pair_f = collections.defaultdict(list), collections.Counter()
    for t, rs in by_ticket.items():
        if len(rs) < 2:
            continue
        for ra, rb in itertools.combinations(sorted(rs), 2):
            pair_t[(ra, rb)].append(t)
            for fa in sorted(rs[ra])[:30]:
                for fb in sorted(rs[rb])[:30]:
                    pair_f[(ra, fa, rb, fb)] += 1
    pairs = [{"repos": list(k), "shared_tickets": len(v), "example_tickets": sorted(v)[:5]} for k, v in pair_t.items()]
    pairs.sort(key=lambda p: -p["shared_tickets"])
    files = [{"a": f"{ra}::{fa}", "b": f"{rb}::{fb}", "shared_tickets": n}
             for (ra, fa, rb, fb), n in pair_f.most_common(10) if n >= 2]
    return pairs, files


def note_for(r):
    bits = [f"{r['commits']} commits", f"{r['bugfix_commits']} fix-like"]
    if r.get("kind") == "config":
        bits.append(f"config ({r.get('lang', 'config')})")
    elif r.get("lang"):
        bits.append(r["lang"])
    if r.get("small_repo"):
        bits.append("repo too small for a hotspot call")
    if r["single_owner"]:
        bits.append(f"{round(r['top_author_share'] * 100)}% one author" + (", not recently active" if r["owner_inactive"] else ""))
    if r["coupling_partners"]:
        bits.append(f"{r['coupling_partners']} co-change partners")
    return ", ".join(bits)


def write_md(path, report, rows, dirs, pairs, xpairs, xfiles, top):
    L = ["# Hotspot report", "",
         f"Window: since {report['window']}. Generated {report['generated_at']}.", "",
         "Hotspots are ranked from history and other signals. A rank is a prompt to read the code, not a defect finding.", "",
         "## Repositories", "", "| Repo | Stacks | HEAD | Commits | Files ranked | Large commits skipped |", "|---|---|---|---|---|---|"]
    for r in report["repos"]:
        stacks_str = ", ".join(r.get("stacks", [])) or "none"
        L.append(f"| {r['name']} | {stacks_str} | `{r['head']}` | {r['commits_analyzed']} | {r['files_ranked']} | {r['skipped_large_commits']} |")
    if report["warnings"]:
        L += ["", "## Warnings", ""] + [f"- {w}" for w in report["warnings"]]
    L += ["", f"## Top {top} files", "",
          "| # | Repo | File | Kind | Lang | Class | Score | Commits | Fix-like | Authors | Top share | Complexity | Signals |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows[:top]:
        L.append(f"| {r['rank']} | {r['repo']} | `{r['path']}` | {r.get('kind', 'code')} | {r.get('lang', '-')} | {r['class']} | {r['score']} | {r['commits']} | "
                 f"{r['bugfix_commits']} | {r['authors']} | {round(r['top_author_share'] * 100)}% | {r['complexity']} | {', '.join(r['signals']) or '-'} |")
    L += ["", "## Directories", "", "| Repo | Directory | Class | Score | Files | Hotspot files |", "|---|---|---|---|---|---|"]
    for d in [d for d in dirs if d["class"] != "none"][:10]:
        L.append(f"| {d['repo']} | `{d['path']}` | {d['class']} | {d['score']} | {d['files']} | {d['hotspot_files']} |")
    L += ["", "## Files that change together", "",
          "Pairs that cross modules without an obvious reason point to coupling the diagrams may not show.", "",
          "| Repo | File A | File B | Shared commits | Degree | Crosses module |", "|---|---|---|---|---|---|"]
    for q in pairs[:15]:
        L.append(f"| {q['repo']} | `{q['a']}` | `{q['b']}` | {q['shared']} | {q['degree']} | {'yes' if q['crosses_module'] else 'no'} |")
    if xpairs:
        L += ["", "## Changes that span repositories", "", "Repos linked by shared ticket ids in commit subjects.", "",
              "| Repos | Shared tickets | Examples |", "|---|---|---|"]
        for p in xpairs[:10]:
            L.append(f"| {' and '.join(p['repos'])} | {p['shared_tickets']} | {', '.join(p['example_tickets'])} |")
        if xfiles:
            L += ["", "| File A | File B | Shared tickets |", "|---|---|---|"]
            for f in xfiles:
                L.append(f"| `{f['a']}` | `{f['b']}` | {f['shared_tickets']} |")
    L += ["", "## Reading this report", "",
          "- Percentiles are computed within each repository and file kind (code vs config), so scores compare files reliably.",
          "- Complexity is an indentation proxy for code; for configuration files, size in lines stands in for complexity.",
          "- Fix-like commits come from a subject-line pattern. Squash merges and terse messages hide fixes.",
          "- Renames appear as delete plus add, which can split a file's history.",
          "- A complex file that rarely changes is not a hotspot. It may still be a structural risk: check fan-in and cycles.",
          "- Test files, docs, lockfiles, generated and vendored code are excluded per detected stack unless the matching include flag was used.",
          "- No individual is named. Do not use these numbers to assess people.", ""]
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--out", default="docs")
    ap.add_argument("--since", default="12 months ago")
    ap.add_argument("--signals")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--embed-top", type=int, default=40)
    ap.add_argument("--min-commits", type=int, default=3)
    ap.add_argument("--min-files", type=int, default=10,
                    help="repos with fewer ranked files are capped at class \"watch\" (default 10)")
    ap.add_argument("--max-files-per-commit", type=int, default=40)
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--min-shared", type=int, default=5)
    ap.add_argument("--recent-days", type=int, default=180)
    ap.add_argument("--bugfix-regex", default=r"\b(fix|fixes|fixed|bug|hotfix|defect|regression|incident|revert|patch)\b")
    ap.add_argument("--ticket-regex", default=r"\b[A-Z][A-Z0-9]+-\d+\b")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--include-docs", action="store_true")
    ap.add_argument("--include-tests", action="store_true", help="rank test files too (excluded by default)")
    ap.add_argument("--code-only", action="store_true", help="exclude configuration files (YAML, JSON, TOML, etc.) and rank code files only")
    a = ap.parse_args()

    bug_re = re.compile(a.bugfix_regex, re.I)
    a.ticket_re = re.compile(a.ticket_regex)
    signals = json.loads(pathlib.Path(a.signals).read_text()) if a.signals else {}

    names = [pathlib.Path(r).resolve().name for r in a.repos]
    if len(set(names)) != len(names):
        sys.exit("Repository directory names must be unique (they label results): " + ", ".join(names))

    rows, pairs, infos, warnings, tickets = [], [], [], [], {}
    for name, repo in zip(names, a.repos):
        try:
            r, p, t, info, w = analyze_repo(name, pathlib.Path(repo).resolve(), a, bug_re, signals)
        except RuntimeError as e:
            sys.exit(str(e))
        rows += r
        pairs += p
        infos.append(info)
        warnings += w
        tickets[name] = t
    score_rows(rows, a)
    for r in rows:
        r["note"] = note_for(r)
    dirs = directory_rollup(rows)
    xpairs, xfiles = cross_repo(tickets) if len(names) > 1 else ([], [])
    pairs.sort(key=lambda q: (-q["degree"], -q["shared"]))

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": time.strftime("%Y-%m-%d"), "window": a.since, "weights": WEIGHTS,
        "threshold": a.threshold, "repos": infos, "warnings": warnings,
        "files": rows, "directories": dirs, "coupling": pairs[:200],
        "cross_repo": {"repo_pairs": xpairs, "file_pairs": xfiles},
    }
    (out / "hotspots.json").write_text(json.dumps(report, indent=2) + "\n")
    write_md(out / "hotspots.md", report, rows, dirs, pairs, xpairs, xfiles, a.top)

    emb = {}
    for r in [r for r in rows if r["class"] != "none"][:a.embed_top]:
        emb[f"{r['repo']}::{r['path']}"] = {"score": r["score"], "rank": r["rank"], "class": r["class"],
                                            "signals": r["signals"], "note": r["note"]}
    for d in [d for d in dirs if d["class"] != "none"][:15]:
        emb[f"{d['repo']}::{d['path']}"] = {"score": d["score"], "rank": 0, "class": d["class"], "signals": [],
                                            "note": f"{d['hotspot_files']} hotspot and {d['watch_files']} watch files of {d['files']}"}
    (out / "hotspots.embed.js").write_text(
        f"// Replace the sample HOTSPOTS object in the diagram page with this. Generated {report['generated_at']}.\n"
        f"const HOTSPOTS = {json.dumps(emb, indent=2)};\n")

    hot = sum(r["class"] == "hotspot" for r in rows)
    watch = sum(r["class"] == "watch" for r in rows)
    print(f"{len(rows)} files ranked across {len(names)} repo(s): {hot} hotspot, {watch} watch. Wrote {out}/hotspots.json, .md, .embed.js")
    for w in warnings:
        print("warning:", w, file=sys.stderr)


if __name__ == "__main__":
    main()
