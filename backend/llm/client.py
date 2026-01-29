import json
import os
import urllib.request
from pathlib import Path


def _load_dotenv() -> None:
    # Load .env from repo root or backend folder if present.
    candidates = [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for path in candidates:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


def _extract_json(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def _sanitize_speech(value: str | None) -> str | None:
    if not value:
        return value
    cleaned = value.replace("undefined", "").replace("Undefined", "").replace("UNDEFINED", "")
    return cleaned.strip()


def call_llm(prompt: str) -> dict:
    """
    Return structured output:
    {
        "speech": "...",
        "action": {
            "vote": "player_id | null",
            "kill": "player_id | null",
            "check": "player_id | null",
            "guard": "player_id | null",
            "save": true | false | null,
            "poison": "player_id | null"
        }
    }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "deepseek-v3.2")

    if not api_key:
        from llm.mock import call_llm as mock_call_llm
        return mock_call_llm(prompt)

    url = api_base.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful game AI. Reply strictly in JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        from llm.mock import call_llm as mock_call_llm
        return mock_call_llm(prompt)

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    parsed = _extract_json(content) if isinstance(content, str) else None
    if parsed:
        if isinstance(parsed, dict):
            speech = parsed.get("speech")
            if isinstance(speech, str):
                parsed["speech"] = _sanitize_speech(speech)
        return parsed
    from llm.mock import call_llm as mock_call_llm
    return mock_call_llm(prompt)
