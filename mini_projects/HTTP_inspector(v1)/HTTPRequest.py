import urllib.parse


class HTTPRequest:
    def __init__(self, raw_message: str):
        self.method = ""
        self.path = ""
        self.http_version = ""
        self.headers = {}
        self.query_params = {}
        self.body = ""

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
                self.headers[key.strip().lower()] = value.strip()

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