# C# & .NET Architecture Reference

Guidelines for scanning, analyzing, and documenting C# and .NET codebases across all generations: Azure Functions, Legacy ASP.NET (.NET Framework), and Modern .NET (.NET Core / .NET 5-9+), with strategies for analyzing uncompilable codebases.

## Detect

Identify the .NET generation and architecture from project files and source markers:

- **Build & Project Files**:
  - Modern SDK-style projects: `<Project Sdk="Microsoft.NET.Sdk...">`, `*.sln`, `*.csproj`, `Directory.Build.props`, `Directory.Build.targets`, `global.json`.
  - Legacy MSBuild projects: `<ToolsVersion>`, `<ProductVersion>`, GUID project types (`{349c5851-65df-11da-9384-00065b846f21}` for ASP.NET Web Application), `packages.config`, `web.config`.
  - Azure Functions: `host.json`, `local.settings.json`, `Microsoft.Azure.Functions.Worker` or `Microsoft.NET.Sdk.Functions`.
- **Target Frameworks**:
  - Legacy .NET Framework: `<TargetFrameworkVersion>v4.8</TargetFrameworkVersion>` (or `v2.0`–`v4.7.2`).
  - .NET Core / Modern .NET: `<TargetFramework>net8.0</TargetFramework>` (or `netcoreapp3.1`, `net6.0`, `net7.0`, `net9.0`).
- **File Extensions**: `.cs`, `.fs`, `.vb`, `.aspx`, `.ascx`, `.asmx`, `.svc`, `.cshtml`, `.razor`.

## Entry Points

### 1. Azure Functions
- **In-Process Model** (`Microsoft.NET.Sdk.Functions`):
  - Methods marked `[FunctionName("Name")]`.
  - Trigger bindings: `[HttpTrigger]`, `[TimerTrigger("0 */5 * * * *")]`, `[QueueTrigger("name")]`, `[ServiceBusTrigger("topic")]`, `[CosmosDBTrigger]`, `[EventHubTrigger]`, `[BlobTrigger]`.
  - In-process startup: Class inheriting `FunctionsStartup` with `[assembly: FunctionsStartup(typeof(Startup))]`.
- **Isolated Worker Model** (`Microsoft.Azure.Functions.Worker`):
  - Methods marked `[Function("Name")]`.
  - Trigger bindings with `HttpRequestData` / `HttpResponseData`.
  - Startup in `Program.cs` via `ConfigureFunctionsWorkerDefaults()`.

### 2. Legacy ASP.NET (.NET Framework 2.0–4.8)
- **Web Forms**: `.aspx` files and their code-behind `.aspx.cs` (`Page_Load`, event handlers), User Controls (`.ascx`).
- **Global Application Lifecycle**: `Global.asax` and `Global.asax.cs` (`Application_Start`, `Session_Start`, `Application_BeginRequest`).
- **WCF (Windows Communication Foundation)**: `.svc` files with interfaces marked `[ServiceContract]` and methods marked `[OperationContract]`; endpoints defined in `web.config` under `<system.serviceModel>`.
- **ASMX Web Services**: `.asmx` files, classes with `[WebService]` and methods with `[WebMethod]`.
- **ASP.NET MVC 3–5**: Controllers inheriting `System.Web.Mvc.Controller`; route registration in `App_Start/RouteConfig.cs` (`routes.MapRoute`).
- **ASP.NET Web API 1–2**: Controllers inheriting `System.Web.Http.ApiController`; route configuration in `App_Start/WebApiConfig.cs` (`config.Routes.MapHttpRoute`, `config.MapHttpAttributeRoutes()`).
- **HTTP Modules & Handlers**: Classes implementing `IHttpModule` or `IHttpHandler`, registered in `web.config` under `<system.webServer>/<modules>` and `<handlers>`.

### 3. Modern .NET (.NET Core / .NET 5–9+)
- **Minimal APIs**: `app.MapGet()`, `app.MapPost()`, `app.MapGroup()` in `Program.cs`.
- **Controllers**: Classes marked `[ApiController]` inheriting `ControllerBase` with `[Route]` and `[HttpGet]`/`[HttpPost]`.
- **Razor Pages & Blazor**: `.cshtml.cs` `PageModel` handlers (`OnGet`, `OnPost`), Blazor Server/Wasm components (`.razor`).
- **Worker Services & Background Tasks**: Classes implementing `BackgroundService` (`ExecuteAsync`) or `IHostedService`.
- **Message Consumers**: MassTransit consumers (`IConsumer<T>`), NServiceBus message handlers (`IHandleMessages<T>`).
- **gRPC Services**: Implementations deriving from generated `<Service>.ServiceBase`.
- **Console / Topshelf / Windows Services**: `ServiceBase.Run()`, Topshelf `HostFactory.Run()`.

