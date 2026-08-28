import json
import os
import sys
from pathlib import Path
import asyncio
from typing import Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from inspector_tools import HTTPRequest
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

# Async-safe registry for active intercept events using asyncio.Event
intercept_events: dict[int, asyncio.Event] = {}
events_lock = asyncio.Lock()

# Load environment variable
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "backend_lab")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

CONN_INFO = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

# Initialize AsyncConnectionPool
pool = AsyncConnectionPool(conninfo=CONN_INFO, min_size=2, max_size=5, open=False)


async def open_pool():
    """Opens the database connection pool asynchronously."""
    await pool.open()
    print("🔌 Database connection pool opened.")


async def close_pool():
    """Closes all connections in the pool safely."""
    await pool.close()
    print("🔌 Database connection pool closed.")


async def init_db():
    """Connect to the database using the connection pool and execute the tables.sql script."""
    BASE_DIR = Path(__file__).resolve().parent
    schema_path = BASE_DIR / "schema" / "tables.sql"

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            with open(schema_path, "r", encoding="utf-8") as file:
                make_table = file.read()

            await cur.execute(make_table)
            await conn.commit()
            print("✅ tables.sql script executed successfully.")

async def get_dashboard_status()->bool:
    query = """SELECT is_paused FROM dashboard_status where id = 1;"""
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            result = await cur.fetchone()
            return result["is_paused"] if result else False

async def toggle_status():
    query = """
        UPDATE dashboard_status 
        SET is_paused = NOT is_paused, updated_at = CURRENT_TIMESTAMP 
        WHERE id = 1
        RETURNING is_paused;
    """
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            result = await cur.fetchone()
            await conn.commit()
            return result["is_paused"] if result else False

async def get_request_by_id(request_id: int):
    """Retrieves full details of a specific raw request by ID."""
    query = """
        SELECT id, method, host, port, path, headers, raw_bytes 
        FROM raw_requests 
        WHERE id = %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (request_id,))
            row = await cur.fetchone()
            return row if row else None

async def get_pending_intercepts():
    """Receiving the list of pending requests for CLI / Web Dashboard."""
    query = """
        SELECT i.id AS queue_id, r.id AS request_id, r.method, r.host, r.port, r.path, r.headers, r.raw_bytes
        FROM intercept_queue i
        JOIN raw_requests r ON i.request_id = r.id
        WHERE i.status = 'pending'
        ORDER BY i.id ASC;
    """
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query)
            return await cur.fetchall()


async def save_modified_request(
    request_id: int, method: str, path: str, headers: dict, raw_bytes: bytes
):
    """Saves modified request bytes and metadata into modified_requests table."""
    query = """
        INSERT INTO modified_requests (request_id, method, path, headers, raw_bytes)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (request_id) 
        DO UPDATE SET 
            method = EXCLUDED.method,
            path = EXCLUDED.path,
            headers = EXCLUDED.headers,
            raw_bytes = EXCLUDED.raw_bytes;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                query,
                (
                    request_id,
                    method,
                    path,
                    json.dumps(headers),
                    raw_bytes,
                ),
            )
            await conn.commit()


async def create_intercept_entry(request_id: int) -> int:
    """Inserts a new pending entry into intercept_queue and returns queue_id."""
    query = """
        INSERT INTO intercept_queue (request_id, status)
        VALUES (%s, 'pending')
        RETURNING id;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (request_id,))
            row = await cur.fetchone()
            await conn.commit()
            return row[0]


async def save_security_analysis(request_id: int, security_context, risk_level: str):
    async with pool.acquire() as conn:
        query = """
            INSERT INTO security_analyses (request_id, risk_score, risk_level, matched_patterns, flags)
            VALUES ($1, $2, $3, $4, $5)
        """
        patterns_json = json.dumps(getattr(security_context, "matched_patterns", []))
        flags_json = json.dumps(getattr(security_context, "flags", {}))

        await conn.execute(
            query,
            request_id,
            security_context.risk_score,
            risk_level,
            patterns_json,
            flags_json
        )

async def wait_for_user_action(request_id: int, timeout: float = 300.0) -> str:
    """
    Asynchronously waits until released via in-memory asyncio.Event OR database status change.
    """
    event = asyncio.Event()

    async with events_lock:
        intercept_events[request_id] = event

    try:
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Non-blocking async wait for 0.5s chunks
                await asyncio.wait_for(event.wait(), timeout=0.5)
                break
            except asyncio.TimeoutError:
                pass

            query = "SELECT status FROM intercept_queue WHERE request_id = %s;"
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (request_id,))
                    row = await cur.fetchone()
                    if row and row[0] != 'pending':
                        return row[0]

        query = "SELECT status FROM intercept_queue WHERE request_id = %s;"
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (request_id,))
                row = await cur.fetchone()
                return row[0] if row else "forwarded"

    finally:
        async with events_lock:
            intercept_events.pop(request_id, None)


async def release_intercepted_request(request_id: int, action: str) -> bool:
    """Called by Dashboard API when user releases a request (forwarded / dropped)."""
    if action not in ("forwarded", "dropped"):
        raise ValueError("Action must be 'forwarded' or 'dropped'")

    query = """
        UPDATE intercept_queue 
        SET status = %s 
        WHERE request_id = %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (action, request_id))
            await conn.commit()

    async with events_lock:
        event = intercept_events.get(request_id)
        if event:
            event.set()
            return True

    return False


