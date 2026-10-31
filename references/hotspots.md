# Code Hotspots and Issue Validation

Hotspot analysis identifies architectural risk by triangulating independent signals rather than relying on a single metric.

## Multi-Signal Triangulation

A file is classified as a **hotspot** when churn AND complexity are both high, or when three or more signals agree. It is classified as **watch** when two signals agree. A single isolated metric is never treated as a hotspot.

### Signals Evaluated

| Signal | Source | Definition | Meaning |
|---|---|---|---|
| `churn` | Git log | Number of commits modifying the file in the time window | The code is under frequent modification |
| `complexity` | Indentation / LOC | Sum of indentation levels (for code) or line count (for config) | Deeply nested logic or sprawling configuration |
| `bugfix` | Commit subjects | Commits matching fix/bug/defect heuristics | The file experiences recurring defects or regressions |
| `coupling` | Git co-change | Files frequently modified in the same commit | Hidden dependencies or lack of modular cohesion |
| `owner` | Git authors | One contributor authored ≥80% of changes | Single-point-of-failure knowledge risk |
| `fan_in` | Code graph / AST | Number of distinct incoming callers | High-impact dependency with broad blast radius |
| `issues` | Static analysis | Rule violation counts from SARIF analyzers | Lint, formatting, or static code violations |
| `issues_high` | Static analysis | High/critical severity security or correctness findings | Actionable defect or vulnerability risks |
| `runtime` | APM / Profiler | Fraction of request time or slow queries attributed to file | Measurable production execution bottleneck |

## Multi-Stack & Config Awareness

`scripts/hotspots.py` automatically detects stacks present in each repository (Python, TypeScript, C#, Java, Go, Ruby, PHP, Rust, Terraform, YAML/Config):
1. **Per-Stack Exclusions**: Vendor libraries, generated classes, and test fixtures are excluded based on the detected stacks.
2. **Config Files Ranked on Their Own Terms**: Configuration files (YAML, JSON, TOML, XML, Dockerfiles, etc.) are ranked in their own percentile group (`kind: "config"` vs `kind: "code"`). Lines of code stand in for complexity because indentation depth is meaningless for structured data.
3. **`--code-only` Flag**: Optionally exclude configuration files entirely to focus purely on application code.

## Running Hotspot Analysis

### 1. Basic Git Ranking
```bash
python3 scripts/hotspots.py path/to/repo1 [path/to/repo2 ...] --out docs --since "12 months ago"
```
Outputs:
- `docs/hotspots.json`: Full machine-readable metrics and metadata.
- `docs/hotspots.md`: Human-readable Markdown summary with repo, directory, and coupling tables.
- `docs/hotspots.embed.js`: JavaScript snippet to embed directly into `diagrams/index.html`.

### 2. Ingesting Static Analysis (SARIF)
Extract findings from any SARIF-compatible scanner without exposing code snippets or secrets:
```bash
python3 scripts/sarif_to_signals.py scan.sarif --repo backend-api --root path/to/repo --out docs/signals.json --merge
```

### 3. Re-Ranking with Signals
```bash
python3 scripts/hotspots.py path/to/repo --signals docs/signals.json --out docs
```

## Interpreting Findings

- For each of the top 10 ranked hotspots, inspect the source lines and document:
  1. The contributing signals.
  2. The code patterns explaining the score (e.g., God class, deep branching, state machine in controller).
  3. Risk assessment and remediation direction (e.g., characterization tests, decomposition, interface extraction).
- Cross-module file coupling without documented interface contracts indicates architectural leakage; document these as `(inferred)` edges.
- Never name or evaluate individuals. Author metrics are reported strictly as anonymous aggregate counts and percentage shares.

