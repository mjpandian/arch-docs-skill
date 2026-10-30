---
name: arch-docs-skill
description: Create evidence-based architecture documentation and an offline interactive diagram page for an existing codebase, including legacy systems and multi-repo estates. Use for architecture guides, technical manuals, system overviews, modernization assessments, onboarding guides, or implementation deep-dives.
---

# Architecture Docs

Document what an existing system does, how its parts interact, and which design choices are supported by repository evidence. Confirm the requested audience, scope, and output paths from the user's request. Treat applicable repository instructions and user constraints as authoritative.

## Workflow

1. **Scope**: Identify the system boundary, the repositories in scope, intended readers, desired depth, requested outputs, and existing documentation to preserve. Note any runtime evidence available (traces, logs, production config, feature-flag state). Ask a concise clarifying question only when a missing choice blocks useful work. Otherwise, record the assumption and proceed.
2. **Estimate**: For large or multi-repo scope, state the expected size before starting (repositories, approximate file count, number of analysis batches). This lets the user narrow scope before a costly run.
3. **Discover**: For each repository, record the commit SHA, languages and framework versions, build system, deployable units, and entry points. Entry points include HTTP routes, queue consumers, scheduled jobs, batch scripts, stored procedures, database triggers, and file watchers. Note generated and vendored code to exclude. Use configured code graph or index tools when available, following their usage and freshness instructions. Otherwise, list repository files and search targeted symbols. Inspect tests when they help confirm behavior. If no graph tool was used, say so in the summary.
4. **Map**: Trace entry points, components, dependencies, data stores, external integrations, and security boundaries. For multi-repo systems, derive cross-repo links only from contracts: API specifications, schemas, topic names matched on both producer and consumer sides, shared database schemas, and shared client libraries. Do not infer a link from name similarity alone.
5. **Record**: Write each material fact to the evidence ledger before drafting prose (see Evidence and efficiency).
6. **Outline**: Plan the chapter hierarchy and diagrams before drafting. Reuse consistent names for components, layers, and data.
7. **Write**: Start with a concise system summary, then explain architecture and implementation detail. Support design rationale with code, configuration, tests, or explicit source documentation. Write prose only from ledger entries.
8. **Diagram**: Populate the interactive template with confirmed project data and link the page from the documentation.
9. **Verify**: Run the checks in Completion criteria. Report what was verified and what was not.

## Evidence and efficiency

- Prefer graph or index queries and targeted reads over loading large unrelated files. Read by line range where possible. Do not reread a file unless a specific question requires it.
- Treat existing documentation as a hypothesis. Check each claim you reuse against code. Record disagreements in a drift register.
- Verify counts from code or structured data, not narrative documentation.
- Distinguish observed facts from interpretation. Mark material uncertainty `(inferred)` and state what remains to be verified.
- Do not conclude that a component is unused, secure, encrypted, publicly exposed, or tested solely because a search returned no result. Record such cases as `dead-candidate` or as open questions, to be confirmed.
- Never invent paths, line numbers, protocols, authentication mechanisms, or security controls. Do not expose secret values. If you find a secret, report only its file, its line, and the fact that it exists.
- Report security weaknesses as risks with remediation direction. Do not write exploits or proofs of concept.
- Stop when evidence is sufficient for the requested scope. Do not pad documents with unsupported sections.

### Evidence ledger

For legacy or multi-repo scope, keep `docs/ledger.json`. For a single small system, the ledger is optional, but claims must still be checkable. Each entry has this shape:

```json
{
  "id": "F-0001",
  "claim": "Patient records are encrypted at rest with field-level encryption",
  "repo": "backend-api",
  "src": "src/store/patients.py:17",
  "commit": "a1b2c3d",
  "confidence": "verified",
  "evidence": "encrypt_field() called on ssn and dob before insert",
  "source_docs": ["docs/old/security.md:12"],
  "status": "active"
}
```

| Confidence | Meaning |
|---|---|
| `verified` | Confirmed by reading the code at `src` at the recorded commit |
| `inferred` | Derived from graph analysis, naming, or structure. Needs a reading check |
| `doc-only` | Stated in existing documentation but not found in code. Treat as a risk until confirmed |
| `conflict` | Code and documentation disagree, or code breaks a stated rule. Both sides go in the drift register |
| `static-only` | Found in code, but running in production cannot be confirmed without runtime evidence |
| `dead-candidate` | No incoming references found. Confirm before removing or documenting as live |

Retire entries by setting `"status": "superseded"` and pointing to the replacement. Do not delete them.

Create `docs/drift.md` as a table of every `conflict` and `doc-only` entry: the documented statement, what the code shows, and the recommended action.

## Legacy and multi-repo considerations

- Look for behavior outside HTTP: scheduled jobs, queue consumers, batch scripts, stored procedures, triggers, and file drops. Legacy systems often run critical logic there.
- Note configuration-driven wiring, reflection, and dynamic dispatch. Mark these `static-only` unless runtime evidence confirms them.
- Mark feature-flagged and dead-candidate code explicitly. Do not document it as live.
- Shared database coupling is often the hardest migration blocker. For each shared table, record which repository writes it and which only reads it.
- Use git history for ownership and churn. Flag single-owner, high-churn modules as risks. Rationale reconstructed from commit messages or pull requests is `(inferred)`.
- Performance findings are hypotheses. Record each with its file and line, and propose how to measure it. Do not state timings or benchmarks without measurement.
- Security findings are reported as risks. Hardcoded secrets are reported by location only.

