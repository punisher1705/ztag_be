# Zero-Trust API Gateway with AI Anomaly Detection

A hand-rolled API gateway that sits in front of downstream services, handling authentication (JWT + API key strategies), rate limiting, request routing, and audit logging — with a local, open-source LLM agent (LangGraph) that flags anomalous traffic patterns such as credential stuffing or token replay.

Built as a portfolio project to demonstrate production-grade backend engineering: hand-rolled security primitives (not library defaults), SOLID design patterns applied concretely, full observability, and a real Docker → Kubernetes → CI/CD deployment path — using only open-source tooling throughout.

---

## Project Status

> **Current phase:** Walking skeleton complete. Config validation, containerized app boot, health checks, and the local dev stack (MySQL, Redis, Ollama) are working. Auth, rate limiting, gateway routing, and the anomaly agent are in active development.

| Component | Status |
|---|---|
| Config validation (`pydantic-settings`, fail-fast) | ✅ Done |
| Docker Compose stack (gateway, MySQL, Redis, Ollama) | ✅ Done |
| `uv`-based dependency management | ✅ Done |
| Health/readiness endpoints | ✅ Done (readiness check is a placeholder) |
| Swagger/OpenAPI docs (APIFlask) | ✅ Scaffolded, no routes documented yet |
| User model + Alembic migrations | 🔧 In progress |
| JWT auth strategy | 🔧 In progress |
| API key auth strategy | ⬜ Not started |
| Redis-backed rate limiting | ⬜ Not started |
| Middleware pipeline (Chain of Responsibility) | ⬜ Not started |
| Gateway routing + stub downstream services | ⬜ Not started |
| LangGraph anomaly detection agent | ⬜ Not started |
| Prometheus / Grafana / Loki / Tempo | ⬜ Not started |
| Kubernetes manifests + Helm chart | ⬜ Not started |
| GitHub Actions CI/CD | ⬜ Not started |
| Test suite (>70% coverage target) | ⬜ Not started |

---

## Architecture

```
                    ┌─────────────────────────────┐
   Client ────────► │   Zero-Trust API Gateway     │
                    │  (Flask/APIFlask)            │
                    │                              │
                    │  Middleware chain:           │
                    │  1. Request context          │
                    │  2. Auth (Strategy pattern)  │
                    │  3. Rate limit (Redis)       │
                    │  4. Anomaly check (async)     │
                    │  5. Route → downstream        │
                    └───────────┬──────────────────┘
                                │
                 ┌──────────────┼───────────────┐
                 ▼                              ▼
         ┌───────────────┐             ┌───────────────┐
         │ Inventory Svc  │             │ Orders Svc     │
         │ (stub service) │             │ (stub service) │
         └───────────────┘             └───────────────┘

   Supporting infrastructure:
   - MySQL       → users, api_keys, audit_log
   - Redis       → rate-limit counters, token blacklist, request-log window
   - Ollama      → local LLM inference for the anomaly-detection agent
   - Prometheus, Grafana, Loki, Tempo → observability stack
```

