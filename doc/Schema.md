# SCHEMA.md — Data Structures & Contracts

## Real Estate AI Bot · Single source of truth for all data shapes

**Reference:** SPEC.md (read first)
**Rule:** Every function, prompt, and formatter must conform to the schemas defined here.
If a schema needs to change, update this file first — then update the code.

---

## 1. Google Sheets — Property Listing

### Column Definitions

| Column | Key            | Type    | Required | Accepted Values                                |
| ------ | -------------- | ------- | -------- | ---------------------------------------------- |
| A      | `name`         | string  | yes      | Any non-empty string                           |
| B      | `location`     | string  | yes      | Full address or area name                      |
| C      | `bts`          | string  | no       | Nearest BTS/MRT station name. `""` if none     |
| D      | `price`        | integer | yes      | Monthly rent in THB. No commas, no symbols     |
| E      | `type`         | string  | yes      | `Studio` / `1BR` / `2BR` / `3BR` / `Penthouse` |
| F      | `size_sqm`     | integer | yes      | Size in square meters                          |
| G      | `floor`        | integer | no       | Floor number. `0` if ground floor or unknown   |
| H      | `furnished`    | string  | yes      | `Fully` / `Partially` / `Unfurnished`          |
| I      | `pet_friendly` | string  | yes      | `TRUE` / `FALSE`                               |
| J      | `parking`      | string  | yes      | `TRUE` / `FALSE`                               |
| K      | `description`  | string  | no       | Free text. Max 200 characters recommended      |
| L      | `available`    | string  | yes      | `TRUE` / `FALSE`                               |

### Rules

- Row 1 is always the header row — never data
- `available = FALSE` rows are excluded before any processing
- `price` must be a plain integer — the Sheets connector casts it to `int`
- `pet_friendly` and `parking` are stored as strings `"TRUE"` / `"FALSE"` in Sheets but cast to `bool` by the connector

### Sample Row

```
| Lumpini Ville Sukhumvit 77 | Sukhumvit 77, Phrakanong | On Nut | 24500 | 1BR | 35 | 8 | Fully | TRUE | TRUE | Pool view, quiet building | TRUE |
```

---

## 2. Internal Listing Dict

After `data/sheets.py` reads from Google Sheets, each row becomes a Python dict with this shape:

```python
{
    "name":         str,    # e.g. "Lumpini Ville Sukhumvit 77"
    "location":     str,    # e.g. "Sukhumvit 77, Phrakanong"
    "bts":          str,    # e.g. "On Nut" — empty string if none
    "price":        int,    # e.g. 24500
    "type":         str,    # e.g. "1BR"
    "size_sqm":     int,    # e.g. 35
    "floor":        int,    # e.g. 8
    "furnished":    str,    # e.g. "Fully"
    "pet_friendly": bool,   # e.g. True
    "parking":      bool,   # e.g. True
    "description":  str,    # e.g. "Pool view, quiet building"
}
```

Note: `available` is not included — rows where `available = FALSE` are filtered out before this dict is created.

### Type Casting Rules (sheets.py responsibility)

| Raw value from Sheets | Cast to                                      |
| --------------------- | -------------------------------------------- |
| `"24500"`             | `int(24500)`                                 |
| `"35"`                | `int(35)`                                    |
| `"8"`                 | `int(8)`                                     |
| `"TRUE"`              | `bool(True)`                                 |
| `"FALSE"`             | `bool(False)`                                |
| `""` (empty string)   | Keep as `""` for strings, `0` for int fields |

---

## 3. Summarizer — Input / Output

### Input

```python
raw_chat: str
```

Plain string. Any length. Any language (Thai or English). No preprocessing required.

**Example:**

```
สวัสดีครับ ผมกำลังหาคอนโดแถว BTS อโศก งบประมาณประมาณ 25,000 บาทต่อเดือน
ต้องการ 1 ห้องนอน ต้องเลี้ยงแมวได้ครับ ต้องการที่จอดรถด้วย
อยากได้ชั้นไม่สูงมาก ต่ำกว่าชั้น 15 น่าจะดี
พอดีจะย้ายเข้าต้นเดือนหน้าครับ
```

---

### Output (from OpenAI)

The model must return a JSON object. Use `response_format={"type": "json_object"}`.

```json
{
    "budget": "25,000 THB/month",
    "location": "BTS Asok ± 2 stations",
    "property_type": "1BR Condo",
    "move_in": "Early next month",
    "intent_level": "High",
    "next_step": "Send listings and schedule a viewing",
    "notes": ["Has a cat", "Needs 1 parking space", "Prefers below floor 15"]
}
```

### Field Definitions

| Field           | Type             | Description                      | When not mentioned                    |
| --------------- | ---------------- | -------------------------------- | ------------------------------------- |
| `budget`        | string           | Budget as stated or inferred     | `"Not specified"`                     |
| `location`      | string           | Preferred area or BTS station    | `"Not specified"`                     |
| `property_type` | string           | Room type and property type      | `"Not specified"`                     |
| `move_in`       | string           | Move-in date or timeframe        | `"Not specified"`                     |
| `intent_level`  | string           | `Low` / `Medium` / `High` only   | `"Medium"`                            |
| `next_step`     | string           | Recommended action for the agent | `"Follow up to clarify requirements"` |
| `notes`         | array of strings | Any other relevant details       | `[]`                                  |

### Intent Level Guide (for prompt)