## Hidden Wiring

- **Dependency Injection**:
  - Modern: `IServiceCollection` registrations (`builder.Services.AddScoped<T, U>()`, `AddSingleton`, `AddTransient`), Scrutor assembly scanning.
  - Legacy: Autofac, Castle Windsor, Unity, StructureMap, Ninject container registration in `Global.asax.cs`.
- **In-Memory Mediator**: MediatR requests (`IRequest<T>`) and handlers (`IRequestHandler<T, R>`) dispatched without compile-time coupling.
- **Middleware & Filter Pipelines**:
  - Modern: `app.UseMiddleware<T>()`, `app.UseAuthentication()`, endpoint filters.
  - Legacy: Action filters (`ActionFilterAttribute`), HTTP Modules (`IHttpModule`) intercepting the ASP.NET pipeline.
- **Reflection & Dynamic Dispatch**: `Assembly.Load()`, `Activator.CreateInstance()`, string-based handler lookups from configuration.

## Config and Secrets

- **Configuration Sources**:
  - Legacy: `web.config` and `app.config` (`<appSettings>`, `<connectionStrings>`, custom `<configSections>`), accessed via `ConfigurationManager.AppSettings["..."]`.
  - Modern: `appsettings.json`, `appsettings.{Environment}.json`, environment variables, accessed via `IConfiguration` and `IOptions<T>`.
  - Azure Functions: `local.settings.json` (`Values` object) for local runs, Application Settings in Azure portal.
- **Secrets Management**:
  - Development: `dotnet user-secrets` (`secrets.json`).
  - Production: Azure Key Vault (`AddAzureKeyVault`), AWS Secrets Manager, HashiCorp Vault.
- **Risks**: Unencrypted connection strings, machine keys, or database credentials stored in `web.config` or `appsettings.json`.

## Data Access

- **ORMs & Mappers**:
  - Entity Framework Core: `DbContext`, `DbSet<T>`, Fluent API `OnModelCreating`.
  - Legacy Entity Framework 6: `.edmx` visual models, `ObjectContext`, `DbContext` in `packages.config`.
  - Linq to SQL: `.dbml` XML schemas.
  - Micro-ORMs: Dapper (`connection.Query<T>()`), PetaPoco, RepoDb.
  - Legacy ADO.NET: `SqlConnection`, `SqlCommand`, `SqlDataAdapter`, `DataSet`, `DataTable`.
- **Schema Migrations**:
  - Modern: EF Core migrations (`dotnet ef migrations add`, `DbContextModelSnapshot.cs`), DbUp.
  - Legacy: EF6 migrations (`Configuration.cs` with `DbMigrationsConfiguration`), RoundhousE, SQL Server Database Projects (`.sqlproj`).
- **Transaction Boundaries**: `using (var tx = db.Database.BeginTransaction())`, `using (var scope = new TransactionScope())`.

## Concurrency

- **Task-Based Asynchronous Pattern (TAP)**: `async Task<T>`, `await`, `Task.WhenAll()`, `ValueTask<T>`, `CancellationToken`.
- **Channels & Threading**: `System.Threading.Channels.Channel<T>` for producer-consumer workflows, `SemaphoreSlim`, `ReaderWriterLockSlim`.
- **Legacy Concurrency**: `ThreadPool.QueueUserWorkItem`, raw `Thread`, APM (`BeginInvoke`/`EndInvoke`), EAP (`BackgroundWorker`).
- **Concurrency Risks**:
  - Sync-over-async deadlocks: Calling `.Result` or `.Wait()` on asynchronous Tasks in legacy ASP.NET or UI SynchronizationContexts.
  - Multi-threaded access to non-thread-safe EF Core `DbContext` or legacy `ObjectContext`.
  - Unobserved task exceptions crashing worker processes.

## Performance

