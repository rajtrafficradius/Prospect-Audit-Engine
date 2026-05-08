import json
from typing import Any, Dict


MODEL_PRICING_PER_MILLION = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
    "text-embedding-3-large": {"input": 0.13, "output": 0.0},
}


_STATE: Dict[str, Any] = {
    "openai_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0,
    "estimated_openai_cost": 0.0,
    "models_used": [],
    "last_model": None,
}


def _extract_usage_metrics(response: Any) -> Dict[str, int]:
    usage = getattr(response, "usage", None)
    if not usage:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = (
        getattr(usage, "prompt_tokens", None)
        or getattr(usage, "input_tokens", None)
        or 0
    )
    output_tokens = (
        getattr(usage, "completion_tokens", None)
        or getattr(usage, "output_tokens", None)
        or 0
    )
    total_tokens = getattr(usage, "total_tokens", None)
    if total_tokens is None:
        total_tokens = int(input_tokens or 0) + int(output_tokens or 0)

    return {
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "total_tokens": int(total_tokens or 0),
    }


def _estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING_PER_MILLION.get(model_name or "")
    if not pricing:
        return 0.0
    return (
        (input_tokens / 1_000_000.0) * pricing["input"]
        + (output_tokens / 1_000_000.0) * pricing["output"]
    )


def get_usage_summary() -> Dict[str, Any]:
    return {
        "openai_calls": int(_STATE["openai_calls"]),
        "input_tokens": int(_STATE["input_tokens"]),
        "output_tokens": int(_STATE["output_tokens"]),
        "total_tokens": int(_STATE["total_tokens"]),
        "estimated_openai_cost": round(float(_STATE["estimated_openai_cost"]), 6),
        "models_used": list(_STATE["models_used"]),
        "last_model": _STATE["last_model"],
    }


def _emit_usage_update(delta: Dict[str, Any]) -> None:
    print(f"[USAGE] {json.dumps(delta)}")


def record_openai_usage(response: Any, model_name: str = "") -> Dict[str, Any]:
    metrics = _extract_usage_metrics(response)
    clean_model = str(model_name or "").strip()
    _STATE["openai_calls"] += 1
    _STATE["input_tokens"] += metrics["input_tokens"]
    _STATE["output_tokens"] += metrics["output_tokens"]
    _STATE["total_tokens"] += metrics["total_tokens"]
    _STATE["estimated_openai_cost"] += _estimate_cost(
        clean_model,
        metrics["input_tokens"],
        metrics["output_tokens"],
    )
    if clean_model:
        models = list(_STATE["models_used"])
        if clean_model not in models:
            models.append(clean_model)
        _STATE["models_used"] = models
        _STATE["last_model"] = clean_model
    _emit_usage_update({
        "event": "usage_delta",
        "openai_calls": 1,
        "input_tokens": metrics["input_tokens"],
        "output_tokens": metrics["output_tokens"],
        "total_tokens": metrics["total_tokens"],
        "estimated_openai_cost": round(_estimate_cost(clean_model, metrics["input_tokens"], metrics["output_tokens"]), 6),
        "models_used": [clean_model] if clean_model else [],
        "last_model": clean_model or None,
    })
    return get_usage_summary()
