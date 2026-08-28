from inspector_tools.ml_analysis.security_context import SecurityContext
from inspector_tools.model_loader import ModelLoader
import json

SAFE_SHORT_PROMPTS = {
    "hello",
    "hi",
    "hey",
    "test",
    "ping",
    "hello world",
    "tell me a joke",
}

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


def predict_headers(headers: dict, model) -> float:
    if not headers:
        return 0.0

    max_probability = 0.0
    for header_name, header_value in headers.items():
        probabilities = model.predict_proba([str(header_value)])[0]
        malicious_probability = probabilities[1]
        if malicious_probability > max_probability:
            max_probability = malicious_probability

    return max_probability


def predict_body(body: str, model) -> float:
    if not body:
        return 0.0

    real_body = extract_prompt_from_json(body)
    cleaned_lower = real_body.strip().lower()
    if cleaned_lower in SAFE_SHORT_PROMPTS or len(cleaned_lower) <= 3:
        return 0.0

    print(f"DEBUG - Extracted Text for Model: '{real_body}'")

    probabilities = model.predict_proba([str(real_body)])[0]
    malicious_probability = float(probabilities[1])
    return malicious_probability


def run_ml_predictions(context: SecurityContext, model_loader: ModelLoader) -> None:
    if model_loader.header_model:
        context.flags["header_malicious_probablity"] = predict_headers(
            context.headers, model_loader.header_model
        )
    else:
        print("header model not loaded")
        context.flags["header_malicious_probablity"] = -1.0

    if model_loader.body_model:
        raw_body = getattr(context, "request", context).body if hasattr(context, "request") else context.body
        context.flags["body_malicious_probablity"] = predict_body(
            raw_body, model_loader.body_model
        )
    else:
        print("body model not loaded")
        context.flags["body_malicious_probablity"] = -1.0