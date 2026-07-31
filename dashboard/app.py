import asyncio
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from database.db_manager import (
    get_pending_intercepts,
    init_db,
    open_pool,
    release_intercepted_request,
    save_modified_request,
)


def rebuild_raw_http(method: str, path: str, headers: dict, body: str = "") -> bytes:
    request_line = f"{method} {path} HTTP/1.1\r\n"

    body_bytes = body.encode("utf-8")

    # Recalculate Content-Length based on the actual length of the new body
    headers = dict(headers)  # copy to avoid mutating the caller's dict
    for key in list(headers.keys()):
        if key.lower() == "content-length":
            del headers[key]
    headers["Content-Length"] = str(len(body_bytes))

    headers_lines = []
    for k, v in headers.items():
        headers_lines.append(f"{k}: {v}\r\n")

    headers_str = "".join(headers_lines)
    request_head = f"{request_line}{headers_str}\r\n".encode("utf-8")

    return request_head + body_bytes


async def async_input(prompt: str = "") -> str:
    """Non-blocking wrapper for standard input using asyncio thread pool."""
    return await asyncio.to_thread(input, prompt)


async def start_cli_dashboard() -> None:
    await open_pool()
    await init_db()
    print("\n" + "=" * 60)
    print("🚀 [CLI INTERCEPTOR DASHBOARD STARTED]")
    print("Waiting for pending requests... (Press Ctrl+C to exit)")
    print("=" * 60 + "\n")

    try:
        while True:
            pending_list = await get_pending_intercepts()

            for item in pending_list:
                queue_id = item.get("queue_id")
                req_id = item["request_id"]
                method = item["method"]
                path = item["path"]
                host = item["host"]
                port = item["port"]
                headers = item["headers"]

                if isinstance(headers, str):
                    try:
                        headers = json.loads(headers)
                    except json.JSONDecodeError:
                        headers = {}

                print("\n" + "🔴 " * 15)
                print(f"🚨 [INTERCEPTED REQUEST #{req_id} | Queue #{queue_id}]")
                print(f"📌 Target: {host}:{port}")
                print(f"🌐 Line: {method} {path}")
                print("📋 Headers:")
                if isinstance(headers, dict):
                    for k, v in headers.items():
                        print(f"   └─ {k}: {v}")
                print("-" * 50)

                while True:
                    try:
                        raw_action = await async_input("👉 Action -> [f]orward / [d]rop / [e]dit: ")
                        action = raw_action.strip().lower()
                    except UnicodeDecodeError:
                        print("⚠️ Invalid encoding character detected. Retrying...")
                        continue

                    if action == "f":
                        await release_intercepted_request(req_id, action="forwarded")
                        print(f"✅ Request #{req_id} FORWARDED (Unmodified).")
                        break

                    elif action == "d":
                        await release_intercepted_request(req_id, action="dropped")
                        print(f"❌ Request #{req_id} DROPPED.")
                        break

                    elif action == "e":
                        print("\n--- ✏️ EDIT REQUEST MODE ---")
                        new_path_input = await async_input(f"New Path (Press Enter to keep '{path}'): ")
                        new_path = new_path_input.strip() or path

                        current_host = headers.get("Host", headers.get("host", f"{host}:{port}"))
                        new_host_input = await async_input(
                            f"New Host Header (Press Enter to keep '{current_host}'): "
                        )
                        new_host = new_host_input.strip() or current_host
                        headers["Host"] = new_host

                        new_body_input = await async_input("New Body Data (Press Enter to keep empty/original): ")
                        new_body = new_body_input.strip()

                        new_raw_bytes = rebuild_raw_http(method, new_path, headers, body=new_body)

                        await save_modified_request(req_id, method, new_path, headers, new_raw_bytes)
                        await release_intercepted_request(req_id, action="forwarded")
                        print(f"✏️ Request #{req_id} MODIFIED & FORWARDED!")
                        break

                    else:
                        print("⚠️ Invalid choice! Please enter 'f', 'd', or 'e'.")

            await asyncio.sleep(0.5)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\n🛑 Stopping CLI Dashboard... Goodbye!")


if __name__ == "__main__":
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        asyncio.run(start_cli_dashboard())
    except KeyboardInterrupt:
        pass