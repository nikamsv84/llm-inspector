# 🛡️ Mini Burp Suite

A lightweight, multi-threaded HTTP security proxy designed for network traffic inspection, security analysis, vulnerability research, and custom request manipulation. This tool acts as a structured framework to intercept, log, and analyze live HTTP traffic.

---

## 🗺️ Project Roadmap & Version History

You can explore the evolution of this project step-by-step. Navigate to the **Releases/Tags** section of this repository to download and run any specific version to see how the architecture evolved.

- [x] **v1.0.0 - HTTP Inspector**: Basic socket listener capable of capturing, parsing, and logging raw HTTP requests.
- [x] **v2.0.0 - MITM Forward Proxy (Current)**: Dynamic target routing, loop prevention, multi-threading, and live bi-directional data streaming.
- [ ] **v3.0.0 - Request/Response Modifier**: Packet intercepting mechanism to pause, modify, or drop headers/bodies before forwarding.
- [ ] **v4.0.0 - Dashboard (FastAPI)**: Web interface to monitor live logs, view security statistics, and handle intercept UI using asynchronous tasks.
- [ ] **v5.0.0 - Database & Containerization**: Porting JSON logs to SQLite/PostgreSQL and containerizing the entire stack via Docker.
- [ ] **v6.0.0 - HTTPS Interception (SSL/TLS)**: Implementing `CONNECT` tunneling and dynamic certificate generation to audit encrypted traffic.
- [ ] **v7.0.0 - AI Security Engine**: Native integration of an LLM scanner for prompt injection and advanced threat analysis.

---

## 🔍 Version Details & Architecture

### 📦 v1.0.0 — HTTP Inspector
The foundational release focused on establishing basic socket communication and raw HTTP parsing.
* **Architecture**: Single-threaded TCP socket listener bound to a local port.
* **Parsing Engine**: Custom HTTP parser that processes raw text streams to break down requests into structured parameters: Methods (`GET`, `POST`, etc.), Paths, Headers, Query Parameters, Cookies, and Body Data.
* **Logging**: Implementation of a structured `JSONLogger` to save captured requests into a local `requests_log.json` file for offline analysis.
* **Security Baseline**: Initial integration of a local `Security_Analyzer` engine to scan raw text lines for basic web attack signatures.

### 🚀 v2.0.0 — MITM Forward Proxy (Current)
An architectural leap transitioning the project from a passive listener into an active, functional network middleman.
* **True Forward Proxy**: Dynamically opens an upstream socket connection (`mitm_socket`) targeting the remote host parsed from the client's HTTP headers.
* **Multi-Threaded Concurrency**: Leverages Python's `threading` library to spawn isolated workers for each incoming browser connection, allowing simultaneous multi-request streaming without locking up the server.
* **Infinite Loop Prevention**: Integrated defensive network check that drops any incoming requests targeting the proxy's own IP/Port configuration (`127.0.0.1:8080`), avoiding thread exhaustion and recursive socket loops.
* **Bi-directional Data Streaming**: Implements real-time chunk-by-chunk response streaming from remote web servers directly back to the active client socket.

---
