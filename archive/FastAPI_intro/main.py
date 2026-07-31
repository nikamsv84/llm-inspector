import webview
from threading import Thread
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

is_intercept_on = False

MOCK_PACKETS = [
    {"id": 1, "method": "GET", "path": "/api/v1/auth", "status": 200, "risk": "Low"},
    {"id": 2, "method": "POST", "path": "/v2/users/login", "status": 401, "risk": "Medium"},
    {"id": 3, "method": "GET", "path": "/admin/config", "status": 403, "risk": "High"},
]


@app.post("/api/intercept/toggle")
def toggle_intercept():
    global is_intercept_on
    is_intercept_on = not is_intercept_on
    return {"status": "ON" if is_intercept_on else "OFF"}


@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    global is_intercept_on

    status_text = "ON" if is_intercept_on else "OFF"
    status_color = "text-red-500" if is_intercept_on else "text-amber-400"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Mini Burp Suite</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-gray-100 font-sans p-6">

        <div class="flex justify-between items-center border-b border-gray-800 pb-4 mb-6">
            <div>
                <h1 class="text-2xl font-bold text-emerald-400 font-mono">⚡ MINI BURP SUITE</h1>
                <p class="text-xs text-gray-400 mt-1">Backend, Security & AI Lab v3.0.0-alpha</p>
            </div>

            <div class="flex items-center space-x-4">
                <button onclick="toggleIntercept()" class="px-4 py-2 bg-gray-900 border border-gray-700 hover:border-amber-500 hover:bg-gray-800 text-amber-400 rounded-lg font-mono text-xs transition-all active:scale-95 shadow-md">
                    ⏻ TOGGLE INTERCEPT
                </button>
                <span class="px-3 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 text-xs rounded-full font-mono">Proxy: 8080</span>
            </div>
        </div>

        <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-gray-900 border border-gray-800 p-4 rounded-lg">
                <p class="text-xs text-gray-400 uppercase">Captured Packets</p>
                <p class="text-2xl font-bold text-white mt-1 font-mono">{len(MOCK_PACKETS)}</p>
            </div>

            <div class="bg-gray-900 border border-gray-800 p-4 rounded-lg">
                <p class="text-xs text-gray-400 uppercase">Intercept Status</p>
                <p id="intercept-status" class="text-2xl font-bold mt-1 font-mono {status_color}">{status_text}</p>
            </div>

            <div class="bg-gray-900 border border-gray-800 p-4 rounded-lg">
                <p class="text-xs text-gray-400 uppercase">AI Security Threats</p>
                <p class="text-2xl font-bold text-red-500 mt-1 font-mono">1 Detected</p>
            </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            <div class="bg-gray-800 px-4 py-3 border-b border-gray-700">
                <h2 class="text-sm font-semibold font-mono text-gray-300">HTTP History</h2>
            </div>
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="border-b border-gray-800 text-xs text-gray-400 font-mono bg-gray-900/50">
                        <th class="p-3">ID</th>
                        <th class="p-3">Method</th>
                        <th class="p-3">Path</th>
                        <th class="p-3">Status</th>
                        <th class="p-3">Risk Level</th>
                    </tr>
                </thead>
                <tbody class="text-sm font-mono divider-y divider-gray-800">
    """

    for pkt in MOCK_PACKETS:
        risk_color = "text-emerald-400" if pkt["risk"] == "Low" else (
            "text-amber-400" if pkt["risk"] == "Medium" else "text-red-500 font-bold")
        method_color = "text-blue-400" if pkt["method"] == "GET" else "text-purple-400"

        html_content += f"""
                    <tr class="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                        <td class="p-3 text-gray-500">#{pkt["id"]}</td>
                        <td class="p-3 {method_color} font-bold">{pkt["method"]}</td>
                        <td class="p-3 text-gray-300">{pkt["path"]}</td>
                        <td class="p-3 text-gray-400">{pkt["status"]}</td>
                        <td class="p-3 {risk_color}">{pkt["risk"]}</td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>

        <script>
        function toggleIntercept() {
            fetch('/api/intercept/toggle', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    const statusTarget = document.getElementById('intercept-status');
                    statusTarget.innerText = data.status;

                    if (data.status === 'ON') {
                        statusTarget.className = 'text-2xl font-bold mt-1 font-mono text-red-500';
                    } else {
                        statusTarget.className = 'text-2xl font-bold mt-1 font-mono text-amber-400';
                    }
                });
        }
        </script>

    </body>
    </html>
    """
    return html_content


def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    fastapi_thread = Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    time.sleep(1)

    webview.create_window(
        title="Mini Burp Suite - Interactive Desktop",
        url="http://127.0.0.1:8000",
        width=950,
        height=650
    )
    webview.start()