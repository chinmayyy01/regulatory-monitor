import json
import os
import time
import urllib.error
import urllib.request

from app.config import GROQ_API_BASE, MODEL_WORKER, groq_api_key

USER_AGENT = "RegIntelAI/0.1 (+https://github.com/chinmayyy01/regulatory-monitor)"
RETRY_DELAYS = (0, 5, 15, 30, 60)
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium")
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "4096"))


class LlmError(RuntimeError):
    pass


def _loads(content: str):
    try:
        value = json.loads(content)
        if isinstance(value, (dict, list)):
            return value
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = content.find(opener)
        end = content.rfind(closer)
        if start == -1 or end <= start:
            continue
        try:
            value = json.loads(content[start : end + 1])
            if isinstance(value, (dict, list)):
                return value
        except json.JSONDecodeError:
            continue
    return None


def _post(payload: dict, timeout: int) -> dict:
    request = urllib.request.Request(
        f"{GROQ_API_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {groq_api_key()}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def chat_json(
    system: str,
    user: str,
    model: str = MODEL_WORKER,
    timeout: int = 90,
) -> tuple[dict, dict]:
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    last_error: Exception | None = None
    json_mode = True
    for delay in RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            data = _post(payload, timeout)
        except urllib.error.HTTPError as error:
            body = error.read()[:300]
            if error.code == 400 and json_mode:
                json_mode = False
                payload.pop("response_format", None)
                last_error = LlmError(f"json mode rejected: {body!r}")
                continue
            if error.code in (429, 500, 502, 503):
                last_error = LlmError(f"HTTP {error.code}")
                continue
            raise LlmError(f"HTTP {error.code}: {body!r}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            continue

        content = data["choices"][0]["message"]["content"]
        parsed = _loads(content)
        if parsed is None:
            raise LlmError(f"model did not return json: {content[:200]!r}")
        return parsed, data.get("usage", {})

    raise LlmError(f"gave up after {len(RETRY_DELAYS)} attempts: {last_error!r}")
