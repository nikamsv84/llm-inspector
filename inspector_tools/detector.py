from .HTTPRequest import HTTPRequest
from .HTTPRequest import HTTPRequest


class WebSecurityScanner:
    def __init__(self):
        # Database attack signatures (SQL Injection)
        self.sqli_signatures = [
            "'",  # Breaks the query string structure to inject custom logic
            "or 1=1",  # Creates an always-true condition to bypass authentication
            "--",  # Comments out the remainder of the database command
            "union select"  # Appends unauthorized queries to leak sensitive data
        ]

        # Browser-side attack signatures (Cross-Site Scripting - XSS)
        self.xss_signatures = [
            "<script>",  # Injects directly executable JavaScript blocks into the victim's browser
            "javascript:",  # Forces the browser to execute dangerous scripts instead of navigating
            "onerror=",  # Leverages HTML event handlers to trigger covert script execution
            "alert("  # Commonly used proof-of-concept function to confirm a successful exploit
        ]

    def analyze(self, req: HTTPRequest) -> dict:
        analysis_result = {
            "is_secure": True,
            "attack_type": None,
            "matched_patterns": []
        }

        if not req.query_params:
            return analysis_result

        detected_sqli = set()
        detected_xss = set()

        for key, value in req.query_params.items():
            lower_value = value.lower()

            for pattern in self.sqli_signatures:
                if pattern in lower_value:
                    detected_sqli.add(pattern)

            for pattern in self.xss_signatures:
                if pattern in lower_value:
                    detected_xss.add(pattern)

        if detected_sqli or detected_xss:
            analysis_result["is_secure"] = False
            all_patterns = list(detected_sqli | detected_xss)
            analysis_result["matched_patterns"] = all_patterns

            if detected_sqli and detected_xss:
                analysis_result["attack_type"] = "Multi-Payload Attack"
            elif detected_sqli:
                analysis_result["attack_type"] = "SQL Injection"
            else:
                analysis_result["attack_type"] = "XSS"

        return analysis_result