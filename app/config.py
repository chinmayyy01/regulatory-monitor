import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_BASE = "https://api.groq.com/openai/v1"
OPENAI_API_BASE = "https://api.openai.com/v1"

GROQ_MODELS = {
    "worker": "openai/gpt-oss-20b",
    "judge": "openai/gpt-oss-120b",
    "challenger": "qwen/qwen3.8-27b",
    "prompt_guard": "meta-llama/llama-prompt-guard-2-86m",
}

OPENAI_MODELS = {
    "worker": "gpt-4.1-mini",
    "judge": "gpt-4.1",
    "challenger": "gpt-4o-mini",
    "prompt_guard": "",
}


def provider() -> str:
    return "openai" if os.getenv("OPENAI_API_KEY", "").strip() else "groq"


MODELS = GROQ_MODELS if provider() == "groq" else OPENAI_MODELS

MODEL_WORKER = MODELS["worker"]
MODEL_JUDGE = MODELS["judge"]
MODEL_CHALLENGER = MODELS["challenger"]
MODEL_PROMPT_GUARD = MODELS["prompt_guard"]

MODEL_CHEAP = "gpt-4o-mini" if provider() == "openai" else "openai/gpt-oss-20b"

PRICES_PER_MTOKEN = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "openai/gpt-oss-20b": (0.0, 0.0),
    "openai/gpt-oss-120b": (0.0, 0.0),
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_CHARS = 200_000


def api_base() -> str:
    return GROQ_API_BASE if provider() == "groq" else OPENAI_API_BASE


def api_key() -> str:
    if provider() == "openai":
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key.startswith("sk-"):
            raise RuntimeError("OPENAI_API_KEY is missing or malformed.")
        return key
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key.startswith("gsk_"):
        raise RuntimeError(
            "GROQ_API_KEY is missing or malformed. Copy .env.example to .env and fill it in."
        )
    return key


def estimate_cost(model: str, usage: dict) -> float:
    price_in, price_out = PRICES_PER_MTOKEN.get(model, (0.0, 0.0))
    prompt = int(usage.get("prompt_tokens", 0))
    completion = int(usage.get("completion_tokens", 0))
    return (prompt * price_in + completion * price_out) / 1_000_000


def groq_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key.startswith("gsk_"):
        raise RuntimeError(
            "GROQ_API_KEY is missing or malformed. Copy .env.example to .env and fill it in."
        )
    return key
