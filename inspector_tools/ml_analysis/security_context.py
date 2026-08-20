
from inspector_tools import HTTPRequest

class SecurityContext:
    def __init__(self, req: HTTPRequest):
        self.headers = req.headers
        self.body = req.body
        self.risk_score = 0.0
        self.flags = {
            "combined_model_override": False,
            "body_malicious_probablity": 0.0,
            "header_malicious_probablity":0.0,
            "xss_sqli_detected":""
        }