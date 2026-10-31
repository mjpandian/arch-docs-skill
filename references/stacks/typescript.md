# TypeScript & JavaScript Architecture Reference

Guidelines for scanning, analyzing, and documenting TypeScript and Node.js codebases.

## Detect

- **Build & Packaging Files**: `package.json`, `tsconfig.json`, `jsconfig.json`, `pnpm-workspace.yaml`, `lerna.json`, `turbo.json`.
- **Lockfiles**: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb`.
- **File Extensions**: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`.
- **Framework Signatures**:
  - Express: `express()`, `app.use()`, `router.get()`
  - NestJS: `@Controller()`, `@Injectable()`, `@Module()`, `nest-cli.json`
  - Next.js: `next.config.js`, `app/page.tsx`, `pages/api/*.ts`
  - Fastify: `fastify()`, `fastify.register()`
  - React/Vue/Angular: Component trees, state management stores (Redux, Zustand, Pinia).

## Entry Points

- **HTTP Handlers**: Express routers, Fastify routes, NestJS controllers (`@Get`, `@Post`), Next.js App Router route handlers (`route.ts`).
- **WebSockets & Real-Time**: Socket.io server handlers, WS connections, subscriptions in Apollo GraphQL.
- **Queue Consumers**: BullMQ workers (`new Worker('queue', async job => ...)`), SQS consumers, KafkaJS subscribers.
- **Scheduled Tasks**: Node-cron jobs, NestJS `@Cron()`, Agenda tasks.
- **CLI Scripts**: Bin scripts defined in `package.json` (`"bin"`), Commander.js or Yargs scripts.

## Hidden Wiring

- **Dependency Injection**: NestJS DI container (`@Inject()`, token injection), TSyringe, InversifyJS.
- **Dynamic Imports**: `import(path)`, `require(computedPath)`.
- **Middleware Chains**: Express middleware stacks, Koa onion pipeline, NestJS interceptors and guards.
- **Event Emitters**: `EventEmitter` instances firing decoupled events across disparate domains.
- **Monorepo Linking**: Workspace package references (`workspace:*` or npm/yarn workspaces) linking internal packages.

## Config and Secrets

- **Config Files**: `.env`, `.env.local`, `config/*.json`, `dotenv` configs, `process.env`.
- **Config Libraries**: `@nestjs/config`, `dotenv`, `envalid`, `zod` environment parsers.
- **Secrets Management**: AWS Systems Manager / Secrets Manager SDK (`@aws-sdk/client-secrets-manager`), Vault client.
- **Risks**: Exposing server-side secrets in Next.js client bundles (missing `NEXT_PUBLIC_` prefix guard).

## Data Access

- **ORMs & Query Builders**: Prisma (`schema.prisma`, `PrismaClient`), TypeORM (`@Entity()`, `Repository`), Drizzle ORM, MikroORM, Knex.js, Mongoose (`Schema`, `model`).
- **Direct Drivers**: `pg`, `mysql2`, `ioredis`, `mongodb`.
- **Schema Migrations**: `prisma migrate`, TypeORM migrations (`typeorm migration:run`), Knex migrations.
- **Transactions**: Prisma `$transaction()`, TypeORM `dataSource.transaction()`.

## Concurrency

- **Event Loop & Promises**: `async/await`, `Promise.all()`, `Promise.allSettled()`.
- **Worker Threads**: `worker_threads` module (`Worker`, `parentPort`) for CPU-bound computations.
- **Cluster Mode**: Node.js `cluster` module, PM2 process management running multiple fork workers.
- **Concurrency Risks**: Unhandled promise rejections crashing processes; CPU-intensive synchronous loops blocking the single-threaded event loop.

## Performance

- **Common Bottlenecks**: Blocking event loop with heavy crypto, JSON parsing of massive payloads, or regex catastrophic backtracking (ReDoS); unbounded `Promise.all()` saturating database connection pools.
- **Profiling Tools**: Node.js built-in profiler (`node --prof`), Clinic.js (`clinic doctor`, `clinic bubbleprof`), Chrome DevTools inspection.
- **Caching**: Redis (`ioredis`), LRU-cache in-memory caches, Next.js incremental static regeneration (ISR).

## Security

- **Authentication**: Passport.js strategies, NextAuth.js (Auth.js), JWT verification (`jsonwebtoken`, `jose`).
- **Input Validation**: Zod, Yup, Joi, class-validator (`@IsNotEmpty()`, `@IsEmail()`).
- **Common Risks**: Prototype pollution through deep object merges; command injection via `child_process.exec()`; unescaped innerHTML in frontend rendering (XSS); SQL injection through raw Knex/TypeORM query fragments.

## Exclusions

- **Generated & Build Artifacts**: `node_modules/*`, `dist/*`, `build/*`, `.next/*`, `.nuxt/*`, `coverage/*`, `*.tsbuildinfo`, `*.min.js`, `*.map`.
- **Test Paths**: `__tests__/*`, `*.test.ts`, `*.test.tsx`, `*.spec.ts`, `*.spec.tsx`, `*.test.js`, `*.spec.js`, `tests/*`.

## Tools

Export findings to SARIF 2.1.0 using these verified command options:

- **ESLint** (Linting and security rules):
  ```bash
  npx eslint . --format @microsoft/eslint-formatter-sarif --output-file eslint.sarif
  ```
  *(Requires `npm install @microsoft/eslint-formatter-sarif`)*

- **TypeScript Compiler** (Type checking diagnostics):
  ```bash
  npx tsc --noEmit
  ```

- **Semgrep** (Static analyzer):
  ```bash
  semgrep --config p/typescript --sarif -o semgrep.sarif
  ```

