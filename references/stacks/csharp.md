# C# & .NET Architecture Reference

Guidelines for scanning, analyzing, and documenting C# and .NET codebases.

## Detect

- **Build & Project Files**: `*.sln`, `*.csproj`, `*.fsproj`, `Directory.Build.props`, `Directory.Build.targets`, `global.json`, `nuget.config`.
- **File Extensions**: `.cs`, `.fs`.
- **Framework Signatures**:
  - ASP.NET Core: `WebApplication.CreateBuilder()`, `Program.cs`, `Startup.cs`, `[ApiController]`, `[Route]`, Minimal APIs (`app.MapGet()`, `app.MapPost()`)
  - Entity Framework Core: `DbContext`, `DbSet<T>`, `OnModelCreating`, `appsettings.json`
  - WCF / Legacy .NET Framework: `web.config`, `*.svc`, `[ServiceContract]`
  - Messaging: MassTransit, MediatR (`IRequest<T>`, `INotificationHandler<T>`), NServiceBus

## Entry Points

- **HTTP Controllers & Minimal APIs**: `[ApiController]` controller actions, Minimal API route endpoints (`app.MapGet()`, `app.MapPost()`).
- **Background Workers**: `BackgroundService` (`ExecuteAsync`), `IHostedService` implementations, Hangfire recurring jobs.
- **Message Consumers**: MassTransit consumers (`IConsumer<T>`), Azure Service Bus / RabbitMQ message pumps.
- **gRPC Services**: Classes deriving from generated `<Service>.ServiceBase`.
- **CLI Commands**: CommandLineParser, System.CommandLine apps.

## Hidden Wiring

- **Dependency Injection**: `IServiceCollection` registrations (`AddScoped`, `AddTransient`, `AddSingleton`), Autofac, Scrutor assembly scanning.
- **In-Memory Mediator**: MediatR requests and notifications where senders and handlers have no direct static reference.
- **Middleware Pipeline**: `app.UseMiddleware<T>()`, `app.UseAuthentication()`, custom `IMiddleware` implementations.
- **Reflection & Dynamic Loading**: `Assembly.Load()`, `Type.GetType()`, dependency injection via string-based configuration keys.

## Config and Secrets

- **Config Files**: `appsettings.json`, `appsettings.{Environment}.json`, `launchSettings.json`.
- **Config Providers**: `IConfiguration`, Options pattern (`IOptions<T>`, `IOptionsSnapshot<T>`).
- **Secrets Management**: `dotnet user-secrets` in development; Azure Key Vault provider, AWS Secrets Manager provider, HashiCorp Vault.
- **Risks**: Unencrypted connection strings committed in `appsettings.json`.

## Data Access

- **ORMs & Mappers**: Entity Framework Core (`DbContext`), Dapper (`connection.Query<T>()`), NHibernate, Linq2DB.
- **Direct ADO.NET**: `SqlConnection`, `NpgsqlConnection`, `SqlCommand`.
- **Migrations**: EF Core Migrations (`dotnet ef migrations add`, `DbContextModelSnapshot.cs`).
- **Transactions**: `IDbContextTransaction`, `TransactionScope` distributed transactions.

## Concurrency

- **Task-Based Asynchronous Pattern (TAP)**: `async Task<T>`, `await`, `Task.WhenAll()`, `ValueTask<T>`, `CancellationToken`.
- **Threading & Synchronization**: `lock`, `SemaphoreSlim`, `Monitor`, `Channel<T>` for producer-consumer queues.
- **Concurrency Risks**: Sync-over-async deadlocks (`.Result` or `.Wait()` on asynchronous Tasks); unobserved task exceptions; multi-threaded access to non-thread-safe EF Core `DbContext`.

## Performance

- **Common Bottlenecks**: Blocking thread pool threads with synchronous I/O; EF Core client evaluation / N+1 queries (missing `.Include()`); missing `AsNoTracking()` on read-only queries; excessive allocations causing GC Gen2 pressure.
- **Profiling Tools**: `dotnet-trace`, `dotnet-dump`, `dotnet-counters`, BenchmarkDotNet.
- **Caching**: `IMemoryCache`, `IDistributedCache` (backed by Redis or SQL Server).

## Security

- **Authentication & Authorization**: ASP.NET Core Identity, JWT Bearer (`AddJwtBearer`), cookie authentication, policy-based authorization (`[Authorize(Policy = "...")]`).
- **Data Protection**: ASP.NET Core Data Protection API (key rings).
- **Common Risks**: Insecure deserialization via `BinaryFormatter` or unconstrained `TypeNameHandling` in Json.NET; SQL injection via raw SQL strings in EF Core (`FromSqlRaw`); mass assignment over-posting on entity models without DTOs.

## Exclusions

- **Generated & Build Artifacts**: `bin/*`, `obj/*`, `*.Designer.cs`, `*.g.cs`, `*.g.i.cs`, `*.AssemblyInfo.cs`, `*.generated.cs`, `packages/*`, `*.csproj.user`, `TestResults/*`.
- **Test Paths**: `*Test.cs`, `*Tests.cs`, `*UnitTest.cs`, `tests/*`, `test/*`.

## Tools

Export findings to SARIF 2.1.0 using these verified command options:

- **MSBuild / Roslyn Compiler Analyzers** (Native .NET compiler error log):
  ```bash
  dotnet build /p:ErrorLog=artifacts/build.sarif,version=2.1
  ```
  *(Captures all compiler warnings, security rules, and Roslyn analyzer violations in SARIF 2.1.0)*

- **Dotnet Format** (Formatting and code style analyzer):
  ```bash
  dotnet format --report artifacts/format.sarif --verify-no-changes
  ```

- **Semgrep** (Static security analysis):
  ```bash
  semgrep --config p/csharp --sarif -o semgrep.sarif
  ```