- **Common Bottlenecks**:
  - EF / EF Core client evaluation and N+1 query loops (missing `.Include()` or projection with `.Select()`).
  - Missing `AsNoTracking()` on high-volume read-only queries.
  - Excessive object allocation and string concatenation causing Garbage Collection Gen2 / LOH (Large Object Heap) pauses.
  - Thread pool starvation from blocking synchronous calls on async request threads.
- **Profiling Tools**: `dotnet-trace`, `dotnet-dump`, `dotnet-counters`, BenchmarkDotNet, PerfView.
- **Caching**: `IMemoryCache`, `IDistributedCache` (backed by Redis or SQL Server), legacy `HttpRuntime.Cache`.

## Security

- **Authentication & Authorization**:
  - Modern: ASP.NET Core Identity, JWT Bearer (`AddJwtBearer`), policy-based authorization (`[Authorize(Policy = "...")]`).
  - Legacy: Forms Authentication (`<authentication mode="Forms">`), Windows Authentication, WCF message/transport security.
- **Input Validation**: Data Annotations (`[Required]`, `[StringLength]`), FluentValidation.
- **Common Risks**:
  - Insecure deserialization: `BinaryFormatter` (inherently unsafe), `NetDataContractSerializer`, or Json.NET with `TypeNameHandling.All`.
  - SQL injection via raw SQL string concatenation in ADO.NET or EF (`FromSqlRaw`, `SqlQuery`).
  - Mass assignment over-posting: Binding HTTP requests directly to database entity models instead of dedicated view models / DTOs.
  - XML External Entity (XXE) vulnerabilities in legacy `XmlDocument` or `XmlReader` instances without safe resolver settings.

## Exclusions

- **Generated & Build Artifacts**: `bin/*`, `obj/*`, `*.Designer.cs`, `*.g.cs`, `*.g.i.cs`, `*.AssemblyInfo.cs`, `*.generated.cs`, `packages/*`, `*.csproj.user`, `*.suo`, `.vs/*`, `App_Data/*`, `TestResults/*`.
- **Test Paths**: `*Test.cs`, `*Tests.cs`, `*UnitTest.cs`, `tests/*`, `test/*`, `*.Tests/*`.

## Tools & Compilation-Free Scanning

In real-world legacy codebases and incomplete checkout environments, **compilation often fails**:
- Target frameworks like `net45` or `net472` cannot compile on Linux/macOS build agents.
- Private NuGet feeds or enterprise package sources may be unreachable.
- Missing COM dependencies, local database fixtures, or expired signing certificates.

### Strategy for Handling Compilation Failure

1. **Do Not Let Build Failures Block Analysis**:
   - If `dotnet build` succeeds, run Roslyn analyzer SARIF export.
   - If `dotnet build` fails, **immediately fall back to build-free static analysis**. Do not attempt to fix build environments or alter developer SDK targets.
   - Record compilation blockers and dependency deficiencies as findings in `docs/09-risks-and-migration.md`.

2. **Build-Free Static Analysis (Semgrep)**:
   Semgrep parses C# syntax directly without compiling or resolving assemblies:
   ```bash
   semgrep --config p/csharp --sarif -o semgrep.sarif
   ```

3. **Build-Free Project Extraction**:
   Inspect `.csproj`, `.sln`, and `packages.config` directly as XML/text to derive:
   - Framework versions (`<TargetFramework>`, `<TargetFrameworkVersion>`).
   - Project dependencies and multi-project solution structure (`<ProjectReference>`).
   - External library versions (`<PackageReference>`, `packages.config`).

4. **Build-Free Route & Entry Point Mapping**:
   Use symbol searches and regex pattern matching for attributes:
   - Modern: `\[(Http[A-Za-z]+|Route|FunctionName|Function)\b`
   - Legacy MVC: `\[Route\b`, controllers in `Controllers/` directory, route maps in `App_Start/`.
   - Legacy WCF: `\[ServiceContract\b`, `\[OperationContract\b`, `<service>` in `web.config`.

5. **When Compilation Succeeds (Roslyn Compiler SARIF Export)**:
   ```bash
   dotnet build /p:ErrorLog=artifacts/build.sarif,version=2.1
   ```
   *(Captures all compiler diagnostics, warnings, and Roslyn analyzer rules into SARIF 2.1.0)*

6. **Dotnet Format (Style & Quality Diagnostics)**:
   ```bash
   dotnet format --report artifacts/format.sarif --verify-no-changes
   ```
