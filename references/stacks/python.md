# Python Architecture Reference

Guidelines for scanning, analyzing, and documenting Python codebases.

## Detect

- **Build & Packaging Files**: `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`, `Pipfile`, `poetry.lock`, `environment.yml`.
- **File Extensions**: `.py`, `.pyi`.
- **Framework Signatures**:
  - FastAPI: `FastAPI()`, `@app.get()`, `@app.post()`, `APIRouter()`
  - Django: `manage.py`, `wsgi.py`, `asgi.py`, `urls.py`, `settings.py`, `models.Model`
  - Flask: `Flask(__name__)`, `@app.route()`, `Blueprint()`
  - Celery: `Celery()`, `@app.task`, `shared_task`
  - Data/ML: `pandas`, `numpy`, `torch`, `tensorflow`, `pydantic`

## Entry Points

- **HTTP Handlers**: FastAPI route decorators (`@router.get`, `@router.post`), Flask view functions, Django `urls.py` path routing, Starlette endpoints.
- **Queue Consumers & Tasks**: Celery task declarations, RQ workers, Dramatiq actors, Kafka consumer loops (`confluent-kafka`, `kafka-python`).
- **Scheduled Jobs**: Celery Beat schedules (`CELERY_BEAT_SCHEDULE`), APScheduler jobs, cron wrapper scripts.
- **CLI Commands**: Click command groups (`@click.command`), Typer apps, `argparse` entry points in `__main__.py`.
- **ASGI/WSGI Anchors**: `uvicorn main:app`, `gunicorn wsgi:application`.

## Hidden Wiring

- **Dependency Injection**: FastAPI `Depends()`, Dependency Injector containers, injector modules.
- **Dynamic Imports**: `importlib.import_module()`, `__import__()`, plugin registries mapping string identifiers to classes.
- **Decorators & Wrappers**: Custom route wrappers, middleware decorators modifying request/response context, `@functools.wraps`.
- **Signals**: Django signals (`post_save.connect()`, `@receiver`), Blinker signal dispatches.
- **Metaclasses & Class Registration**: Subclass registration hooks via `__init_subclass__` or custom metaclasses.

## Config and Secrets

- **Settings Files**: `settings.py`, `config.py`, `.env`, `alembic.ini`.
- **Config Libraries**: `pydantic-settings` (`BaseSettings`), `python-dotenv`, Dynaconf, decouple.
- **Secrets Management**: AWS Secrets Manager SDK (`boto3.client('secretsmanager')`), Azure KeyVault SDK, HashiCorp Vault hvac.
- **Risks**: Hardcoded secret fallbacks in `os.getenv("SECRET_KEY", "fallback")`.

## Data Access

- **ORMs & Query Builders**: SQLAlchemy (`Session`, `AsyncSession`, `declarative_base`), Django ORM (`models.Model`, `QuerySet`), Tortoise-ORM, Peewee.
- **Direct Drivers**: `asyncpg`, `psycopg2`, `psycopg`, `pymongo`, `redis-py`.
- **Schema Migrations**: Alembic (`alembic/versions/*.py`), Django migrations (`migrations/*.py`).
- **Transaction Boundaries**: SQLAlchemy `with session.begin():`, Django `@transaction.atomic`.

## Concurrency

- **AsyncIO**: `async def`, `await`, `asyncio.gather()`, `asyncio.create_task()`, asyncio event loop running on uvloop.
- **Multithreading**: `threading.Thread`, `concurrent.futures.ThreadPoolExecutor` (subject to GIL in standard CPython).
- **Multiprocessing**: `multiprocessing.Process`, `concurrent.futures.ProcessPoolExecutor`.
- **Background Workers**: Celery distributed tasks, Dramatiq, RQ.
- **Concurrency Risks**: Blocking I/O calls (e.g. `requests.get()`) executed inside async event loops; shared mutable state across threads without locks.

## Performance

- **Common Bottlenecks**: Synchronous HTTP or database calls in async coroutines; N+1 query patterns in SQLAlchemy/Django ORM (missing `selectinload`, `joinedload`, `select_related`).
- **Profiling Tools**: `cProfile`, Py-Spy, Memray, Scalene.
- **Caching**: Redis clients (`aioredis`, `redis`), Cachetools, Django caching backends.

## Security

- **Authentication**: `python-jose`, `PyJWT`, `passlib`, OAuth2 password bearer schemes in FastAPI.
- **Input Validation**: Pydantic schemas, Marshmallow schemas, Django forms.
- **Common Risks**: SQL injection through raw SQL formatting; pickle deserialization of untrusted payloads (`pickle.loads()`); SSRF via unrestricted `requests.get()` or `httpx.get()`; path traversal in file upload handlers.

## Exclusions

- **Generated & Cache Artifacts**: `*.pyc`, `__pycache__/*`, `.pytest_cache/*`, `.mypy_cache/*`, `.tox/*`, `.venv/*`, `venv/*`, `*.egg-info/*`, `dist/*`, `build/*`.
- **Test Paths**: `tests/*`, `test/*`, `test_*.py`, `*_test.py`, `conftest.py`.

## Tools

Export findings to SARIF 2.1.0 using these verified command options:

- **Bandit** (Security scanner):
  ```bash
  bandit -r . -f custom --format-custom-template @bandit-sarif-formatter -o bandit.sarif
  ```
  *(Requires `pip install bandit-sarif-formatter`)*

- **Ruff** (Linter and code analyzer):
  ```bash
  ruff check --output-format=sarif -o ruff.sarif
  ```

- **Semgrep** (Static analyzer):
  ```bash
  semgrep --config auto --sarif --output semgrep.sarif
  ```