| Level    | Signals                                              |
| -------- | ---------------------------------------------------- |
| `High`   | Ready to view, clear requirements, specific timeline |
| `Medium` | Interested but vague on details, no urgency          |
| `Low`    | Just browsing, many conditions, far timeline         |

---

## 4. Matcher — Input / Output

### Input

```python
requirement: str       # Raw requirement text from the agent
listings: list[dict]   # List of Internal Listing Dicts (Section 2)
```

**Example requirement:**

```
BTS Asok 25k 1BR pet-friendly parking below floor 15
```

**Example listings:** _(truncated for readability)_

```python
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
        "pet_friendly": True,
        "parking": True,
        "description": "Pool view, quiet building"
    },
    { ... }
]
```

---

### Output (from OpenAI)

```json
{
    "matches": [
        {
            "rank": 1,
            "name": "Lumpini Ville Sukhumvit 77",
            "reason": "Within budget, pet-friendly, has parking, below floor 15",
            "highlight": "Floor 8 · Pool view · Fully furnished · 35 sqm"
        },
        {
            "rank": 2,
            "name": "iDeo Mobi Sukhumvit",
            "reason": "Pet-friendly, has parking, slightly over budget",
            "highlight": "Floor 12 · City view · Fully furnished · 30 sqm"
        }
    ],
    "reply_message": "Hi! Thank you for your interest. I have found 2 options that match your requirements:\n\n1. Lumpini Ville Sukhumvit 77 — 24,500 THB/month, 1BR, pet-friendly, parking included.\n\n2. iDeo Mobi Sukhumvit — 26,000 THB/month, 1BR, pet-friendly, parking included.\n\nWould you like to schedule a viewing? I am available this week."
}
```

### Field Definitions

| Field                 | Type    | Description                                                              |
| --------------------- | ------- | ------------------------------------------------------------------------ |
| `matches`             | array   | Ranked list of matching properties. Max 5 items. Empty array if none.    |
| `matches[].rank`      | integer | 1-based ranking. 1 is the best match.                                    |
| `matches[].name`      | string  | Must exactly match the `name` field from the listing                     |
| `matches[].reason`    | string  | Why this property matches the requirement                                |
| `matches[].highlight` | string  | Key selling points for this property                                     |
| `reply_message`       | string  | Ready-to-send message to the client. Professional tone. No placeholders. |

### No-Match Output

When no listings match the requirement:

```json
{
    "matches": [],
    "reply_message": "Thank you for reaching out. Unfortunately, we do not have any available properties that match your current requirements. Could you let us know if you are flexible on location or budget? We will do our best to find something suitable."
}
```

---

## 5. Telegram Message Formats

### /summarize Output

```
📋 *Lead Summary*

💰 *Budget:* 25,000 THB/month
📍 *Location:* BTS Asok ± 2 stations
🏠 *Property Type:* 1BR Condo
📅 *Move-in Date:* Early next month
🔥 *Intent Level:* High
✅ *Recommended Next Step:* Send listings and schedule a viewing

💬 *Key Notes:*
• Has a cat
• Needs 1 parking space
• Prefers below floor 15
```

Rules:

- Use Telegram `Markdown` parse mode (not MarkdownV2)
- `*text*` = bold
- If `notes` is empty, omit the Key Notes section entirely
- Intent level emoji: High = 🔥 · Medium = 🟡 · Low = 🔵

---

### /match Output

```
🏠 *Results: 2 Matching Properties*

*1. Lumpini Ville Sukhumvit 77*
📍 On Nut (BTS)
💰 24,500 THB/month · 1BR · 35 sqm
✅ Pet-friendly · Parking included
📝 Floor 8 · Pool view · Fully furnished

*2. iDeo Mobi Sukhumvit*
📍 Asok (BTS)
💰 26,000 THB/month · 1BR · 30 sqm
✅ Pet-friendly · Parking included
📝 Floor 12 · City view · Fully furnished

———
💬 *Ready-to-send reply:*

Hi! Thank you for your interest. I have found 2 options...
```

Rules:

- Header shows actual count: `Results: N Matching Properties`
- Each property block is separated by a blank line
- `reply_message` appears after `———` divider
- If `matches` is empty, replace the whole output with:
    ```
    😔 No properties matched those requirements.
    Try adjusting the budget, location, or other criteria.
    ```

---

## 6. Error Message Strings

These strings are used by handlers. Keep them consistent — do not vary the wording.

| Scenario                  | Message                                                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `/summarize` with no text | `"Please paste the customer chat after the command.\n\nExample:\n/summarize\nHi, I'm looking for a 1BR near BTS Asok..."` |
| `/match` with no text     | `"Please describe what the client needs after the command.\n\nExample:\n/match BTS Asok 25k 1BR pet-friendly"`            |
| OpenAI API error          | `"Something went wrong while processing your request. Please try again in a moment."`                                     |
| Google Sheets error       | `"Could not load property data. Please contact your administrator."`                                                      |
| Access denied             | `"Access denied."`                                                                                                        |

---

## 7. Config Object Shape

```python
# config.py — expected attributes after loading

config.TELEGRAM_BOT_TOKEN   # str
config.OPENAI_API_KEY       # str
config.GOOGLE_SHEET_ID      # str
config.SERVICE_ACCOUNT_PATH # str — path to service_account.json
config.ALLOWED_IDS          # set[int] — Telegram user IDs
```

---

_SCHEMA.md v1.0 — Real Estate AI Bot_
_Next document: PROMPTS.md_
