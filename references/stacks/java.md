# Java & Kotlin Architecture Reference

Guidelines for scanning, analyzing, and documenting Java and Kotlin codebases.

## Detect

- **Build & Project Files**: `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `gradlew`, `mvnw`.
- **File Extensions**: `.java`, `.kt`, `.kts`.
- **Framework Signatures**:
  - Spring Boot: `@SpringBootApplication`, `@RestController`, `@Service`, `@Repository`, `application.properties`, `application.yml`
  - Jakarta EE / Quarkus / Micronaut: `@ApplicationScoped`, `@Path`, Quarkus extensions
  - JPA / Hibernate: `@Entity`, `@Table`, `EntityManager`, `JpaRepository`

## Entry Points

- **HTTP Controllers**: Spring Web `@RestController` / `@RequestMapping`, JAX-RS / Quarkus `@Path`, Ktor routing functions.
- **Queue & Event Consumers**: Spring Kafka (`@KafkaListener`), Spring AMQP (`@RabbitListener`), JMS message listeners (`@JmsListener`).
- **Scheduled Tasks**: Spring `@Scheduled(cron = "...")`, Quartz jobs.
- **Batch Processing**: Spring Batch `Job`, `Step`, `ItemReader`, `ItemWriter`.
- **CLI & Application Runners**: `CommandLineRunner`, `ApplicationRunner`, Picocli applications.

## Hidden Wiring

- **Dependency Injection**: Spring IoC container (`@Autowired`, constructor injection), Google Guice, Dagger.
- **Aspect-Oriented Programming (AOP)**: `@Aspect`, custom annotations triggering Spring `@Transactional`, `@Cacheable`, `@Async` via proxy mechanisms.
- **Reflection & Bean Discovery**: Classpath scanning, Spring `ApplicationContext.getBean()`, Java ServiceLoader (`META-INF/services/*`).
- **Event Bus**: Spring `ApplicationEventPublisher` and `@EventListener` decoupled dispatchers.

## Config and Secrets

- **Config Files**: `application.yml`, `application.properties`, `bootstrap.yml`, `logback.xml`.
- **Configuration Mechanisms**: Spring `@ConfigurationProperties`, `@Value("${...}")`, MicroProfile Config.
- **Secrets Management**: Spring Cloud Vault, AWS Secrets Manager Starter, Azure Key Vault starter.
- **Risks**: Storing plaintext database credentials or keystore passwords in version-controlled `application.properties`.

## Data Access

- **ORMs & Frameworks**: Spring Data JPA / Hibernate (`JpaRepository`, `CrudRepository`), MyBatis (`@Mapper`), jOOQ, R2DBC for reactive access.
- **Direct Drivers**: JDBC `DataSource`, `JdbcTemplate`.
- **Migrations**: Flyway (`src/main/resources/db/migration/*.sql`), Liquibase (`changelog.xml` / `.yaml`).
- **Transaction Boundaries**: `@Transactional(rollbackFor = Exception.class)`.

## Concurrency

- **Threads & Thread Pools**: `ExecutorService`, Spring `@Async`, `CompletableFuture<T>`, Virtual Threads (Project Loom / Java 21+).
- **Kotlin Coroutines**: `suspend fun`, `CoroutineScope`, `Dispatchers.IO`, `Flow<T>`.
- **Reactive Streams**: Project Reactor (`Mono<T>`, `Flux<T>`), RxJava.
- **Concurrency Risks**: Thread pool starvation from blocking database calls on reactive or common thread pools; race conditions on mutable Spring singleton beans.

## Performance

- **Common Bottlenecks**: Hibernate N+1 query problem (missing `join fetch` or `@EntityGraph`); excessive object allocation triggering Garbage Collection pauses; blocking calls inside reactive reactive web filters.
- **Profiling Tools**: JDK Flight Recorder (JFR) & JDK Mission Control, VisualVM, async-profiler.
- **Caching**: Spring Cache abstraction (`@Cacheable`, `@CacheEvict`) backed by Caffeine, Redis, or Ehcache.

## Security

- **Authentication & Security**: Spring Security (`SecurityFilterChain`, `@PreAuthorize("hasRole('...')")`), Shiro, Keycloak adapters.
- **Input Validation**: Jakarta Bean Validation (`@NotNull`, `@Size`, `@Valid`).
- **Common Risks**: Insecure deserialization via Java native serialization (`ObjectInputStream`); SQL injection through string concatenation in HQL or native JPA queries; Log4j style JNDI injection (`Log4Shell`).

## Exclusions

- **Generated & Build Artifacts**: `target/*`, `build/*`, `.gradle/*`, `gradle/wrapper/*`, `*/generated-sources/*`, `*.class`, `*.jar`, `*.war`, `*.iml`, `.idea/*`.
- **Test Paths**: `src/test/*`, `*Test.java`, `*Tests.java`, `*TestCase.java`, `*Test.kt`, `*Tests.kt`.

## Tools

Export findings to SARIF 2.1.0 using these verified command options:

- **PMD** (Static code and security analysis):
  ```bash
  pmd check -f sarif -r pmd-report.sarif -d src/main/java -R category/java/bestpractices.xml,category/java/security.xml
  ```
  *(Supported natively in PMD 6.31.0+ and PMD 7.x via `-f sarif`)*

- **SpotBugs** (Bug and vulnerability detector):
  ```bash
  mvn spotbugs:check
  ```
  *(With the SpotBugs SARIF plugin configured in `pom.xml`)*

- **Semgrep** (Static security analysis):
  ```bash
  semgrep --config p/java --sarif -o semgrep.sarif
  ```

