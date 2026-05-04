import json
from pathlib import Path

from openai import OpenAI

from config import config

MODEL = "gpt-4o-mini"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "summarize.txt"

_client = OpenAI(api_key=config.OPENAI_API_KEY)
_prompt_template = PROMPT_PATH.read_text(encoding="utf-8")


def summarize_chat(raw_chat: str) -> dict:
    prompt = _prompt_template.replace("{chat}", raw_chat)

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Summarizer returned empty content from OpenAI")

    return json.loads(content)
