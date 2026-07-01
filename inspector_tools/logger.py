import json
import datetime
from .HTTPRequest import HTTPRequest

class JSONLogger:
    def __init__(self, filename: str = "requests_log.json"):
        # Initialize the logger with a target filename
        self.filename = filename

    def log_request(self, message: HTTPRequest):
        # Construct a clean dictionary parsing all needed HTTP layers
        log_entry = {
            "time": str(datetime.datetime.now()),
            "method": message.method,
            "path": message.path,
            "http_version": message.http_version,
            "headers": dict(message.headers),  # Cast CaseInsensitiveDict to standard dict for JSON
            "query params": message.query_params,
            "body": message.body,
            "cookie": message.cookies
        }

        # Step 1: Read existing data safely
        try:
            with open(self.filename, "r") as f:
                file_content = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Handle missing or empty/corrupt files by initializing a fresh list
            file_content = []

        # Step 2: Append the new log entry object
        file_content.append(log_entry)

        # Step 3: Write the updated list back to disk securely
        try:
            with open(self.filename, "w") as f:
                json.dump(file_content, f, indent=4)
        except Exception as e:
            print(f"[!] Critical Error saving JSON log: {e}")