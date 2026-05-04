# PROMPTS.md — Prompt Templates & Engineering Notes

## Real Estate AI Bot · Complete prompt reference with examples

**Reference:** SCHEMA.md (read first — all I/O schemas are defined there)
**Rule:** Prompts live in `prompts/` as `.txt` files — never hardcoded in Python.
To improve output quality, edit the prompt file. Do not change the Python code.

---

## 1. Summarizer Prompt

**File:** `prompts/summarize.txt`
**Used by:** `ai/summarizer.py`
**Model:** `gpt-4o-mini`
**Response format:** `{"type": "json_object"}`

---

### Full Prompt

```
You are an assistant for a real estate agency in Bangkok, Thailand.
Your job is to read a raw customer chat and extract key information about what the client is looking for.

The chat may be in Thai, English, or a mix of both.
Extract the information regardless of language and always respond in English.

Return ONLY a valid JSON object. No explanation. No markdown. No code fences.

Use this exact schema:
{
  "budget": "string — monthly rent as stated or inferred. Include currency. Example: '25,000 THB/month'",
  "location": "string — preferred area, BTS/MRT station, or neighborhood",
  "property_type": "string — room type and property type. Example: '1BR Condo', '2BR House'",
  "move_in": "string — move-in date or timeframe as stated",
  "intent_level": "string — must be exactly one of: Low, Medium, High",
  "next_step": "string — one clear recommended action for the agent",
  "notes": ["array of strings — any other relevant details the agent should know"]
}

Rules:
- If a field is not mentioned in the chat, use "Not specified" for string fields and [] for the notes array.
- intent_level must be exactly "Low", "Medium", or "High" — no other values.
- intent_level guide:
    High   = client has clear requirements, specific timeline, ready to view
    Medium = client is interested but vague on details or timeline
    Low    = client is browsing, many conditions, no urgency
- next_step should be a short, specific action. Example: "Send listings near BTS Asok and schedule a viewing"
- notes should capture anything useful that does not fit the other fields: pets, parking, floor preference, furniture preference, number of bathrooms, deal-breakers, etc.
- Do not add fields that are not in the schema.
- Do not wrap the JSON in markdown code fences.

Customer chat:
"""
{chat}
"""
```

---

### How to Inject the Variable

In `ai/summarizer.py`, load the prompt file and replace `{chat}` at runtime:

```python
with open("prompts/summarize.txt", "r") as f:
    prompt_template = f.read()

prompt = prompt_template.replace("{chat}", raw_chat)
```

---

### Example — Full Input / Output

**Input chat (Thai):**

```
สวัสดีครับ ผมกำลังหาคอนโดแถว BTS อโศก
งบประมาณประมาณ 25,000 บาทต่อเดือน
ต้องการ 1 ห้องนอน ต้องเลี้ยงแมวได้ครับ ต้องการที่จอดรถด้วย
อยากได้ชั้นไม่สูงมาก ต่ำกว่าชั้น 15 น่าจะดี
พอดีจะย้ายเข้าต้นเดือนหน้าครับ
```

**Expected output:**

```json
{
    "budget": "25,000 THB/month",
    "location": "BTS Asok",
    "property_type": "1BR Condo",
    "move_in": "Early next month",
    "intent_level": "High",
    "next_step": "Send listings near BTS Asok and schedule a viewing",
    "notes": [
        "Has a cat — needs pet-friendly building",
        "Needs 1 parking space",
        "Prefers below floor 15"
    ]
}
```

---

### Example — Missing Information

**Input chat:**

```
Hi, looking for something near Thonglor. Not sure on budget yet.
```

**Expected output:**

```json
{
    "budget": "Not specified",
    "location": "Thonglor",
    "property_type": "Not specified",
    "move_in": "Not specified",
    "intent_level": "Low",
    "next_step": "Follow up to clarify budget, room type, and timeline",
    "notes": []
}
```

---

### Tuning Notes

| Problem                                               | Fix                                                                          |
| ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| Model returns markdown fences around JSON             | Add "Do not wrap the JSON in markdown code fences" — already in prompt       |
| `intent_level` returns values like "high" or "MEDIUM" | Enforce exact casing in the prompt — already done                            |
| Notes are too verbose                                 | Add: "Each note should be one short sentence — maximum 15 words"             |
| Model adds extra fields not in schema                 | Add: "Do not add fields that are not in the schema" — already in prompt      |
| Thai input causes garbled output                      | Confirm `response_format={"type": "json_object"}` is set — forces valid JSON |
| Budget includes formatting like "฿25,000"             | Add: "Express budget in the format: '25,000 THB/month'"                      |

---

## 2. Matcher Prompt

**File:** `prompts/match.txt`
**Used by:** `ai/matcher.py`
**Model:** `gpt-4o-mini`
**Response format:** `{"type": "json_object"}`

---

### Full Prompt

