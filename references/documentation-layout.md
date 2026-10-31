# Documentation Structure and Layered Manuals

When documenting codebases, tailor depth and structure to the system size and requested audience.

## Single-System Default: `docs/TECHNICAL_MANUAL.md`

For a single repository or focused service, compile a single self-contained manual covering:

1. **Executive Summary**: High-level problem domain, system boundaries, and current status.
2. **Architecture Overview & Request Flow**: High-level component interactions and lifecycle of typical requests.
3. **Technology Stack & Runtime Dependencies**: Complete matrix of languages, frameworks, storage engines, queues, and build tools.
4. **Design Decisions, Patterns, and Trade-offs**: Architecture Decision Records (ADRs) and rationale backed by code evidence.
5. **Key Use Cases & User Journeys**: Step-by-step transaction walkthroughs for primary functional capabilities.
6. **Core Components & Responsibilities**: Deep dive into primary packages, services, and modules.
7. **Data Models & Data Flow**: Schema definitions, storage mechanics, caching, and data pipelines.
8. **Integration Points & External Contracts**: Third-party APIs, incoming webhooks, and protocol specifications.
9. **Deployment & Runtime Topology**: Infrastructure, containerization, orchestration, and environment parity.
10. **Performance Characteristics & Known Bottlenecks**: Measured or hypothesized latency, throughput, and memory patterns.
11. **Security Model & Trust Boundaries**: Authentication, authorization, token lifecycle, secrets management, and sensitive data handling.
12. **Open Questions for SMEs**: Gaps in static analysis requiring runtime inspection or SME input.
13. **Glossary & Diagram Index**: Acronyms, domain terms, and links to diagram tabs.

## Layered Layout for Large or Multi-Repo Estates

For multi-repo estates, break the documentation into layered files so different readers can engage at their desired depth:

| File | Audience | Purpose |
|---|---|---|
| `docs/00-executive-summary.md` | Leadership & Product | High-level capabilities, key risks, technical debt summary, modernization roadmap |
| `docs/01-context.md` | All Readers | System context, user personas, external systems, and comprehensive Technology Stack Matrix |
| `docs/02-containers.md` | Architects & Leads | Deployable units, datastores, message queues, and cross-repo contracts |
| `docs/03-use-cases.md` | Architects & Developers | End-to-end execution paths for primary business use cases, sequence flows, failure modes |
| `docs/04-components/<repo>.md` | Developers | Module layering, internal design patterns, entry points, and key classes for each repo |
| `docs/05-data.md` | Data & Backend Engineers | ERDs, database schemas, migration history, caching strategies, and data lineage |
| `docs/06-integrations.md` | Integration Engineers | External APIs, webhooks, event schemas, retry policies, and circuit breakers |
| `docs/07-security.md` | Security & Compliance | Trust zones, authentication flows, authorization rules, secret storage, sensitive data classification |
| `docs/08-deployment.md` | DevOps & SRE | Infrastructure topology, CI/CD pipelines, container orchestration, environment configs |
| `docs/09-risks-and-migration.md` | Architects & Leadership | Ranked hotspots, technical debt register, modernization hurdles, and proposed remediation |
| `docs/10-open-questions.md` | SMEs | Specific unverified assumptions and questions for subject-matter experts |
| `docs/tour.md` | Onboarding Developers | Guided code tour following dependency direction from foundation utilities to high-level flows |
| `docs/hotspots.md` | Maintainers & Architects | Generated output from `scripts/hotspots.py` with file and directory risk rankings |
| `docs/ledger.json` | Maintainers & Tools | Structured evidence ledger with verification status, confidence, and commit SHAs |
| `docs/drift.md` | Maintainers & Architects | Drift register comparing documentation claims against code realities |

## Code Citing Conventions

- Always cite code as `relative/path/to/file.ext:line_number`.
- Link claims to their Ledger ID (`F-####`) to enable traceability.
- Append a "Last verified" section to each chapter listing repository commit SHAs used.

