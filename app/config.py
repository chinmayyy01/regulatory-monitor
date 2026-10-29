import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_BASE = "https://api.groq.com/openai/v1"

MODEL_JUDGE = "openai/gpt-oss-120b"
MODEL_WORKER = "openai/gpt-oss-20b"
MODEL_CHALLENGER = "qwen/qwen3.8-27b"
MODEL_PROMPT_GUARD = "meta-llama/llama-prompt-guard-2-86m"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_CHARS = 200_000


def groq_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key.startswith("gsk_"):
        raise RuntimeError(
            "GROQ_API_KEY is missing or malformed. Copy .env.example to .env and fill it in."
        )
    return key
