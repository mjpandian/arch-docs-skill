# Go Architecture Reference

Guidelines for scanning, analyzing, and documenting Go codebases.

## Detect

- **Build & Module Files**: `go.mod`, `go.sum`, `go.work`.
- **File Extensions**: `.go`.
- **Directory Layouts**: Standard Go project layouts (`cmd/*`, `internal/*`, `pkg/*`, `api/*`).
- **Framework Signatures**:
  - Web: Gin (`gin.Default()`), Echo (`echo.New()`), Chi (`chi.NewRouter()`), Fiber, standard `net/http` (`http.HandleFunc`)
  - RPC: gRPC (`google.golang.org/grpc`), Connect RPC, protobuf definitions (`*.pb.go`)
  - Databases: GORM, sqlx, pgx (`github.com/jackc/pgx`), Ent, sqlc

## Entry Points

- **HTTP Handlers**: Gin route registrations (`router.GET`, `router.POST`), Chi route trees, `http.HandlerFunc` implementations.
- **gRPC Services**: Server registrations (`pb.Register<Service>Server(grpcServer, &server{})`).
- **CLI & Commands**: Cobra commands (`*cobra.Command`), Urfave CLI apps located in `cmd/<app>/main.go`.
- **Queue & Stream Consumers**: Sarama / Kafka consumers, RabbitMQ channel listeners, AWS SQS workers.
- **Background Goroutines**: Standalone daemon loops launched in `main.go`.

## Hidden Wiring

- **Dependency Injection**: Google Wire (`wire.go`, `wire_gen.go`), Uber Fx (`fx.New()`, `fx.Provide()`).
- **Middleware Chains**: Standard `func(http.Handler) http.Handler` wrappers or Gin `HandlerFunc` slices.
- **Interface Decoupling**: Structural typing where concrete packages do not explicitly declare interface implementations.
- **Dynamic Handlers**: Reflection dispatch (`reflect.ValueOf`) or factory registries mapping string identifiers to constructors.

## Config and Secrets

- **Config Libraries**: Viper (`viper.SetConfigName()`), envconfig, Cleanenv, standard `os.Getenv()`.
- **Config Formats**: `config.yaml`, `config.json`, `.env`.
- **Secrets Management**: AWS SDK for Go (`aws-sdk-go-v2/service/secretsmanager`), HashiCorp Vault Go API.
- **Risks**: Passing raw configuration structs across packages without encapsulation.

## Data Access

- **ORMs & Generators**: GORM (`gorm.DB`), Ent framework, sqlc (type-safe SQL compiler producing Go code), sqlx.
- **Direct Drivers**: `pgxpool.Pool`, `database/sql` (`*sql.DB`).
- **Migrations**: Golang-migrate (`github.com/golang-migrate/migrate`), Goose (`pressly/goose`).
- **Transaction Boundaries**: `tx, err := db.BeginTx(ctx, &sql.TxOptions{})`.

## Concurrency

- **Goroutines & Channels**: `go worker()`, `chan T`, buffered vs unbuffered channels, `select` statements.
- **Synchronization**: `sync.WaitGroup`, `sync.Mutex`, `sync.RWMutex`, `sync.Once`, `sync.Map`, `atomic` primitives.
- **Context Propagation**: `context.Context` carrying deadlines, cancellation signals, and trace metadata.
- **Concurrency Risks**: Goroutine leaks (hanging on channel send/receive without context cancellation); data races on shared struct pointers; deadlocks across multiple mutex locks.

## Performance

- **Common Bottlenecks**: High garbage collection pressure from heap escapes; missing connection pooling (`SetMaxOpenConns`); channel contention in hot execution loops.
- **Profiling Tools**: `pprof` (`go tool pprof`, `net/http/pprof`), Go execution tracer (`go tool trace`), benchmarks (`go test -bench=. -benchmem`).
- **Caching**: In-memory caches (`go-cache`, BigCache), Redis clients (`go-redis`).

## Security

- **Authentication**: `golang-jwt/jwt`, OAuth2 (`golang.org/x/oauth2`), Gorilla sessions.
- **Input Sanitization**: HTML escaping, SQL parameterization.
- **Common Risks**: SQL injection via string formatting (`fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", id)`); command injection through `os/exec`; SSRF via unrestricted `http.Get()`; unvalidated path traversal in file handlers.

## Exclusions

- **Generated & Build Artifacts**: `vendor/*`, `bin/*`, `*.pb.go`, `*_pb.go`, `wire_gen.go`, `mock_*.go`.
- **Test Paths**: `*_test.go`, `testdata/*`.

## Tools

Export findings to SARIF 2.1.0 using these verified command options:

- **GolangCI-Lint** (Comprehensive aggregator with 40+ linters):
  ```bash
  golangci-lint run --out-format sarif > golangci.sarif
  ```

- **Govulncheck** (Official Go vulnerability scanner):
  ```bash
  govulncheck -format sarif ./... > govulncheck.sarif
  ```

- **Semgrep** (Static security analysis):
  ```bash
  semgrep --config p/golang --sarif -o semgrep.sarif
  ```

