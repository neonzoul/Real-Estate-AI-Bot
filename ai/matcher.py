import json
from pathlib import Path

from openai import OpenAI

from config import config

MODEL = "gpt-4o-mini"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "match.txt"

NO_MATCH_REPLY = (
    "Thank you for reaching out. Unfortunately, we do not currently have any "
    "available properties that match your requirements. Could you let us know "
    "if you are flexible on location, budget, or other criteria? We will do "
    "our best to find something suitable."
)

_client = OpenAI(api_key=config.OPENAI_API_KEY)
_prompt_template = PROMPT_PATH.read_text(encoding="utf-8")


def match_properties(requirement: str, listings: list[dict]) -> dict:
    if not listings:
        return {"matches": [], "reply_message": NO_MATCH_REPLY}

    listings_json = json.dumps(listings, ensure_ascii=False, indent=2)
    prompt = _prompt_template.replace("{requirement}", requirement).replace(
        "{listings}", listings_json
    )

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Matcher returned empty content from OpenAI")

    return json.loads(content)