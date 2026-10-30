# Architecture Docs Skill

An AI-agent skill for creating evidence-based architecture documentation from existing codebases. It supports single repositories, legacy systems, and multi-repository estates, and includes a self-contained HTML diagram template.

## What It Produces

For a small, single-repository system, the default outputs are:

- `docs/TECHNICAL_MANUAL.md`: architecture overview, key components, data and integration flows, deployment, security boundaries, and other topics supported by evidence.
- `docs/diagrams/index.html`: an offline, interactive architecture diagram generated from `assets/diagrams.html`.

For larger or multi-repository scopes, the skill can create layered documentation for different audiences, plus an evidence ledger (`docs/ledger.json`) and a drift register (`docs/drift.md`). It records the repository commit SHAs used so readers can trace claims to a specific code state. Output paths can be set by the user. Existing files are not to be overwritten.

## Contents

```text
arch-docs-skill/
├── SKILL.md
├── README.md
└── assets/
    └── diagrams.html
```

- `SKILL.md` contains the workflow, evidence standards, output conventions, and completion checks.
- `assets/diagrams.html` is the interactive diagram template. Its `DIAGRAMS` object contains illustrative sample data that must be fully replaced with project-specific findings before delivery.

## Use

Install or reference this directory in an AI coding-agent environment that supports `SKILL.md` skills. Keep `SKILL.md` and `assets/diagrams.html` together so the skill can find its template. Invoke it with a request to document an existing system, for example:

- “Create an architecture manual for this repository for new engineers.”
- “Map the data flow and security boundaries across these repositories.”
- “Assess this legacy system for modernization and document its runtime entry points.”
- “Generate a layered technical guide and an offline diagram page.”

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

The template provides tabs for app flow, data flow, integration flow, security boundaries, module layering, and deployment. The skill adds a cross-repository view when relevant. The page supports:

- Source, ledger ID, confidence, repository, and commit details for diagram items
- Confidence styling for inferred, unverified, and dead-candidate items
- A repository filter, verified-only checkbox, and search field
- Clickable nodes and edges, keyboard-accessible node selection, and animated flow controls
- A footer check for missing ledger IDs, unverified items, and undefined edge endpoints

The generated page must remain self-contained and offline. Sensitive values must never be included. Only label data as sensitive when the code or configuration supports that classification.

## Verification

Before calling the documentation complete, the skill checks that:

- Every diagram item has a ledger ID and the footer reports no missing IDs.
- Every edge points to defined nodes, and internal links and diagram tabs resolve.
- Source references and counts match the recorded repository commit and underlying code or data.
- Every documentation/code conflict is represented in the drift register.
- Outputs contain no secret-like values, no template sample data, and no overwritten files.
- A separate validation pass reviews the evidence ledger for legacy or multi-repository work.

Static inspection cannot establish runtime behavior by itself. The final summary identifies the discovery method, repository SHAs, ledger totals, drift count, top risks, limitations, and findings that still need verification.
