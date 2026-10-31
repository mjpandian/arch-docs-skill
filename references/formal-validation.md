# Formal Validation with TLA+

When documenting architectures with concurrency, retries, distributed coordination, or shared state, diagrams alone cannot demonstrate correctness. Small, bounded TLA+ models provide formal validation of critical design assumptions.

## When to Model

Apply TLA+ modeling specifically to high-risk, non-trivial flows:
- At-least-once queue consumers and worker redelivery handling.
- Distributed locks, leader election, or consensus handoffs.
- Multi-service sagas, two-phase commits, or partial failure recovery.
- Concurrently written database tables without strict ACID isolation.
- Token expiration, revocation, and session invalidation races.

Do not model standard synchronous request-response CRUD flows where concurrency is trivial.

## Bundled Reference Model: `QueueConsumer.tla`

The skill includes reference files in `assets/tla/`:
- `assets/tla/QueueConsumer.tla`: Models workers receiving, processing, and acknowledging messages with simulated crashes and redeliveries.
- `assets/tla/QueueConsumer_unsafe.cfg`: Scenario where `Idempotent = FALSE` (fails safety invariant `AtMostOnce`).
- `assets/tla/QueueConsumer_safe.cfg`: Scenario where `Idempotent = TRUE` (passes within state space bounds).

## Workflow

### 1. Define Invariants in Plain English
Before writing TLA+, formulate the core safety and liveness properties:
- Safety: "A message's business effect is recorded in the store at most once."
- Safety: "No two workers hold the same lock key simultaneously."
- Liveness: "Every submitted task eventually transitions to either COMPLETED or FAILED."

### 2. Formulate Spec & Scenarios
Save specifications in `docs/model/<FlowName>.tla`:
- State assumptions explicitly in the header (`ASSUMPTION A1: ...`).
- Abstract data to small finite sets (e.g., `Msgs = {m1, m2}`, `Workers = {w1, w2}`).
- Model crashes, timeouts, and redeliveries with explicit bounds (`MaxCrashes = 2`).
- Build two configurations per model:
  - `docs/model/<FlowName>_current.cfg`: Current behavior as evidenced in code.
  - `docs/model/<FlowName>_proposed.cfg`: Proposed fix or alternative architecture.

### 3. Run the TLC Checker
Execute TLC using the bundled runner:
```bash
python3 scripts/run_tlc.py docs/model/QueueConsumer.tla docs/model/QueueConsumer_current.cfg --scenario current --results docs/model/results
```
Options:
- `--scenario current|proposed`: Marks whether the run reflects current code or an unmerged proposal.
- `--jar PATH`: Explicit path to `tla2tools.jar`.
- `--download`: Automatically downloads latest `tla2tools.jar` if none is found on the system.

### 4. Interpret Results
- **Violated (`exit code 1`)**: TLC identified a counterexample trace. Trace the state transitions back to source code lines. If the code permits the interleaving, record a `verified` defect/risk with remediation steps.
- **Checked (`exit code 0`)**: TLC explored all reachable states without finding invariant violations. Write: *"TLC found no violation within bounds (N states) under stated assumptions."* Never write "proven" or "safe" — the result is valid only within the model's bounds.
- **Not-Checked (`exit code 2`)**: TLC failed to complete (timeout, syntax error, missing Java runtime). Deliver the specifications as unrun with open questions.

### 5. Diagram Integration
- Add model check results to affected nodes and edges in `docs/diagrams/index.html`.
- Violations in current behavior display a red `✖` badge; passes within bounds display a green `✓`.
- Proposed fixes appear only in the side panel so the diagram never displays an unmerged fix as current reality.

