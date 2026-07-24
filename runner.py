import subprocess
import sys
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
env = os.environ.copy()
env["PYTHONPATH"] = BASE_DIR + os.pathsep + env.get("PYTHONPATH", "")

def run_lab():
    print("🚀 Starting Proxy Server...")
    proxy_process = subprocess.Popen([sys.executable, "inspector_server.py"], cwd=BASE_DIR, env=env)

    time.sleep(1.5)

    print("🖥️ Starting CLI Dashboard...\n")
    try:
        dashboard_process = subprocess.Popen(
            [sys.executable, "-m", "dashboard.app"],
            cwd=BASE_DIR,
            env=env,
        )
        dashboard_process.wait()
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    finally:
        print("🧹 Shutting down Proxy Server...")
        proxy_process.terminate()
        proxy_process.wait()
        print("✅ Everything stopped safely.")

if __name__ == "__main__":
    run_lab()