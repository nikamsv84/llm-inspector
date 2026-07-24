# 🏛️ Architecture Decision Records (ADR) & Development Journal

Welcome to the architectural documentation for the Backend Security Lab project. This document outlines key engineering decisions, structural design patterns, and security best practices implemented during development.

---

## 📌 ADR-001: Database Driver Selection (`psycopg3`)

* **Date:** July 20, 2026
* **Status:** Accepted

### Context
The socket inspector server requires high-throughput persistence to log intercepted HTTP byte streams (`raw_requests`) and handle real-time request holding/releasing queues.

### Decision
We selected **`psycopg3`** with `psycopg_pool.ConnectionPool` over SQLAlchemy ORM.

### Rationale
1. **Minimal Latency & High Performance:** Eliminates ORM object-mapping overhead for network packets where raw speed is critical.
2. **Native Zero-Copy Transfers:** Directly stream binary data (`BYTEA`) between sockets and PostgreSQL without unnecessary memory allocations.
3. **Thread-Safe Pooling:** Utilizes lightweight connection pooling suited for multi-threaded socket handling (`handle_client` workers).

---

## 📌 ADR-002: Project Structure & Separation of Concerns

* **Date:** July 20, 2026
* **Status:** Accepted

### Decision
* Placed `db_manager.py` inside `inspector_tools/` rather than the project root or dashboard directory.

### Rationale
* Encapsulates all database pool management and SQL execution logic into a dedicated module.
* Enables both the low-level `inspector_server.py` and the high-level `dashboard/app.py` to import database utilities seamlessly without circular dependencies.

---

## 🔒 Security Best Practices Implemented

* **Environment Isolation:** All sensitive credentials (`DB_USER`, `DB_PASSWORD`, `DB_NAME`) are kept strictly out of Git version control using `.env`.
* **Repository Template:** Provided `.env.example` to allow quick setup for collaborators without exposing production secrets.
* **Git Hygiene:** Configured `.gitignore` to prevent accidental tracking of active local environment files.

---

## 🚀 Key Learning Takeaways for Today
* Managing thread-safe connection pools in Python.
* Structuring PostgreSQL queries with `RETURNING id` for cross-table primary key resolution.
* Using non-blocking thread synchronization mechanisms (`threading.Event`) instead of CPU-intensive loops.
---
