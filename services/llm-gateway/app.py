import random
import time

PROVIDERS = ["openai", "anthropic", "gemini", "azure-openai"]

MAX_RETRIES = 3
CIRCUIT_BREAKER_ENABLED = True
CIRCUIT_BREAKER_THRESHOLD = 5
RETRY_BACKOFF_BASE = 0.05

SENSITIVE_HEADERS = {"authorization", "x-api-key", "api-key", "cookie", "set-cookie"}


def redact_headers(headers):
    redacted = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted


def estimate_cost(prompt_tokens, completion_tokens, provider):
    rates = {
        "openai": 0.00001,
        "anthropic": 0.000012,
        "gemini": 0.000006,
        "azure-openai": 0.000011,
    }
    return (prompt_tokens + completion_tokens) * rates[provider]


def call_provider(provider, prompt):
    if provider == "openai" and random.random() < 0.7:
        time.sleep(0.25)
        raise TimeoutError("provider timeout")
    completion_tokens = random.randint(100, 800)
    return {"provider": provider, "text": "ok", "completion_tokens": completion_tokens}


def chat(request):
    headers = request.get("headers", {})
    print({"event": "incoming_request", "headers": redact_headers(headers)})

    prompt = request["prompt"]
    prompt_tokens = len(prompt.split())
    last_error = None

    consecutive_failures = {provider: 0 for provider in PROVIDERS}

    for attempt in range(MAX_RETRIES):
        for provider in PROVIDERS:
            if (
                CIRCUIT_BREAKER_ENABLED
                and consecutive_failures[provider] >= CIRCUIT_BREAKER_THRESHOLD
            ):
                continue
            try:
                result = call_provider(provider, prompt)
                result["attempt"] = attempt
                result["cost"] = estimate_cost(prompt_tokens, result["completion_tokens"], provider)
                return result
            except TimeoutError as exc:
                last_error = exc
                consecutive_failures[provider] += 1
                continue
        time.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))

    raise RuntimeError(f"all providers failed after {MAX_RETRIES} attempts: {last_error}")


if __name__ == "__main__":
    response = chat({
        "prompt": "write a compliance report for a regulated bank",
        "headers": {"authorization": "Bearer sk-prod-leaked-example"},
    })
    print(response)

