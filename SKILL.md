---
name: arch-docs-skill
description: Create evidence-based architecture documentation and an offline interactive diagram page for an existing codebase, including legacy systems and multi-repo estates, with stack-aware hotspot and issue validation and optional TLA+ model checking. Use for architecture guides, technical manuals, system overviews, modernization assessments, onboarding guides, or implementation deep-dives.
---

# Architecture Docs

Document what an existing system does, how its parts interact, and which design choices are supported by repository evidence. Confirm the requested audience, scope, and output paths from the user's request. Treat applicable repository instructions and user constraints as authoritative.

## Workflow

1. **Scope**: Identify the system boundary, the repositories in scope, intended readers, desired depth, requested outputs, and existing documentation to preserve. Note any runtime evidence available (traces, logs, production config, feature-flag state). Ask a concise clarifying question only when a missing choice blocks useful work. Otherwise, record the assumption and proceed.
2. **Estimate**: For large or multi-repo scope, state the expected size before starting (repositories, approximate file count, number of analysis batches). This lets the user narrow scope before a costly run.
3. **Discover**: For each repository, record the commit SHA, languages, frameworks, runtime dependencies, build system, deployable units, and entry points. Compile a structured technology stack matrix (languages, frameworks, datastores, queues, build/deploy tooling). Consult the matching stack reference in `references/stacks/` for entry point idioms, hidden wiring, and tooling. Note generated and vendored code to exclude. Use configured code graph or index tools when available; otherwise list repository files and search targeted symbols. Inspect tests when they help confirm behavior. If no graph tool was used, say so in the summary.
4. **Map**: Trace entry points, components, dependencies, data stores, external integrations, security boundaries, and key use cases. For each primary functional use case, document the end-to-end transaction path across layers. For multi-repo systems, derive cross-repo links only from contracts: API specifications, schemas, topic names matched on both producer and consumer sides, shared database schemas, and shared client libraries. Do not infer a link from name similarity alone. See `references/legacy-and-multi-repo.md`.
5. **Record**: Write each material fact to the evidence ledger (`docs/ledger.json`) before drafting prose. See `references/ledger.md`.
6. **Outline**: Plan the chapter hierarchy and diagrams before drafting. Reuse consistent names for components, layers, and data. See `references/documentation-layout.md`.
7. **Write**: Start with a concise system summary, then explain architecture and implementation detail. Support design rationale with code, configuration, tests, or explicit source documentation. Write prose only from ledger entries.
8. **Diagram**: Populate the interactive template (`docs/diagrams/index.html`) from `assets/diagrams.html` with confirmed project data across the 8 required views, and link the page from the documentation. See `references/diagram-page.md`.
9. **Hotspots and issues**: Run `scripts/hotspots.py` to rank files by independent signals from git history, the code graph, static scanners (via `scripts/sarif_to_signals.py`), and runtime data. Inspect the top 10 files and write findings with code evidence. See `references/hotspots.md`.
10. **Model** (optional): For critical flows with concurrency, retries, ordering, or shared state, write small TLA+ models from the ledger, run them with TLC via `scripts/run_tlc.py`, and record the results. See `references/formal-validation.md`.
11. **Verify**: Run the checks in Completion criteria. Report what was verified and what was not.

## Core Principles

- **Ground in Evidence**: Prefer graph/index queries and targeted reads over loading large unrelated files. Cite `relative/path/to/file:line_number` for code claims and record them in `docs/ledger.json`.
- **Treat Docs as Hypotheses**: Verify existing documentation against code. Record disagreements and doc-only claims in `docs/drift.md`.
- **Honest Confidence Levels**: Mark material uncertainty `(inferred)`. Label unreferenced code `dead-candidate` and unconfirmed production deployment `static-only`. Never present an assumption as a confirmed fact.
- **Protect Secrets**: Never invent or expose secret values. If a secret is identified, report only its file, line number, and existence.
- **Remediation Direction**: Report security weaknesses and structural hotspots as risks with remediation direction; never write exploits or proofs of concept.
- **Zero Hallucinated Wiring**: Multi-repo links require verified contracts (OpenAPI, gRPC, schemas, matched topics).
- **Offline Self-Contained Output**: Diagrams must run entirely offline with zero external network requests or CDNs.

