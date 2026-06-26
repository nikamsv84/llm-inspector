# Custom Protocol Socket Server (Foundational Milestone)

A robust, multi-threaded TCP socket server and client implementation in Python. This project serves as a foundational milestone to solidify advanced Python concepts and core networking principles before moving towards standard application-layer protocols (like HTTP).

## 📌 Project Purpose & Context

This project is inspired by fundamental network programming concepts and is designed for academic/experimental purposes. It implements a **custom length-prefixed protocol** to handle the framing of TCP streams. 

> [!NOTE]
> **Network Reality Check:** In a production environment, custom framing like this is rarely used. Instead, standard application-layer protocols (such as HTTP, which relies on `\r\n\r\n` delimiters or `Content-Length` headers) are preferred. This project acts as a stepping stone to understand stream-based communication before simulating or inspecting real-world HTTP traffic.

---

## 🛠️ Advanced Concepts Covered

This codebase is structured to practice and showcase modern, production-grade Python patterns:

* **Advanced Decorators:** Implements a custom `@track_uptime` decorator utilizing `functools.wraps` to dynamically measure, log, and profile individual client session durations without cluttering the core business logic.
* **Strict Type Hinting:** Fully type-hinted code leveraging Python's `typing` module (`Callable`, `Any`) to ensure code readability, maintainability, and robust IDE autocompletion.
* **Multi-threading (`threading`):** Utilizes a thread-per-client model on the server side to handle concurrent connections smoothly.
* **Custom Framing:** Solves the TCP "streaming" challenge by prefixing every message with a fixed 64-byte header indicating the exact length of the incoming payload.

---

## 🚀 How It Works

### The Protocol Breakdown
1. **The Header:** The client calculates the length of the main message, pads it with spaces to strictly fit into **64 bytes**, and sends it first.
2. **The Payload:** Immediately after the header, the client sends the actual string message.
3. **The Server:** The server reads exactly 64 bytes first, parses the integer length, and then reads exactly that many bytes from the socket stream to reconstruct the message perfectly without data bleeding.

---
## 🎓 Acknowledgments & Attribution

* This project's core socket infrastructure is based on the excellent socket programming tutorial by **Tech With Tim**. 
* **My Extensions:** Building upon the tutorial's foundation, I integrated strict Python Type Hinting and designed the custom `@track_uptime` decorator to add execution profiling and session tracking features.

## 📈 Next Steps
Having mastered low-level socket management and custom framing, the next phase of this learning path is the **HTTP Inspector / Proxy Server** project, which transitions from this custom protocol into handling standard, real-world web traffic.