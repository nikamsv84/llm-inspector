import json
import os
import sys
from pathlib import Path
import threading
import time
from typing import Optional
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from inspector_tools import HTTPRequest
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row


# Thread-safe registry for active intercept events
intercept_events: dict[int, threading.Event] = {}
events_lock = threading.Lock()

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "backend_lab")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

CONN_INFO = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

# Initialize ConnectionPool
pool = ConnectionPool(conninfo=CONN_INFO, min_size=2, max_size=5, open=False)


def get_pending_intercepts():
    """Receiving the list of pending requests for CLI / Web Dashboard."""
    query = """
        SELECT i.id AS queue_id, r.id AS request_id, r.method, r.host, r.port, r.path, r.headers, r.raw_bytes
        FROM intercept_queue i
        JOIN raw_requests r ON i.request_id = r.id
        WHERE i.status = 'pending'
        ORDER BY i.id ASC;
    """
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            return cur.fetchall()

def save_modified_request(
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
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    request_id,
                    method,
                    path,
                    json.dumps(headers),
                    raw_bytes,
                ),
            )
            conn.commit()

def create_intercept_entry(request_id: int) -> int:
    """Inserts a new pending entry into intercept_queue and returns queue_id."""
    query = """
        INSERT INTO intercept_queue (request_id, status)
        VALUES (%s, 'pending')
        RETURNING id;
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (request_id,))
            queue_id = cur.fetchone()[0]
            conn.commit()
            return queue_id


def wait_for_user_action(request_id: int, timeout: float = 300.0) -> str:
    """
    Blocks until released via in-memory threading.Event OR database status change.
    """
    event = threading.Event()

    with events_lock:
        intercept_events[request_id] = event

    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            if event.wait(timeout=0.5):
                break

            query = "SELECT status FROM intercept_queue WHERE request_id = %s;"
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (request_id,))
                    row = cur.fetchone()
                    if row and row[0] != 'pending':
                        return row[0]

        query = "SELECT status FROM intercept_queue WHERE request_id = %s;"
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (request_id,))
                row = cur.fetchone()
                return row[0] if row else "forwarded"

    finally:
        with events_lock:
            intercept_events.pop(request_id, None)

def release_intercepted_request(request_id: int, action: str) -> bool:
    """Called by Dashboard API when user releases a request (forwarded / dropped)."""
    if action not in ("forwarded", "dropped"):
        raise ValueError("Action must be 'forwarded' or 'dropped'")

    query = """
        UPDATE intercept_queue 
        SET status = %s 
        WHERE request_id = %s;
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (action, request_id))
            conn.commit()

    with events_lock:
        event = intercept_events.get(request_id)
        if event:
            event.set()
            return True

    return False


def get_modified_request_bytes(request_id: int) -> Optional[bytes]:
    """Retrieves modified raw_bytes from modified_requests table if present."""
    query = """
        SELECT raw_bytes 
        FROM modified_requests 
        WHERE request_id = %s;
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (request_id,))
            row = cur.fetchone()
            return row[0] if row else None


def init_db():
    """Connect to the database using the connection pool and execute the tables.sql script."""
    BASE_DIR = Path(__file__).resolve().parent
    schema_path = BASE_DIR / "schema" / "tables.sql"

    with pool.connection() as conn:
        with conn.cursor() as cur:
            with open(schema_path, "r", encoding="utf-8") as file:
                make_table = file.read()

            cur.execute(make_table)
            conn.commit()
            print("✅ tables.sql script executed successfully.")


def open_pool():
    """Opens the database connection pool."""
    pool.open()
    print("🔌 Database connection pool opened.")


def save_raw_requests(packet: HTTPRequest, raw_bytes: bytes = b"") -> int:
    """Save the parsed HTTP request into the raw_requests table."""
    query = """
        INSERT INTO raw_requests (method, host, port, path, headers, raw_bytes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    headers_json = json.dumps(dict(packet.headers))

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
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
            inserted_id = cur.fetchone()[0]
            conn.commit()
            return inserted_id


def close_pool():
    """Closes all connections in the pool safely."""
    pool.close()
    print("🔌 Database connection pool closed.")


# ---------------------------------------------------------
# 🧪 TEST PROGRAM FOR THREAD BLOCKING & INTERCEPT LOGIC
# ---------------------------------------------------------
def simulated_client_thread(req_id: int):
    """Simulates a client socket connection thread waiting for user action."""
    print(
        f"⏳ [Client Thread] Request #{req_id} paused. Waiting for dashboard"
        " action..."
    )
    start_time = time.time()

    # Block current thread
    final_action = wait_for_user_action(req_id, timeout=10.0)

    elapsed = time.time() - start_time
    print(
        f"🟢 [Client Thread] Request #{req_id} UNBLOCKED after {elapsed:.2f}s!"
        f" Final Action: '{final_action}'"
    )


if __name__ == "__main__":
    try:
        open_pool()
        init_db()

        # 1. Create a sample HTTPRequest instance
        sample_raw = (
            "GET /intercept-test HTTP/1.1\r\n"
            "Host: test.com:443\r\n"
            "User-Agent: InterceptTestAgent\r\n\r\n"
        )
        req = HTTPRequest(sample_raw)

        # 2. Persist raw packet to DB
        new_id = save_raw_requests(req, raw_bytes=sample_raw.encode("utf-8"))
        print(f"✅ Saved raw request with ID: {new_id}")

        # 3. Create a pending record in intercept_queue
        queue_id = create_intercept_entry(new_id)
        print(f"⏸️ Created queue record ID: {queue_id} for request #{new_id}")

        # 4. Spawn simulated socket thread
        client_t = threading.Thread(
            target=simulated_client_thread, args=(new_id,)
        )
        client_t.start()

        # 5. Simulate 2-second user inspection delay in dashboard
        print("👤 [Dashboard Simulation] User is inspecting the packet...")
        time.sleep(2)

        # 6. Simulate user clicking FORWARD button
        print("👆 [Dashboard Simulation] User clicked 'FORWARD'!")
        released = release_intercepted_request(new_id, action="forwarded")
        print(f"✨ Release signal sent: {released}")

        # Wait for client thread execution to complete
        client_t.join()

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        close_pool()