## Documentation output

Write Markdown to the user-requested location. If none is specified, use `docs/TECHNICAL_MANUAL.md`. Do not overwrite existing documentation. Choose a new filename, or ask if the requested path is occupied.

Use clear headings, syntax-highlighted code blocks, tables for structured inventories, and concise notes where useful. Reference code as `file_path:line_number` when the location can be verified. Use relative links to the diagram page.

Cover topics that apply, scaled to the system:

1. Executive summary
2. Architecture overview and request or application flow
3. Design decisions and trade-offs
4. Core components and their responsibilities
5. Data models and data flow
6. Integration points
7. Deployment and runtime topology
8. Performance characteristics and known bottlenecks, when measurable
9. Security model and trust boundaries, when supported by evidence
10. Open questions for subject-matter experts
11. Glossary, references, and diagram index as needed

Omit topics that do not apply rather than inventing content.

For large or multi-repo scope, split the output into layered files so each reader can stop at the right depth:

| File | Audience |
|---|---|
| `00-executive-summary.md` | Leadership |
| `01-context.md` | Everyone: users, external systems, repositories |
| `02-containers.md` | Architects: deployable units, data stores, contracts |
| `03-components/<repo>.md` | Developers: modules, layering, key flows |
| `04`–`09` | Data, integrations, security, performance, deployment, risks and migration |
| `10-open-questions.md` | SMEs |
| `inventory.md`, `ledger.json`, `drift.md` | Maintainers |

When helpful, add `docs/tour.md`: a reading order that follows dependencies, starting from leaf modules and moving toward top-level flows.

Each section cites ledger IDs or `file_path:line_number` for specific claims, marks anything not verified, links to its diagram tab, and ends with a "Last verified" line listing the commit SHAs used.

## Interactive diagram page

Unless the user specifies another path, create `docs/diagrams/index.html` from `assets/diagrams.html`. Keep the page self-contained and offline. Preserve the template's rendering code unless a requested view requires a new shape. Do not overwrite an existing output. Choose a new path or ask the user.

Replace the template's entire `DIAGRAMS` sample data. The sample nodes and descriptions are illustrative. They include unverified behavior and security claims, which must not be carried forward as project facts.

### Data contract

Each node:

```
{ id, label, x, y, w, h, src, detail, summary?, ledger, confidence, repo?, commit?, sensitive? }
```

- `summary` is one or two plain-English sentences for non-specialist readers. `detail` holds the technical notes.
- `ledger` is the `F-####` ID from `docs/ledger.json`.
- `confidence` is one of the six levels in the Evidence section.
- `src` is `file_path:line_number`, or `external`.

Each edge: `{ from, to, label, ledger, confidence, commit? }`. Every edge endpoint must reference a defined node.

Each zone: `{ id, label, x, y, w, h }`. Zones represent trust zones in the security and deployment views. In the cross-repo view, they represent repositories, with the zone id equal to the repository name.

### Required views

Provide these from the template, one tab each: app flow, data flow, integration flow, security boundaries, module layering, and deployment. Add a cross-repo map for multi-repo scope. Adapt or omit a view that is outside the requested scope or not supported by evidence.

### How the page presents evidence

- Verified items are solid. Inferred items are dashed.
- `doc-only`, `conflict`, and `static-only` items carry a ⚠ badge, and their edges are amber.
- `dead-candidate` items are grey and labelled "(dead?)".
- Items without a ledger ID have a dotted red border.
- The **Verified only** checkbox hides everything not verified, for stakeholder views.
- The **Repo** filter dims items outside the chosen repository.
- The **Find** box highlights nodes matching a name, a summary, or a ledger ID.
- The footer reports missing ledger IDs, unverified items, and edges with undefined endpoints.

### Diagram rules

- Use a verified `file_path:line_number` in each `src`. Do not invent source locations.
- Mark unconfirmed components and relationships `(inferred)`, and say what needs verification.
- Set `sensitive: true` only for confirmed sensitive data or systems: PII, PHI, credentials, or secrets. Never include secret values.
- Label each edge with a confirmed protocol, data type, or authentication mechanism. Mark uncertainty as inferred.
- Keep the page offline. Add no external scripts, fonts, images, or network calls.

## Project-specific constraints

Apply domain requirements, architecture layers, compliance caveats, and data-handling rules only when the user supplies them or the repository's own instructions contain them, such as a CLAUDE.md, AGENTS.md, or agent definition. Those apply only to that repository. Do not carry assumptions from another project into the documentation.

## Completion criteria

- The requested documentation exists at the agreed path and covers the relevant topics supported by evidence.
- The diagram exists at the agreed path, opens offline, and contains project data only. No sample data remains.
- The footer reports zero missing ledger IDs, and the edge-endpoint check passes.
- Every `src` path exists at the recorded commit. Every count matches a query over code or data.
- Every `doc-only` and `conflict` entry appears in the drift register.
- A scan of all output finds no secret-like strings.
- Internal links and tab hashes resolve.
- Nothing existing was overwritten.
- For legacy or multi-repo scope, a validation pass that did not write the documentation has reviewed the ledger for consistency.

The final summary states the discovery method and every fallback used, each repository with its commit SHA, ledger totals by confidence level, the drift count, the top five risks, and the material `(inferred)` items that need verification.
