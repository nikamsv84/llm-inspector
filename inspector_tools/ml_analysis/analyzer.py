from inspector_tools.ml_analysis.security_context import SecurityContext
from inspector_tools.ml_analysis.ml_predictors import run_ml_predictions
from inspector_tools.ml_analysis.combined_attack_rules import has_model_override_conflict
from inspector_tools.HTTPRequest import HTTPRequest
from inspector_tools.model_loader import ModelLoader
from inspector_tools.detector import WebSecurityScanner

import json


def extract_prompt_from_json(raw_body: str) -> str:
    if not raw_body or not raw_body.strip():
        return raw_body

    try:
        data = json.loads(raw_body)

        if isinstance(data, dict):
            if "messages" in data and isinstance(data["messages"], list):
                extracted_texts = []
                for msg in data["messages"]:
                    if isinstance(msg, dict) and "content" in msg:
                        extracted_texts.append(str(msg["content"]))
                if extracted_texts:
                    return " ".join(extracted_texts)

            if "prompt" in data:
                return str(data["prompt"])

    except (json.JSONDecodeError, TypeError):
        pass

    return raw_body

class SecurityAnalyzer:
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader

    def analyze(self, request: HTTPRequest) -> SecurityContext:
        context = SecurityContext(request)
        run_ml_predictions(context, self.model_loader)
        has_model_override_conflict(context)

        web_security_scanner = WebSecurityScanner()
        analysis_result = web_security_scanner.analyze(request)
        is_xss_sqli_detected = not analysis_result["is_secure"]
        context.flags["Xss/Sqli detection: "] = is_xss_sqli_detected


        header_prob = context.flags.get("header_malicious_probablity", 0.0)
        body_prob = context.flags.get("body_malicious_probablity", 0.0)

        clean_header_prob = header_prob if header_prob > 0.40 else 0.0
        clean_body_prob = body_prob if body_prob > 0.40 else 0.0

        context.risk_score = max(clean_header_prob, clean_body_prob)

        if is_xss_sqli_detected:
            context.risk_score = 1.0

        return context