## Reference Guides

Detailed instructions, schemas, and per-stack guides are located in `references/`:

### Method & Output References
- [Evidence Ledger & Drift Register](references/ledger.md): Ledger schema, confidence levels, drift register, and lifecycle rules.
- [Legacy & Multi-Repo Considerations](references/legacy-and-multi-repo.md): Background workers, dynamic dispatch, shared database coupling, and contract mapping.
- [Documentation Structure & Layout](references/documentation-layout.md): Chapter outline for `TECHNICAL_MANUAL.md` and layered files (`00` to `10`) for multi-repo estates.
- [Interactive Diagram Page](references/diagram-page.md): Template contract, node/edge/zone schemas, tech stack display, animated use-case player, and the 8 required views.
- [Hotspots & Issue Validation](references/hotspots.md): Multi-signal triangulation, stack detection, config file ranking, SARIF integration, and interpretation.
- [Formal Validation with TLA+](references/formal-validation.md): When to model, reference specs, TLC execution with `scripts/run_tlc.py`, and badge integration.

### Stack-Specific References (`references/stacks/`)
Each stack reference provides detection markers, entry points, hidden wiring, config/secrets, data access, concurrency patterns, performance bottlenecks, security vectors, exclusions, and verified SARIF tool command lines:
- [Python Reference](references/stacks/python.md): FastAPI, Django, Flask, Celery, SQLAlchemy, Alembic, Bandit, Ruff.
- [TypeScript & JavaScript Reference](references/stacks/typescript.md): Express, NestJS, Next.js, BullMQ, Prisma, TypeORM, ESLint SARIF.
- [C# & .NET Reference](references/stacks/csharp.md): ASP.NET Core, Minimal APIs, EF Core, MassTransit, Roslyn ErrorLog SARIF.
- [Java & Kotlin Reference](references/stacks/java.md): Spring Boot, Quarkus, JPA/Hibernate, PMD SARIF, SpotBugs.
- [YAML, Kube & IaC Reference](references/stacks/yaml-and-iac.md): Kubernetes manifests, Helm, Kustomize, Terraform, Kube-Linter, Trivy, Checkov.
- [Go Reference](references/stacks/go.md): Gin, Chi, gRPC, GORM, sqlc, Goroutines, GolangCI-Lint, Govulncheck.

## Completion Criteria

Before declaring the documentation complete, verify:

- [ ] The requested documentation exists at the agreed path (`docs/TECHNICAL_MANUAL.md` or layered `docs/00`–`10`) and covers tech stack, architecture, design, data flow, security, deployment, and key use cases.
- [ ] The interactive diagram exists at `docs/diagrams/index.html`, opens offline without network requests, and contains confirmed project data across the required views (including key use cases and tech stack annotations).
- [ ] The diagram footer reports 0 missing ledger IDs and 0 dangling edge endpoints.
- [ ] Every source citation `file:line` exists at the recorded commit SHA.
- [ ] Every documentation/code conflict appears in `docs/drift.md`.
- [ ] All outputs are scanned and contain zero hardcoded secrets or sensitive credentials.
- [ ] If hotspots ran: `docs/hotspots.json`, `docs/hotspots.md`, and `docs/hotspots.embed.js` exist; top 10 hotspots have written findings with code evidence; no individuals are named.
- [ ] If TLA+ modeling ran: every result has a JSON execution record from `scripts/run_tlc.py`; violations cite counterexample traces mapped to code; no flow is labeled "proven" solely because TLC passed within bounds.
- [ ] The final summary states discovery methods, repository SHAs, ledger totals by confidence level, drift count, top risks, top hotspots, and material inferred items needing SME verification.
