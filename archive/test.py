import time
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from database.db_manager import *


def simulate_incoming_request(path: str, description: str):
    print(f"\n📡 [Client] Sending Request: {description} (Path: {path})...")

    req_id = save_raw_requests("GET", "example.com", 80, path, {"Host": "example.com", "User-Agent": "TestClient"})

    create_intercept_entry(req_id)

    start_time = time.time()
    action = wait_for_user_action(req_id)
    elapsed = time.time() - start_time

    print(f"🎯 [Client] Request #{req_id} unblocked after {elapsed:.2f}s! Final Action -> '{action}'")


if __name__ == "__main__":
    open_pool()
    print("🧪 Starting Complete Pipeline Test...")

    simulate_incoming_request("/api/v1/health", "Test 1: Forward Unmodified")

    simulate_incoming_request("/api/v1/secret-data", "Test 2: Drop Request")

    simulate_incoming_request("/api/v1/user", "Test 3: Edit Path")

    print("\n✅ All test scenarios completed successfully!")