# Evidence Ledger and Drift Register

Documenting an existing system requires grounding every architectural assertion in concrete repository evidence.

## Evidence Standards

- Prefer graph or index queries and targeted reads over loading large unrelated files. Read by line range where possible. Do not reread a file unless a specific question requires it.
- Treat existing documentation as a hypothesis. Check each claim reused against code. Record disagreements in a drift register.
- Verify counts from code or structured data, not narrative documentation.
- Distinguish observed facts from interpretation. Mark material uncertainty `(inferred)` and state what remains to be verified.
- Do not conclude that a component is unused, secure, encrypted, publicly exposed, or tested solely because a search returned no result. Record such cases as `dead-candidate` or as open questions, to be confirmed.
- Never invent paths, line numbers, protocols, authentication mechanisms, or security controls. Do not expose secret values. If you find a secret, report only its file, its line, and the fact that it exists.
- Report security weaknesses as risks with remediation direction. Do not write exploits or proofs of concept.
- Stop when evidence is sufficient for the requested scope. Do not pad documents with unsupported sections.

## Evidence Ledger (`docs/ledger.json`)

For legacy or multi-repo scope, maintain `docs/ledger.json`. For a single small system, the ledger is optional, but claims must still be checkable.

Each entry has this structure:

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

### Confidence Levels

| Confidence | Meaning | Handling |
|---|---|---|
| `verified` | Confirmed by reading the code at `src` at the recorded commit | Solid border in diagrams; cited as verified fact |
| `inferred` | Derived from graph analysis, naming, or structure; needs a reading check | Dashed border in diagrams; marked `(inferred)` in prose |
| `doc-only` | Stated in existing documentation but not found in code | ⚠ warning badge; entered into drift register |
| `conflict` | Code and documentation disagree, or code breaks a stated rule | ⚠ warning badge; entered into drift register with diff |
| `static-only` | Found in code, but running in production cannot be confirmed without runtime evidence | ⚠ warning badge; needs APM, config, or trace confirmation |
| `dead-candidate` | No incoming references found; confirm before removing or documenting as live | Grey styling labelled `(dead?)`; verify scheduler/dynamic callers |

### Lifecycle of Ledger Entries

- Retire entries by setting `"status": "superseded"` and referencing the replacement ID. Never delete ledger entries.
- Hotspot findings (type `hotspot`) and scanner findings (type `issue`) are recorded in the ledger as `inferred` until verified from source code.
- Formal validation results (type `model-finding`) remain `inferred` until code inspection confirms the scenario assumptions.

## Drift Register (`docs/drift.md`)

Create `docs/drift.md` containing a structured table of every `conflict` and `doc-only` ledger entry:

```markdown
# Architectural Drift Register

| ID | Documented Statement | Code Reality | Source Location | Severity | Recommended Action |
|---|---|---|---|---|---|
| F-0205 | "Audit logs never contain raw patient PII" | Audit logger serializes full entity payload including SSN | `src/audit/log.py:19` | High | Mask sensitive fields before logger dispatch |
| F-0704 | "Nightly ETL runs at 02:00 UTC" | No cron job or Kubernetes CronJob found in repository | `ml/etl/nightly.sh:1` | Medium | Verify if scheduled in external orchestrator or decommission |
```

