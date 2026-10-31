# Legacy Systems and Multi-Repo Estates

Documenting legacy, brownfield, or distributed architectures introduces challenges beyond single-service greenfield repositories.

## Non-HTTP Entry Points

Critical system behavior in legacy applications often lives outside standard REST/HTTP controllers:
- **Scheduled Jobs**: Unix crontabs, Celery beats, Quartz schedulers, Windows Scheduled Tasks, Spring `@Scheduled`.
- **Message Consumers**: RabbitMQ, Kafka consumers, SQS pollers, Redis pub/sub listeners, JMS message-driven beans.
- **Batch Processing & ETL**: Standalone Python scripts, bash wrappers, database stored procedures, SSIS packages.
- **Data Triggers & Events**: PostgreSQL triggers, CDC streams (Debezium), file-drop watchers.

Examine deployment descriptors, container manifests, and systemd units to capture all active entry points.

## Hidden Wiring & Dynamic Dispatch

Legacy architectures frequently rely on runtime wiring that static call graphs cannot resolve directly:
- **Dependency Injection**: Spring XML configurations, Castle Windsor, Guice, ASP.NET Core service collections.
- **Reflection & Plugin Loaders**: `Class.forName()`, `Assembly.Load()`, Python `importlib.import_module()`.
- **Dynamic Routing & Strategy Patterns**: Handlers registered via database lookups or dictionary dispatch tables.
- **Feature Flags**: Flags dynamically disabling execution paths. Mark flagged or conditional paths explicitly.

Mark unconfirmed runtime bindings as `static-only` unless configuration or runtime evidence confirms active deployment.

## Shared Database Coupling

In multi-repo systems, database coupling is frequently the most critical modernization blocker:
- Map every shared table across all repositories.
- For each table, determine which repository owns write operations, which execute migrations, and which perform read-only queries.
- Identify implicit transactional dependencies (e.g., Service A writes a row with `status='PENDING'` that Service B polls and updates).
- Document shared database links as contract edges in the cross-repo map (`diagrams/index.html`).

## Contract-Based Cross-Repo Mapping

Derive cross-repository links strictly from verified contracts:
1. **API Specifications**: OpenAPI/Swagger specs, gRPC `.proto` definitions, GraphQL schemas.
2. **Topic & Event Schemas**: Explicit message payload types and queue/topic names matched on both producer and consumer sides.
3. **Database Schemas**: Shared migration files, foreign key references across shared tables.
4. **Shared Client Libraries**: SDKs published by producer repos and imported by consumer repos.

Never infer a cross-repo connection based on name similarity or intuition alone. If a connection is suspected but unverified, mark it `(inferred)`.

## Git History for Churn and Ownership

Use git history across each repository:
- **Knowledge Risk**: Identify high-churn modules where >80% of changes were authored by a single contributor who is no longer active.
- **Shared Tickets**: Cross-reference Jira/issue keys in commit subjects across repos using `scripts/hotspots.py` to identify hidden cross-repository co-dependencies.