```
You are an assistant for a real estate agency in Bangkok, Thailand.
Your job is to match a client's requirements against a list of available properties and return the best matches.

Return ONLY a valid JSON object. No explanation. No markdown. No code fences.

Use this exact schema:
{
  "matches": [
    {
      "rank": 1,
      "name": "exact property name from the listings",
      "reason": "short explanation of why this property fits the requirements",
      "highlight": "2-3 key selling points separated by · "
    }
  ],
  "reply_message": "a professional, ready-to-send message to the client listing the matched properties"
}

Rules:
- Return a maximum of 5 matches. Fewer is fine if fewer are relevant.
- Rank by relevance — rank 1 is the best match.
- The "name" field must exactly match the name from the listings data. Do not paraphrase.
- The "reason" field should explain the match in 1 sentence. Be specific. Example: "Within budget, pet-friendly, has parking, below floor 15."
- The "highlight" field should show the 2-3 most relevant features for this client. Example: "Floor 8 · Pool view · Fully furnished"
- If no listings match the requirements, return "matches": [] and write a polite reply_message explaining that no matches were found and asking if the client can be flexible.
- The "reply_message" must be professional and ready to send to the client without any editing.
- Do not use placeholder text like "[Agent Name]" or "[Property Address]" in the reply_message.
- The reply_message should mention each matched property briefly by name and price.
- Do not add fields that are not in the schema.
- Do not wrap the JSON in markdown code fences.

Client requirement:
"""
{requirement}
"""

Available properties (JSON):
"""
{listings}
"""
```

---

### How to Inject the Variables

In `ai/matcher.py`, load the prompt file and replace both variables at runtime:

```python
import json

with open("prompts/match.txt", "r") as f:
    prompt_template = f.read()

prompt = prompt_template.replace("{requirement}", requirement)
prompt = prompt_template.replace("{listings}", json.dumps(listings, ensure_ascii=False, indent=2))
```

Note: Use `ensure_ascii=False` to preserve Thai characters in listing descriptions.

---

### Example — Full Input / Output

**Input requirement:**

```
BTS Asok 25k 1BR pet-friendly parking below floor 15
```

**Input listings (abbreviated):**

```json
[
    {
        "name": "Lumpini Ville Sukhumvit 77",
        "location": "Sukhumvit 77, Phrakanong",
        "bts": "On Nut",
        "price": 24500,
        "type": "1BR",
        "size_sqm": 35,
        "floor": 8,
        "furnished": "Fully",
        "pet_friendly": true,
        "parking": true,
        "description": "Pool view, quiet building"
    },
    {
        "name": "The Base Sukhumvit 50",
        "location": "Sukhumvit 50, Phrakanong",
        "bts": "On Nut",
        "price": 22000,
        "type": "1BR",
        "size_sqm": 30,
        "floor": 18,
        "furnished": "Fully",
        "pet_friendly": false,
        "parking": true,
        "description": "City view, modern building"
    }
]
```

**Expected output:**

```json
{
    "matches": [
        {
            "rank": 1,
            "name": "Lumpini Ville Sukhumvit 77",
            "reason": "Within budget, pet-friendly, has parking, and below floor 15.",
            "highlight": "Floor 8 · Pet-friendly · Pool view"
        }
    ],
    "reply_message": "Hi! Thank you for your interest. Based on your requirements, I found 1 property that matches well:\n\n1. Lumpini Ville Sukhumvit 77 — 24,500 THB/month, 1BR, 35 sqm, pet-friendly, parking included, floor 8.\n\nWould you like to schedule a viewing this week? Please let me know your availability."
}
```

Note: `The Base Sukhumvit 50` is excluded because `pet_friendly = false`.

---

### Example — No Matches

**Input requirement:**

```
BTS Chitlom 15k studio pet-friendly
```

**Expected output:**

```json
{
    "matches": [],
    "reply_message": "Thank you for reaching out. Unfortunately, we do not currently have any available studios near BTS Chitlom within a 15,000 THB budget that allow pets. Could you let us know if you are flexible on location, budget, or pet policy? We will do our best to find something that works for you."
}
```

---

### Tuning Notes

| Problem                                          | Fix                                                                                                   |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| Model returns properties not in the listings     | Add: "You may only recommend properties from the listings provided. Do not invent properties."        |
| `name` field does not match exactly              | Reinforce: "The 'name' field must exactly match the name from the listings data." — already in prompt |
| `reply_message` uses placeholder text            | Add: "Do not use placeholder text like [Agent Name] or [Property Address]" — already in prompt        |
| Too many matches returned for a weak requirement | Add: "Only include properties that are genuinely relevant. Do not pad the list."                      |
| Reply message sounds robotic                     | Add: "Write the reply_message in a warm, professional tone — as if written by a human agent."         |
| Listings JSON is too large and hits token limit  | Pre-filter listings in Python by price range before sending to OpenAI                                 |

---

## 3. Prompt File Locations

```
prompts/
├── summarize.txt   ← Summarizer prompt (Section 1)
└── match.txt       ← Matcher prompt (Section 2)
```

Both files are plain text. No special encoding required. UTF-8.

---

## 4. General Prompting Rules for This Project

These rules apply to both prompts and any future prompts added to this project.

**Always:**

- Start with a clear role statement: "You are an assistant for a real estate agency..."
- Define the exact output schema inside the prompt — not just in code
- Include "Return ONLY a valid JSON object. No explanation. No markdown. No code fences."
- Pair the prompt with `response_format={"type": "json_object"}` in the API call
- Use `{variable_name}` placeholders for runtime injection — never concatenate strings around the prompt
- Include at least one concrete example of expected output in this document (not in the prompt file itself)

**Never:**

- Hardcode prompt text inside Python functions
- Ask the model to return multiple formats (e.g., "return JSON or a message if failed") — always return JSON and handle errors in Python
- Use vague instructions like "return relevant results" — be specific about ranking, limits, and edge cases

---

_PROMPTS.md v1.0 — Real Estate AI Bot_
_Next document: SETUP.md_
