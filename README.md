# Architecture Docs Skill

An AI-agent skill for creating evidence-based architecture documentation from existing codebases. It supports single repositories, legacy systems, and multi-repository estates, and includes a self-contained offline HTML diagram template, git hotspot ranking, static analyzer issue integration, and formal TLA+ validation.

## What It Produces

For a small, single-repository system, the default outputs are:

- `docs/TECHNICAL_MANUAL.md`: architecture overview, technology stack matrix, key use cases, core components, data and integration flows, deployment, security boundaries, and other topics supported by evidence.
- `docs/diagrams/index.html`: an offline, interactive architecture diagram generated from `assets/diagrams.html`.

For larger or multi-repository scopes, the skill creates layered documentation for different audiences (`00-executive-summary.md`, `01-context.md`, `02-containers.md`, `03-use-cases.md`, etc.), plus an evidence ledger (`docs/ledger.json`), drift register (`docs/drift.md`), and ranked hotspot analysis (`docs/hotspots.json`, `docs/hotspots.md`, `docs/hotspots.embed.js`). It records repository commit SHAs used so readers can trace claims to a specific code state.

## Contents

```text
arch-docs-skill/
├── SKILL.md                 # Lean entry workflow, core principles, and completion criteria
├── README.md                # Skill overview and usage guide
├── assets/
│   ├── diagrams.html        # Interactive offline HTML diagram template (8 views)
│   └── tla/                 # Reference TLA+ specs and configurations for concurrency
│       ├── QueueConsumer.tla
│       ├── QueueConsumer_safe.cfg
│       └── QueueConsumer_unsafe.cfg
├── references/              # On-demand reference documentation
│   ├── ledger.md            # Evidence ledger schema and drift register
│   ├── legacy-and-multi-repo.md # Dynamic wiring, non-HTTP entry points, database coupling
│   ├── documentation-layout.md  # Single and layered technical manual chapter outlines
│   ├── diagram-page.md      # Template specifications and interactive features
│   ├── hotspots.md          # Multi-signal triangulation and config file ranking
│   ├── formal-validation.md # TLA+ formal validation with TLC
│   └── stacks/              # Stack-specific detection, wiring, exclusions, and SARIF tools
│       ├── python.md
│       ├── typescript.md
│       ├── csharp.md
│       ├── java.md
│       ├── yaml-and-iac.md
│       └── go.md
├── scripts/
│   ├── hotspots.py          # Stack-aware git churn, complexity, coupling & config ranking
│   ├── sarif_to_signals.py  # Converts SARIF scanner outputs into hotspot signals
│   └── run_tlc.py           # Runs TLC model checker and outputs JSON execution records
└── tests/
    └── test_skill_tools.py  # Automated test suite for scripts, contracts, and HTML
```

- `SKILL.md` contains the lean entry workflow, evidence standards, and completion criteria.
- `references/` contains in-depth documentation templates, schemas, and stack-specific references.
- `assets/diagrams.html` is the interactive diagram template. Its `DIAGRAMS` object contains illustrative sample data that must be fully replaced with project-specific findings before delivery.
- `scripts/hotspots.py` ranks files by independent signals from git history and external analyzers, automatically detecting stacks and ranking configuration files in their own group.
- `scripts/sarif_to_signals.py` normalizes SARIF outputs from Semgrep, CodeQL, Trivy, ESLint, Bandit, PMD, Roslyn, and Kube-Linter into file-level signals without leaking code or secret snippets.
- `scripts/run_tlc.py` executes TLC against TLA+ models to check safety invariants.

## Use

Install or reference this directory in an AI coding-agent environment that supports `SKILL.md` skills. Keep `SKILL.md`, `assets/`, and `scripts/` together so the skill can access its tools and templates. Invoke it with a request to document an existing system, for example:

- “Scan this codebase and create an architecture manual with tech stack and key use cases.”
- “Map the data flow, security boundaries, and deployment topology across these repositories.”
- “Assess this legacy system for modernization, rank hotspots, and document its runtime entry points.”
- “Generate layered technical documentation and an interactive offline HTML diagram.”

Specify the audience, repositories, desired depth, and output paths when they matter. For large or multi-repository work, the skill estimates scope before analysis so the user can narrow it.

## Evidence Model

The skill favors graph/index queries when available, followed by targeted source, configuration, test, and history inspection. It does not treat existing documentation as proof: claims are checked against code, disagreements go into a drift register, and uncertain findings are labeled.

The evidence ledger uses these confidence values:

| Value | Meaning |
| --- | --- |
| `verified` | Confirmed in code at the recorded commit |
| `inferred` | Suggested by graph analysis or structure; needs a source check |
| `doc-only` | Present in existing documentation but not confirmed in code |
| `conflict` | Code and documentation disagree, or code violates a stated rule |
| `static-only` | Found statically, but production behavior is unconfirmed |
| `dead-candidate` | No incoming references found; confirm before treating as unused |

For legacy or multi-repository work, claims are recorded in `docs/ledger.json`, and `doc-only` and `conflict` findings are summarized in `docs/drift.md`. Cross-repository links must be supported by contracts such as API specifications, schemas, matched topic names, shared database schemas, or shared client libraries.

## Diagram Features

The template provides 8 interactive views:
1. **App flow**: Request lifecycle from entry point to response.
2. **Data flow**: Ingestion, validation, persistence, caching, and export.
3. **Integration flow**: Internal and external system communication protocols and credentials.
4. **Security boundaries**: Trust zones, controls, and sensitive data (PHI/PII/secrets).
5. **Module layering**: Permitted architectural layer dependencies.
6. **Deployment**: Runtime topology, environments, and network boundaries.
7. **Cross-repo map**: Contract-based inter-repository relationships.
8. **Key use cases**: Animated, step-by-step transaction walk-throughs for primary user journeys.

The page supports:
- **Tech stack annotations**: Displays component technologies directly on SVG nodes (e.g. `[PostgreSQL 16]`, `[FastAPI]`) and in the side panel.
- **Confidence styling**: Verified (solid), inferred (dashed), warnings for unverified (`⚠`), and dead candidates.
- **Interactive controls**: Play / Pause / Step sequential flow animation, animation speed control, repository filter, verified-only toggle, and search.
- **Hotspot overlay**: Visual heat-strips and ranks from `hotspots.py`.
- **Model-check indicators**: TLA+ verification badges (`✖` violation / `✓` passed within bounds).
- **Offline & private**: Zero external dependencies or network calls; sensitive values masked.

## Verification

Before calling the documentation complete, the skill checks that:

- Every diagram item has a ledger ID and the footer reports no missing IDs.
- Every edge points to defined nodes, and internal links and diagram tabs resolve.
- Source references and counts match the recorded repository commit and underlying code or data.
- Every documentation/code conflict is represented in the drift register.
- Outputs contain no secret-like values, no template sample data, and no overwritten files.
- Top ranked hotspots have written findings backed by code evidence.
- A separate validation pass reviews the evidence ledger for legacy or multi-repository work.
