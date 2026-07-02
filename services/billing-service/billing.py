PROVIDER_RATES = {
    "openai": {"prompt": 0.00001, "completion": 0.00003},
    "anthropic": {"prompt": 0.000012, "completion": 0.00004},
    "gemini": {"prompt": 0.000006, "completion": 0.000018},
}


def usage_charge(provider, prompt_tokens, completion_tokens):
    rate = PROVIDER_RATES[provider]
    return round(
        prompt_tokens * rate["prompt"] + completion_tokens * rate["completion"],
        6,
    )


def monthly_invoice(events):
    total = 0
    for event in events:
        total += usage_charge(
            event["provider"],
            event["prompt_tokens"],
            event["completion_tokens"],
        )
    return round(total, 2)


if __name__ == "__main__":
    print(monthly_invoice([
        {"provider": "openai", "prompt_tokens": 1000, "completion_tokens": 9000},
    ]))

