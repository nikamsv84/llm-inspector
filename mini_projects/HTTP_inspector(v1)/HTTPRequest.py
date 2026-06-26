import urllib.parse

class HTTPRequest:
    def __init__(self, raw_message:str):
        self.method = ""
        self.path = ""
        self.http_version = ""
        self.headers = {}
        self.query_params = {}
        self.body = ""

        if raw_message:
            self._parse(raw_message)

    def _parse(self, raw_message):
        #finding the header and body (if exists) of http request
        parts = raw_message.split("\r\n\r\n", 1)
        header_section = parts[0]
        if len(parts) > 1: # if body exists (in get request for example we don't have body)
            self.body = parts[1]

        lines = header_section.splitlines()
        if not lines:
            return
        request_line = lines[0]
        request_parts = lines[0].split(" ")
        if len(request_parts)>=2:
            self.method, full_path, *version_parts = request_parts
            self.http_version = version_parts[0] if version_parts else "HTTP/1.1"
            parsed_url = urllib.parse.urlparse(full_path)
            self.path = parsed_url.path
            self.query_params = urllib.parse.parse_qs(parsed_url.query)

        for line in lines[1:]:
            if line.strip() == "":
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                self.headers[key.strip()] = value.strip()