Full HLD/LLD notes and design-decision rationale live in [`docs/architecture.md`](docs/architecture.md) and [`docs/adr/`](docs/adr/).

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Flask + APIFlask (adds OpenAPI/Swagger generation) |
| ORM | SQLAlchemy + Alembic migrations |
| Database | MySQL 8 |
| Cache / rate-limit store | Redis |
| Auth | Hand-rolled JWT (PyJWT) + API key strategy — no Auth0/Keycloak |
| AI / Agents | LangChain + LangGraph, served by Ollama (Llama 3.1 8B / Mistral 7B) |
| Observability | Prometheus, OpenTelemetry, Grafana, Loki, Tempo |
| Package management | [`uv`](https://docs.astral.sh/uv/) |
| Containerization | Docker (multi-stage builds, non-root user) |
| Orchestration | Kubernetes (k3d/kind locally → EKS), Helm |
| CI/CD | GitHub Actions |
| Testing | pytest, pytest-cov |

Everything above is open-source; no proprietary APIs (Claude/OpenAI/Datadog/Auth0/AWS Secrets Manager) are required to run this project locally. See [ADR-0005](docs/adr/0005-open-source-only-stack.md) for the full substitution rationale.

## SOLID & Design Pattern Mapping

| Principle / Pattern | Where it lives |
|---|---|
| Strategy | `app/auth/base_strategy.py` — `AuthStrategy` interface with `JWTAuthStrategy` and `APIKeyAuthStrategy` implementations |
| Chain of Responsibility | `app/middleware/pipeline.py` — ordered, short-circuiting request pipeline |
| Open/Closed | Adding a new downstream service is a config entry (`DOWNSTREAM_SERVICES` env var), not a code change |
| Single Responsibility | `app/core/config.py` is the only place that reads environment variables; each middleware stage does exactly one job |
| Dependency Inversion | Routes depend on the `AuthStrategy` interface, never a concrete implementation directly |
| Repository | `app/repositories/` wraps all SQLAlchemy queries — routes and services never touch the ORM directly |

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (for running things locally without Docker, e.g. quick config checks)
- Python 3.11+

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd zero-trust-gateway
cp .env.example .env
```

Generate real secrets and paste them into `.env` (don't leave the placeholder values):

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"   # run twice — once each for APP_SECRET_KEY and JWT_SECRET_KEY
```

### 2. Start the stack

```bash
make up
```

This builds the gateway image (via `uv sync` inside a multi-stage Dockerfile) and starts MySQL, Redis, Ollama, and the gateway itself. The gateway waits for MySQL and Redis to report healthy before starting.

### 3. Pull the local LLM (first run only, ~4.7GB)

```bash
make ollama-pull
```

### 4. Verify it's running

```bash
curl http://localhost:5001/healthz
```

Expected:
```json
{"status": "ok", "service": "zero-trust-gateway", "env": "development"}
```

Swagger UI: [http://localhost:5001/docs](http://localhost:5001/docs)

### Local development without Docker (fast iteration)

```bash
make sync            # uv sync — installs deps into a local .venv
make check-config     # sanity-checks .env loading, no containers needed
```

---

## Common Commands

Run `make help` to see all available targets. Highlights:

| Command | Purpose |
|---|---|
| `make up` / `make down` | Start / stop the full stack |
| `make logs-app` | Tail the gateway's logs |
| `make shell` | Bash into the gateway container |
| `make db-shell` | MySQL shell |
| `make redis-cli` | Redis CLI |
| `make migrate` | Apply pending Alembic migrations |
| `make migrate-create msg="..."` | Generate a new migration |
| `make test` / `make test-cov` | Run tests / tests with coverage report |
| `make lint` / `make format` | Ruff lint / auto-format |
| `make clean` | Stop containers **and delete volumes** (wipes local DB/Redis data) |

---

## Project Structure

```
zero-trust-gateway/
├── app/
│   ├── core/          # config, logging, security helpers, telemetry — no business logic
│   ├── db/            # SQLAlchemy engine/session setup
│   ├── models/         # ORM models only
│   ├── schemas/        # request/response validation (doubles as OpenAPI spec source)
│   ├── repositories/   # Repository pattern — wraps all DB queries
│   ├── auth/           # Strategy pattern — JWT & API key auth implementations
│   ├── middleware/     # Chain of Responsibility — request pipeline
│   ├── gateway/        # routing/proxying to downstream services
│   ├── ai/             # LangGraph anomaly-detection agent
│   ├── api/            # Flask Blueprints (thin controllers)
│   └── services/       # business logic orchestration
├── downstream_services/ # stub services the gateway proxies to
├── migrations/          # Alembic
├── tests/               # unit / integration / ai
├── docker/gateway/      # Dockerfile
├── k8s/                 # raw Kubernetes manifests
├── helm/                # Helm chart
├── monitoring/          # Prometheus/Grafana/Loki/Tempo configs
├── docs/adr/            # Architecture Decision Records
├── docker-compose.yml
├── pyproject.toml       # dependencies (uv)
├── uv.lock
├── Makefile
└── .env.example
```

## API Documentation

Interactive Swagger/OpenAPI docs are generated automatically by APIFlask — no hand-maintained API reference to keep in sync:

- **Local:** [http://localhost:5001/docs](http://localhost:5001/docs)
- **Raw spec:** [http://localhost:5001/openapi.json](http://localhost:5001/openapi.json)

## Testing

```bash
make test          # full suite
make test-unit      # unit tests only
make test-cov       # with coverage report (target: >70% on app/core and app/middleware)
```

## Deployment

Local → Docker Compose (this repo).
Staging/Production → Kubernetes, via either raw manifests (`k8s/`) or the Helm chart (`helm/zero-trust-gateway/`), deployed through the GitHub Actions pipeline (`.github/workflows/`).

See [`docs/architecture.md`](docs/architecture.md) for the full deployment pipeline diagram (lint → test → build → push → staged rollout).

## Observability

- **Metrics:** Prometheus scrapes `/metrics`; Grafana dashboards under `monitoring/grafana/dashboards/` show request rate, error rate, latency percentiles, and anomaly-flag rate.
- **Logs:** structured JSON, correlated by request ID, shipped to Loki.
- **Traces:** OpenTelemetry spans exported to Tempo.

Once running locally: Grafana at `http://localhost:3000`, Prometheus at `http://localhost:9090`.

## Security Notes

- Passwords are bcrypt-hashed; JWT secrets and DB credentials are never hardcoded or logged.
- Anomaly-detection findings are **surfaced to an admin endpoint, not auto-executed** — actions require human approval. See [ADR-0003](docs/adr/0003-human-in-the-loop-anomaly-actions.md).
- `.env` is gitignored; secrets management for staging/production uses HashiCorp Vault or Kubernetes Secrets, not plaintext files.

## Architecture Decision Records

Key design tradeoffs are documented in [`docs/adr/`](docs/adr/), including:
- Why hand-rolled JWT over Keycloak/Auth0
- Why Redis for rate limiting
- Why anomaly-detection actions require human approval
- Why the auth layer uses the Strategy pattern
- Why the stack is fully open-source

## Contributing

This is a personal portfolio project, not currently open for external contributions. Feel free to fork for your own learning.

## License

MIT