# 🛡️ LLM-Inspector

A self-hosted, multi-threaded/async **MITM (Man-in-the-Middle) security proxy purpose-built for LLM traffic**, built as a hands-on learning project to understand network programming, proxy internals, and ML-assisted security analysis — from raw TCP sockets all the way up to a Dockerized, database-backed system with a web dashboard.

Unlike a generic web-traffic proxy, LLM-Inspector is designed to sit in front of LLM/AI-API traffic (chat completion-style requests, prompts, model parameters) and catch attacks that specifically target LLM applications — most notably **prompt injection**, delivered either in the request body or smuggled through HTTP headers. It intercepts live HTTP traffic, parses and logs it, scores it for security risk using a combination of rule-based detectors and machine-learning classifiers trained specifically for LLM attack patterns, and lets a human operator pause, inspect, modify, forward, or drop each request before it reaches the target LLM endpoint.

---

## 📖 Table of Contents

- [Project Philosophy](#-project-philosophy)
- [Architecture Overview](#-architecture-overview)
- [Version Roadmap](#-version-roadmap--history)
- [Repository Structure](#-repository-structure)
- [Core Components](#-core-components)
- [Database Schema](#-database-schema)
- [Security Detection Engine](#-security-detection-engine)
- [Frontend Dashboard](#-frontend-dashboard)
- [Getting Started](#-getting-started)
- [Development Workflow](#-development-workflow)
- [Architecture Decisions](#-architecture-decisions)
- [Archive / Learning Milestones](#-archive--learning-milestones)

---

## 🎯 Project Philosophy

This is a personal learning lab rather than a production tool. It was deliberately built bottom-up: starting from a raw custom TCP protocol, then a plain socket-based HTTP inspector, then a real forward proxy, then a request/response interception layer, and finally a full-stack system with a database, a FastAPI backend, and a Vue dashboard — with LLM-specific threat detection layered on top once the core proxy plumbing was solid.

The project deliberately scopes its AI-security detection to the **OWASP LLM Top 10** risks that are actually detectable from the text of a single HTTP request — primarily **LLM01: Prompt Injection**, with partial coverage of LLM02 (Sensitive Information Disclosure) and LLM07 (System Prompt Leakage). Architecture-level risks (supply chain, model poisoning, excessive agency, etc.) are explicitly out of scope, since they can't be inferred from a single request's content.

Key design decisions were made by the project owner with AI tools used as a *consultant* (architecture discussions, debugging help, code review) rather than as the primary code generator — the intent is to actually learn the underlying concepts (sockets, threading vs. asyncio, HTTP framing, connection pooling, containerization) rather than just ship a working artifact.

---

## 🏗️ Architecture Overview

At a high level, the system is composed of four cooperating services (see `docker-compose.yml`):
<img width="500" height="274" alt="llm_inspector_architecture" src="https://github.com/user-attachments/assets/d43e75a6-947d-46a7-b286-5e51c77ee1d6" />

The proxy itself is built on top of **mitmproxy** (`mitm_addon.py`), which intercepts every HTTP request — typically a request to an LLM/AI API — reconstructs it into a custom lightweight `HTTPRequest` object, runs it through the LLM-focused security analysis pipeline, persists it to PostgreSQL, and — unless the dashboard is in "bypass" mode — pauses the request in an `intercept_queue` until a human operator releases it (forward, drop, or forward-with-modifications) via the FastAPI/WebSocket dashboard or the CLI dashboard.

The naming (`LLMInspectorAddon`, `logger = logging.getLogger("LLMinspector")`) throughout the codebase reflects this focus: the proxy isn't a general-purpose Burp-style toolkit, it's an inspection layer specifically watching for AI/LLM-targeted attacks in transit.

---

## 🗺️ Version Roadmap & History

The `readme.md` at the repo root documents an explicit, versioned evolution of the project. You can check out any tagged release to see how the architecture progressed:

- [x] **v1.0.0 — HTTP Inspector**: Single-threaded socket listener that captures, parses, and logs raw HTTP requests to a local JSON file, with a first pass at a rule-based security analyzer.
- [x] **v2.0.0 — MITM Forward Proxy**: True forward proxy with dynamic upstream target routing, multi-threaded concurrency (thread-per-client), infinite-loop prevention, and bi-directional streaming.
- [x] **v3.0.0 — Request/Response Modifier**: Adds the interception mechanism — requests can be paused, modified, or dropped before being forwarded.
- [ ] **v4.0.0 — Dashboard (FastAPI)**: Web interface for live logs, security statistics, and an async intercept UI. *(In progress / superseded in practice by the current FastAPI + Vue dashboard.)*
- [x] **v5.0.0 — Database & Containerization (current)**: Migrates storage from JSON logs to PostgreSQL, and containerizes the full stack (proxy, API, CLI dashboard, frontend, database) with Docker Compose.
- [ ] **v6.0.0 — HTTPS Interception (SSL/TLS)**: `CONNECT` tunneling and dynamic certificate generation to inspect encrypted traffic (needed to inspect traffic to most real-world hosted LLM APIs, which run over TLS).
- [ ] **v7.0.0 — AI Security Engine**: Deeper native LLM-based scanning for prompt injection and advanced threat analysis, building on the ML detector groundwork already shipped in `inspector_tools/ml_analysis`.

> Note: the top-level `mitm_addon.py`/database-backed implementation is the actively developed system. The `archive/` folder preserves earlier, now-superseded implementations (raw sockets, single-file inspector) as a record of the learning path, from before the project's focus narrowed specifically to LLM traffic.

---

## 📁 Repository Structure

```
.
├── archive/                       # Earlier learning milestones (superseded implementations)
│   ├── FastAPI_intro/             # First experiments with FastAPI
│   ├── TCP_CHAT_SERVER(v0)/       # Foundational custom-protocol TCP socket server/client
│   ├── inspector_server.py        # Early asyncio-based HTTP inspector (pre-mitmproxy)
│   ├── runner.py / test.py        # Misc scratch/test scripts
│
├── dashboard/                     # Web + CLI operator dashboards
│   ├── templates/index.html
│   ├── api.py                     # FastAPI app: REST + WebSocket endpoints
│   └── app.py                     # Terminal/CLI interceptor dashboard
│
├── database/
│   ├── schema/tables.sql          # PostgreSQL schema (DDL)
│   └── db_manager.py              # Async psycopg3 connection pool + all queries
│
├── docs/
│   ├── architecture-decisions.md  # ADRs / engineering journal
│   └── dev-notes-fa.md            # Developer notes (Persian)
│
├── frontend/                      # Vue 3 + Vite + Tailwind dashboard SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── HeaderBar.vue
│   │   │   ├── PacketTable.vue
│   │   │   ├── PacketInspector.vue
│   │   │   ├── BottomConsole.vue      # Security risk console (score ring, flags)
│   │   │   └── AIAttackerModal.vue    # Placeholder for a future AI payload generator
│   │   └── App.vue
│   └── Dockerfile
│
├── inspector_tools/                # Core parsing + security detection library
│   ├── HTTPRequest.py              # Raw-text → structured HTTP request parser
│   ├── detector.py                 # Rule-based WebSecurityScanner (XSS/SQLi patterns)
│   ├── logger.py                   # JSONLogger for local request logging
│   ├── model_loader.py             # Loads pre-trained ML models at proxy startup
│   └── ml_analysis/                # ML + combined-signal detection subsystem
│       ├── analyzer.py             # SecurityAnalyzer — orchestrates all signals
│       ├── ml_predictors.py        # Runs the header/body ML classifiers
│       ├── combined_attack_rules.py# Deterministic cross-field checks (e.g. model-override conflicts)
│       ├── security_context.py     # SecurityContext data object (risk score, flags, patterns)
│       └── readme.md               # Design rationale for the combined-rules subsystem
│
├── mitm_addon.py                   # Main mitmproxy addon — the heart of the proxy
├── docker-compose.yml              # Orchestrates proxy, dashboard API, frontend, Postgres
├── Dockerfile                      # Image for the proxy / backend services
├── requirements.txt
├── .env.example
└── readme.md                       # Original project readme (roadmap + dev process)
```

---

## 🧩 Core Components

### `mitm_addon.py` — the proxy engine
A `mitmproxy` addon class (`LLMInspectorAddon`) that hooks into the `request` event for every flow passing through the proxy:

1. Skips `CONNECT` requests (no HTTPS interception yet — see roadmap v6).
2. Reconstructs the raw HTTP message from the mitmproxy `flow` object and parses it with the custom `HTTPRequest` class.
3. Runs the request through `SecurityAnalyzer` (rule-based + ML + combined-signal detection).
4. Logs the request locally via `JSONLogger` and persists it to PostgreSQL (`raw_requests` table).
5. Checks the global **dashboard pause state**: if the dashboard is *not* paused, the request is queued in `intercept_queue` and execution blocks (via an `asyncio.Event`) until a human operator releases it from the dashboard.
6. Notifies connected dashboard clients in real time over the packet WebSocket.

### `inspector_tools/HTTPRequest.py` — HTTP parser
A lightweight, dependency-free HTTP/1.x request parser built on top of a custom `CaseInsensitiveDict` for header lookups. Extracts method, path, HTTP version, query parameters, cookies, headers, body, and resolves the proxy's upstream target host/port from the `Host` header.

### `inspector_tools/detector.py` — rule-based scanner
A `WebSecurityScanner` that performs pattern-based detection for classic web attacks (XSS, SQL injection, etc.) against the parsed request.

### `database/db_manager.py` — async data layer
Uses **`psycopg3`** with `psycopg_pool.ConnectionPool` (not an ORM — see [Architecture Decisions](#-architecture-decisions)) to manage all persistence:
- Saving raw and modified requests
- Managing the intercept queue and its pending/forwarded/dropped states
- An `asyncio.Event`-based registry (`intercept_events`) that lets a blocked proxy coroutine wait asynchronously for a dashboard decision without polling
- Toggling and reading the global dashboard pause/bypass state
- Request/statistics counters

### `dashboard/api.py` — FastAPI backend
Exposes REST endpoints and two WebSocket channels (`/ws/status` for pause-state updates, and a packet channel for live traffic) that the Vue frontend subscribes to for real-time updates. Uses a `ConnectionManager` to broadcast messages to all connected dashboard clients.

### `dashboard/app.py` — CLI dashboard
A terminal-based alternative to the web dashboard for quickly polling pending intercepted requests, inspecting them, and releasing them — including rebuilding the raw HTTP bytes (with a correctly recalculated `Content-Length`) when a request body has been edited.

---

## 🗄️ Database Schema

PostgreSQL schema (`database/schema/tables.sql`), five tables:

| Table | Purpose |
|---|---|
| `raw_requests` | Every intercepted request as originally received: method, host, port, path, headers (JSONB), and raw bytes (BYTEA). |
| `intercept_queue` | Tracks the pending/forwarded/dropped status of a request while it's held for operator review. One row per request (`FK → raw_requests`, cascading delete). |
| `modified_requests` | Stores the operator-edited version of a request (method, path, headers, raw bytes) if it was changed before forwarding. |
| `dashboard_status` | Single-row table (`id = 1`, enforced by a CHECK constraint) holding the global pause/bypass toggle for the proxy. |
| `security_analyses` | Persisted security-analysis results per request: risk score, risk level, matched patterns, and flags (all JSONB). |

---

## 🔎 Security Detection Engine

The `inspector_tools/ml_analysis` package combines **three independent detection signals** into a single risk decision per request, purpose-built for LLM attack patterns rather than generic web attacks (see its own `readme.md` for the full rationale):

1. **Rule-based detection** (`inspector_tools/detector.py`) — pattern matching for classic web attack signatures (XSS, SQLi, etc.) that can still show up in LLM API traffic.
2. **ML classification** (`ml_predictors.py`) — two separate pre-trained classifiers (one for headers, one for body content), loaded once at proxy startup via `ModelLoader`, trained specifically to estimate the probability that a request contains an LLM attack such as **prompt injection**, a safety/guardrail bypass attempt, or a system-prompt-injection attempt.
3. **Combined-signal rules** (`combined_attack_rules.py`) — deterministic checks that only make sense when header and body are read *together*. Concretely, this currently covers **model-override conflicts**: a header like `X-Model-Override`, `X-Force-Model`, or `X-Preferred-Model` can look harmless in isolation (an internal/enterprise deployment might legitimately use a similarly named header), but becomes a provable attack when it targets a *different* model than the one declared in `body["model"]` — silently trying to redirect the request to another model than the one the caller believes they're using. This kind of cross-field comparison is a fact to check, not a pattern to learn, so it's handled with an explicit rule instead of a classifier.

The current decision logic (per the module's own documentation) is an intentionally simple, conservative **OR** across signals — if *any* signal flags the request, it's treated as insecure, with room to introduce per-signal weighting later if false positives become a problem in practice.

`SecurityAnalyzer.analyze()` orchestrates all three signals into a `SecurityContext` object containing:
- `risk_score` (0–1 float; forced to `1.0` if XSS/SQLi is detected, otherwise the max of the header/body ML probabilities above a 0.40 confidence floor)
- `matched_patterns`
- `flags` (e.g. `combined_model_override`, `header_malicious_probablity`, `body_malicious_probablity`, XSS/SQLi detection flag)

This structured result is what powers the risk ring and flag chips in the frontend's **Security Console**.

### Scope: which LLM risks are covered

Following the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/), the detector deliberately targets only risks that are inferable from the text of a *single* HTTP request:

| Risk | Coverage |
|---|---|
| **LLM01 — Prompt Injection** | ✅ Primary focus — both direct (in the body/prompt) and indirect (smuggled through headers). |
| **LLM02 — Sensitive Information Disclosure** | 🟡 Partial coverage. |
| **LLM07 — System Prompt Leakage** | 🟡 Partial coverage. |
| Supply chain, model poisoning, excessive agency, etc. | ❌ Out of scope — these are architecture/process-level risks that can't be determined by inspecting one request's content. |

The header-conflict logic was further evaluated per attack category — of the four categories in the header training dataset, only `model_override` genuinely requires comparing header against body; `safety_bypass` and `system_prompt_injection` are unambiguous from the header alone (handled by the ML header model), and `role_override` is a known, documented limitation since the proxy currently has no access to session/auth context to validate a claimed role against.

The training pipeline for these models (dataset curation from public prompt-injection datasets, plus a custom generator that systematically injects known prompt-injection payloads into common headers like `User-Agent`, `Referer`, `X-Forwarded-For`, and `X-Custom-*`) is intentionally kept in a **separate repository** from this proxy, so the production proxy image never has to carry heavy training-only dependencies (`datasets`, `pandas`, etc.) — only the final `model.pkl` artifacts and the lightweight inference code in `analyzer.py` ship here.

---

## 🖥️ Frontend Dashboard

A Vue 3 single-page app (Vite + Tailwind CSS) that gives the operator a live, browsable view of proxy traffic:

- **`HeaderBar.vue`** — top navigation/status bar.
- **`PacketTable.vue`** — live, real-time list of intercepted requests (fed over WebSocket).
- **`PacketInspector.vue`** — detailed view of a selected request (method, path, headers, body, target host/port).
- **`BottomConsole.vue`** — the **Security Console**: renders the risk score as an animated ring (0–100%), a risk badge (clean / low / warning / critical), and contextual chips for model-override conflicts and XSS/SQLi detections, based on the `security_details` object attached to each packet.
- **`AIAttackerModal.vue`** — a placeholder modal for a planned future feature: an AI-driven payload generator for offensive testing of LLM endpoints (e.g. auto-generating prompt-injection payloads).

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- A `.env` file based on `.env.example` (database credentials)

### Environment variables (`.env.example`)
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=
DB_USER=
DB_PASSWORD=
```

### Run with Docker Compose
```bash
docker compose up --build
```

This spins up four services, as defined in `docker-compose.yml`:

| Service | Description | Port |
|---|---|---|
| `app` | The mitmproxy addon (`mitmdump -s mitm_addon.py`) | `8080` |
| `dashboard_api` | FastAPI dashboard backend (`uvicorn dashboard.api:app`) | `8000` |
| `frontend` | Vue/Vite dev server | `5173` |
| `postgres` | PostgreSQL 16, auto-initialized from `database/schema/tables.sql` | `5433` (host) → `5432` (container) |

Once running:
1. Point your LLM client / app's HTTP proxy settings at `localhost:8080` (currently HTTP only — see the HTTPS interception item on the roadmap for TLS-protected LLM APIs).
2. Open the dashboard at `http://localhost:5173`.
3. Watch intercepted requests appear in the packet table in real time, inspect their LLM-attack risk in the security console, and forward, modify, or drop them.

### Local (non-Docker) setup
```bash
pip install -r requirements.txt
# ensure PostgreSQL is running and .env is configured
mitmdump -s mitm_addon.py -p 8080          # start the proxy
uvicorn dashboard.api:app --reload         # start the dashboard API
cd frontend && npm install && npm run dev  # start the frontend
```

Or use the CLI dashboard instead of the web UI:
```bash
python -m dashboard.app
```

---

## 🔄 Development Workflow

This project follows an explicit, issue-driven workflow:

1. **Idea → Issue** — every feature or fix starts as a GitHub issue with a clear objective and task checklist.
2. **Research** — the concepts and stack involved are studied *before* writing code, to understand the "why," not just the "how."
3. **Branch** — each issue is implemented on its own feature branch; `main` stays stable and deployable.
4. **Implement & Test** — code is written and verified locally before committing.
5. **Pull Request → Merge** — completed work is merged via a PR that closes the related issue, keeping a clean, traceable history.

Commit messages follow conventional-commit style with closing keywords (e.g. `fixes #12`), and branches are deleted after merge.

---

## 🏛️ Architecture Decisions

Documented in full in `docs/architecture-decisions.md`. Highlights:

**ADR-001 — Database driver: `psycopg3` over an ORM**
Chosen over SQLAlchemy for minimal latency, native zero-copy binary (`BYTEA`) transfer between sockets and PostgreSQL, and thread/async-safe connection pooling suited to concurrent request handling — deliberately avoiding ORM object-mapping overhead where raw throughput matters.

**ADR-002 — Project structure & separation of concerns**
Database management (`db_manager.py`) lives inside its own module so that both the low-level proxy addon and the high-level FastAPI dashboard can import database utilities without circular dependencies.

**Security practices**
- All credentials (`DB_USER`, `DB_PASSWORD`, `DB_NAME`) are kept out of version control via `.env`, with `.env.example` provided as a template.
- `.gitignore` is configured to prevent accidental commits of local environment files, logs, caches, and trained model artifacts.

**Notable engineering fixes along the way**
- Correct `Content-Length` recalculation when a request body is edited by the operator before forwarding.
- Proper `HTTP/1.1 431 Request Header Fields Too Large` response for abnormally large headers, instead of silently failing.
- Resolved a PostgreSQL idle-transaction/lock issue during development (via `pg_terminate_backend`), after which the workflow shifted fully to the `psql` CLI for schema work.

---

## 🧪 Archive / Learning Milestones

The `archive/` directory is intentionally preserved (not deleted) as a record of the project's learning trajectory:

- **`TCP_CHAT_SERVER(v0)/`** — The very first milestone: a multi-threaded TCP socket server/client implementing a custom length-prefixed protocol (a 64-byte header declaring payload length, to solve TCP stream framing). Includes a custom `@track_uptime` decorator (built with `functools.wraps`) for per-client session profiling. Based on a socket-programming tutorial, extended with type hints and uptime tracking. This was the stepping stone toward understanding standard protocols like HTTP.
- **`inspector_server.py`** — An early asyncio-based HTTP inspector (pre-mitmproxy), reading raw HTTP requests directly off a socket with `asyncio.StreamReader`/`StreamWriter`, including the same 431-header-too-large safeguard later carried into the current implementation.
- **`FastAPI_intro/`** — First experiments with FastAPI, before it became the dashboard's backend framework.

---
