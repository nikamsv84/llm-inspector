import unittest
import HTTPRequest


class TestHTTPRequestParser(unittest.TestCase):

    def test_standard_get_request(self):
        # Test core parsing logic, query extraction, and lower-case header normalization
        raw_msg = (
            "GET /analyze?target=vulnerable-app&scan=true HTTP/1.1\r\n"
            "Host: 127.0.0.1:8080\r\n"
            "User-Agent: Mozilla/5.0\r\n"
            "Cookie: session_id=nika_secure_token_123; role=admin\r\n"
            "\r\n"
        )
        req = HTTPRequest.HTTPRequest(raw_msg)

        self.assertEqual(req.method, "GET")
        self.assertEqual(req.path, "/analyze")
        self.assertEqual(req.query_params.get("target"), "vulnerable-app")
        self.assertEqual(req.query_params.get("scan"), "true")
        self.assertEqual(req.headers.get("host"), "127.0.0.1:8080")
        self.assertEqual(req.headers.get("user-agent"), "Mozilla/5.0")
        # Ensure your HTTPRequest class handles req.cookies properly
        self.assertEqual(req.cookies.get("session_id"), "nika_secure_token_123")
        self.assertEqual(req.cookies.get("role"), "admin")

    def test_missing_http_version(self):
        # Prevent IndexError crashes on malformed packets or downgrade attacks without HTTP version
        raw_msg = (
            "GET /index.html\r\n"
            "Host: localhost\r\n"
            "\r\n"
        )
        req = HTTPRequest.HTTPRequest(raw_msg)

        self.assertEqual(req.method, "GET")
        self.assertEqual(req.path, "/index.html")
        self.assertEqual(req.http_version, "HTTP/1.1")

    def test_malformed_headers(self):
        # Avoid parser confusion crashes when handling invalid headers missing a colon character
        raw_msg = (
            "GET / HTTP/1.1\r\n"
            "Host: 127.0.0.1\r\n"
            "MALFORMED_LINE_WITHOUT_COLON_ATTACK\r\n"
            "Authorization: Bearer 12345\r\n"
            "\r\n"
        )
        req = HTTPRequest.HTTPRequest(raw_msg)

        self.assertEqual(req.headers.get("host"), "127.0.0.1")
        self.assertEqual(req.headers.get("authorization"), "Bearer 12345")
        self.assertNotIn("malformed_line_without_colon_attack", req.headers)

    def test_post_request_with_body(self):
        # Validate successful extraction of POST request body payload for data inspection
        raw_msg = (
            "POST /login HTTP/1.1\r\n"
            "Host: 127.0.0.1\r\n"
            "Content-Length: 27\r\n"
            "\r\n"
            "username=nika&password=123"
        )
        req = HTTPRequest.HTTPRequest(raw_msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "/login")
        self.assertEqual(req.body, "username=nika&password=123")


if __name__ == "__main__":
    unittest.main()