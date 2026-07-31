import urllib.parse
from collections import UserDict
from curses.ascii import isalnum
from typing import Callable, Any

# Custom dictionary to automatically handle case-insensitive HTTP header lookups
class CaseInsensitiveDict(UserDict):
    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key.lower().strip(), value)
    def __getitem__(self, key: str):
        return super().__getitem__(key.lower().strip())
    def get(self, key: str, default: Any = None):
        return super().get(key.lower().strip(), default)
    def __contains__(self, key: str):
        return super().__contains__(key.lower().strip())

class HTTPRequest:
    def __init__(self, raw_message: str):
        self.method = ""
        self.path = ""
        self.http_version = ""
        self.headers = CaseInsensitiveDict()
        self.query_params = {}
        self.body = ""
        self.target_host = ""
        self.target_port = ""

        if raw_message:
            self._parse(raw_message)

    def _parse(self, raw_message):

        parts = raw_message.split("\r\n\r\n", 1)
        header_section = parts[0]
        if len(parts) > 1:
            self.body = parts[1]

        lines = header_section.split("\r\n")
        if not lines or lines[0] == "":
            return

        request_line = lines[0]
        request_parts = request_line.split(" ")
        if len(request_parts) >= 2:
            self.method, full_path, *version_parts = request_parts
            self.http_version = version_parts[0] if version_parts else "HTTP/1.1"

            parsed_url = urllib.parse.urlparse(full_path)
            self.path = parsed_url.path

            raw_queries = urllib.parse.parse_qs(parsed_url.query)
            self.query_params = {k: v[0] for k, v in raw_queries.items()}

        for line in lines[1:]:
            if line.strip() == "":
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                self.headers[key] = value.strip()

        initial_host, *initial_port = self.headers.get("host", "").split(":")
        self.target_host = initial_host

        if initial_port:
            self.target_port = int(initial_port[0])
        else:
            self.target_port = 80


    @property
    def cookies(self) -> dict:
        cookie_header = self.headers.get("cookie", "")
        if not cookie_header:
            return {}

        cookie_dict = {}
        parts = cookie_header.split(";")
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                cookie_dict[key.strip().lower()] = value.strip()

        return cookie_dict


if __name__ == "__main__":

    sample_request_with_port = (
        "GET /search HTTP/1.1\r\n"
        "Host: 127.0.0.1:8080\r\n"
        "User-Agent: Mozilla/5.0\r\n"
        "\r\n"
    )

    req1 = HTTPRequest(sample_request_with_port)
    print("[Test 1 - Custom Port]")
    print(f"Target Host: {req1.target_host}")
    print(f"Target Port: {req1.target_port} (Type: {type(req1.target_port).__name__})")
    print("-" * 30)

    sample_request_no_port = (
        "GET /index.html HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Accept: text/html\r\n"
        "\r\n"
    )

    req2 = HTTPRequest(sample_request_no_port)
    print("[Test 2 - Default Port]")
    print(f"Target Host: {req2.target_host}")  #  example.com
    print(f"Target Port: {req2.target_port}")  #  80
    print("-" * 30)