async def get_modified_request_bytes(request_id: int) -> Optional[bytes]:
    """Retrieves modified raw_bytes from modified_requests table if present."""
    query = """
        SELECT raw_bytes 
        FROM modified_requests 
        WHERE request_id = %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (request_id,))
            row = await cur.fetchone()
            return row[0] if row else None


async def save_raw_requests(packet: HTTPRequest, raw_bytes: bytes = b"") -> int:
    """Save the parsed HTTP request into the raw_requests table."""
    query = """
        INSERT INTO raw_requests (method, host, port, path, headers, raw_bytes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    headers_json = json.dumps(dict(packet.headers))

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                query,
                (
                    packet.method,
                    packet.target_host,
                    packet.target_port,
                    packet.path,
                    headers_json,
                    raw_bytes,
                ),
            )
            row = await cur.fetchone()
            await conn.commit()
            return row[0]


async def get_total_requests_count() -> int:
    """Returns the total number of intercepted raw requests."""
    query = "SELECT COUNT(*) FROM raw_requests;"
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query)
            row = await cur.fetchone()
            return row[0]


async def get_modified_requests_count() -> int:
    """Returns the total number of modified requests."""
    query = "SELECT COUNT(*) FROM modified_requests;"
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query)
            row = await cur.fetchone()
            return row[0]


# ---------------------------------------------------------
# 🧪 ASYNC TEST PROGRAM
# ---------------------------------------------------------
async def simulated_client_task(req_id: int):
    """Simulates an async client handler task waiting for user action."""
    print(f"⏳ [Client Task] Request #{req_id} paused. Waiting for dashboard action...")
    start_time = asyncio.get_event_loop().time()

    # Wait for action asynchronously
    final_action = await wait_for_user_action(req_id, timeout=10.0)

    elapsed = asyncio.get_event_loop().time() - start_time
    print(f"🟢 [Client Task] Request #{req_id} UNBLOCKED after {elapsed:.2f}s! Final Action: '{final_action}'")


async def main():
    try:
        await open_pool()
        await init_db()

        # 1. Create a sample HTTPRequest instance
        sample_raw = (
            "GET /intercept-test HTTP/1.1\r\n"
            "Host: test.com:443\r\n"
            "User-Agent: InterceptTestAgent\r\n\r\n"
        )
        req = HTTPRequest(sample_raw)

        # 2. Persist raw packet to DB
        new_id = await save_raw_requests(req, raw_bytes=sample_raw.encode("utf-8"))
        print(f"✅ Saved raw request with ID: {new_id}")

        # 3. Create a pending record in intercept_queue
        queue_id = await create_intercept_entry(new_id)
        print(f"⏸ Created queue record ID: {queue_id} for request #{new_id}")

        # 4. Run simulated client task in background
        client_task = asyncio.create_task(simulated_client_task(new_id))

        # 5. Simulate 2-second user inspection delay in dashboard
        print(" [Dashboard Simulation] User is inspecting the packet...")
        await asyncio.sleep(2)

        # 6. Simulate user clicking FORWARD button
        print("👆 [Dashboard Simulation] User clicked 'FORWARD'!")
        released = await release_intercepted_request(new_id, action="forwarded")
        print(f"✨ Release signal sent: {released}")

        # Wait for client task to complete execution
        await client_task

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())