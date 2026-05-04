# SPEC.md — AI Internal Tool for Real Estate Agencies

## Master Blueprint · Read this before writing any code

**Version:** 1.0
**Stack:** Python · Telegram Bot · OpenAI API · Google Sheets
**Timeline:** MVP in 3 days → First Client Deploy Day 4–7

---

## 1. Project Overview

### What We're Building

A Telegram bot that helps real estate agents do two things:

1. **`/summarize`** — Parse a raw customer chat and return structured lead data
2. **`/match`** — Accept a requirement string, pull listings from Google Sheets, and return ranked matches with a ready-to-send reply

### What We're NOT Building (MVP Scope)

- ❌ Web dashboard
- ❌ Authentication / login system
- ❌ Multi-tenant architecture
- ❌ LINE / Facebook / WhatsApp integration
- ❌ Customer-facing chatbot
- ❌ Database (Google Sheets is the data layer for now)

### Core Philosophy

> Ship fast. Optimize for demo, not scalability.
> If the demo does not impress within 3 minutes, nothing else matters.

---

## 2. Tech Stack

| Layer       | Technology                                    | Reason                                          |
| ----------- | --------------------------------------------- | ----------------------------------------------- |
| Interface   | Telegram Bot                                  | No UI to build · everyone has Telegram          |
| Language    | Python 3.11+                                  | Fast to write · great ecosystem                 |
| Bot Library | `python-telegram-bot` v20+ (async)            | Large community · good docs                     |
| AI          | OpenAI API (`gpt-4o-mini`)                    | Fast · cheap · sufficient for these tasks       |
| Data        | Google Sheets via `gspread` + Service Account | Clients can edit listings without a deploy      |
| Hosting     | Railway.app                                   | GitHub deploy · easy logs · free tier is enough |
| Config      | `.env` + `python-dotenv`                      | No secrets in code                              |

---

## 3. Project Structure

```
real-estate-ai-bot/
├── bot/
│   ├── __init__.py
│   ├── handlers.py          # /start /summarize /match /help
│   └── formatters.py        # Format AI output into Telegram Markdown
├── ai/
│   ├── __init__.py
│   ├── summarizer.py        # Prompt + OpenAI call for /summarize
│   └── matcher.py           # Prompt + OpenAI call for /match
├── data/
│   ├── __init__.py
│   └── sheets.py            # Google Sheets connector
├── prompts/
│   ├── summarize.txt        # Prompt template (kept out of code)
│   └── match.txt            # Prompt template (kept out of code)
├── tests/
│   ├── test_summarizer.py
│   └── test_matcher.py
├── main.py                  # Entry point — starts the bot
├── config.py                # Load and validate env vars
├── requirements.txt
├── .env.example             # Template — never commit real .env
├── .gitignore
├── Procfile                 # For Railway deployment
└── README.md
```

---

## 4. Environment Variables

All secrets live in `.env` only. Never hardcode in source files.

```env
# .env.example
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=sk-...
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
GOOGLE_SERVICE_ACCOUNT_JSON=./service_account.json
ALLOWED_TELEGRAM_IDS=123456789,987654321
```

`config.py` must validate all variables at startup. If any are missing, raise a clear error — never silent fail.

---

## 5. Command Specification

### `/start`

```
Output:
Hello! 🏠 Real Estate AI Assistant

Available commands:
/summarize — Summarize a customer chat
/match — Find matching properties
/help — How to use
```

---

### `/summarize`

**Input format:**

```
/summarize
[paste full customer chat here]
```

**Process:**

1. Strip the command prefix
2. Validate that text follows the command
3. Send text to `ai/summarizer.py`
4. Format and return structured output

**Expected output (Telegram Markdown):**

```
📋 *Lead Summary*

💰 *Budget:* 25,000 THB/month
📍 *Location:* BTS Asok ± 2 stations
🏠 *Property Type:* 1BR Condo
📅 *Move-in Date:* Early next month (~Nov 1)
🔥 *Intent Level:* High
✅ *Recommended Next Step:* Send listings and schedule a viewing

💬 *Key Notes:*
• Has a cat
• Needs 1 parking space
• Prefers below floor 15
```

**Error handling:**

- No text after command → `"Please paste the customer chat after /summarize"`
- OpenAI error → `"Something went wrong. Please try again."`

---

### `/match`

**Input format (short):**

```
/match BTS Asok 25k 1BR pet-friendly parking
```

**Input format (detailed):**

```
/match
Budget 30,000 · Thonglor · 2BR · fully furnished
```

**Process:**

1. Receive requirement text
2. Pull property listings from Google Sheets via `data/sheets.py`
3. Send requirement + listings to `ai/matcher.py`
4. Format and return ranked results

**Expected output:**

```
🏠 *Results: 3 Matching Properties*

*1. Lumpini Ville Sukhumvit 77*
📍 BTS On Nut (2 stops from Asok)
💰 24,500 THB/month · 1BR · 35 sqm
✅ Pet-friendly · Parking included
📝 Floor 8 · Pool view · Fully furnished

*2. iDeo Mobi Sukhumvit*
...

---
💬 *Ready-to-send reply:*
Hi! Thank you for your interest.
Here are 3 options that match what you are looking for...
[copy-paste ready message for the client]
```

**Error handling:**

- Sheet unreachable → `"Could not load property data. Please contact admin."`
- No matches found → `"No properties matched those requirements. Try adjusting the criteria."`

---

### `/help`

Display a usage guide with real examples for both commands.

---

## 6. Google Sheets Schema

Sheet name: `Properties` (first sheet in the Spreadsheet)

| Column | Header       | Type    | Example                              |
| ------ | ------------ | ------- | ------------------------------------ |
| A      | name         | text    | Lumpini Ville Sukhumvit 77           |
| B      | location     | text    | Sukhumvit 77, Phrakanong             |
| C      | bts          | text    | On Nut                               |
| D      | price        | number  | 24500                                |
| E      | type         | text    | 1BR                                  |
| F      | size_sqm     | number  | 35                                   |
| G      | floor        | number  | 8                                    |
| H      | furnished    | text    | Fully / Partially / Unfurnished      |
| I      | pet_friendly | boolean | TRUE / FALSE                         |
| J      | parking      | boolean | TRUE / FALSE                         |
| K      | description  | text    | Pool view, quiet building, near Tops |
| L      | available    | boolean | TRUE / FALSE                         |

**Rules:**

- Row 1 is always the header row
- Only rows where `available = TRUE` are included in match results
- All columns are required — empty cells may cause matching errors

---

## 7. AI Layer Contracts

### summarizer.py

```python
def summarize_chat(raw_chat: str) -> dict:
    """
    Input:  raw customer chat string
    Output: structured dict with the following keys:
            budget, location, property_type, move_in,
            intent_level, next_step, notes (list of strings)
    """
```

- Loads prompt from `prompts/summarize.txt`
- Calls OpenAI with `response_format={"type": "json_object"}`
- Returns parsed dict — never a raw string

### matcher.py

```python
def match_properties(requirement: str, listings: list[dict]) -> dict:
    """
    Input:  requirement string + list of property dicts from Sheets
    Output: dict with keys:
            matches (list of top 3-5 properties with reasoning),
            reply_message (copy-paste ready string for the client)
    """
```

- Loads prompt from `prompts/match.txt`
- Injects listings as JSON into the prompt context
- Returns top 3–5 matches + a reply message

---

## 8. Security

- `ALLOWED_TELEGRAM_IDS` — whitelist of agent Telegram user IDs
- On every incoming message, check `update.effective_user.id` against the whitelist
- If not in whitelist → silently ignore or reply `"Access denied"`
- No customer data is stored anywhere — every request is stateless

---

## 9. Error Handling Rules

| Scenario                    | Behavior                                         |
| --------------------------- | ------------------------------------------------ |
| Missing env var at startup  | Raise immediately with a clear message           |
| OpenAI API timeout          | Retry once, then return user-facing error        |
| Google Sheets unreachable   | Return user-facing error, log full traceback     |
| Empty or garbage user input | Return usage hint — do not call OpenAI           |
| Unexpected exception        | Log full traceback, return generic error to user |

Never let the bot crash silently. Every error must be handled or logged.

---

## 10. Acceptance Criteria — MVP Complete When:

- [ ] `/start` responds instantly with the help menu
- [ ] `/summarize` with a real customer chat returns correct structured output
- [ ] `/match` with a short requirement returns 3 relevant listings
- [ ] `/match` output includes a copy-paste ready reply message
- [ ] Bot ignores messages from users not in `ALLOWED_TELEGRAM_IDS`
- [ ] Bot recovers gracefully from OpenAI errors without crashing
- [ ] Bot is deployed on Railway and running 24/7
- [ ] A non-technical agent can use both commands without any training

---

## 11. Deferred Features — Do Not Build Yet

| Feature                     | Why deferred                           |
| --------------------------- | -------------------------------------- |
| Web dashboard               | Adds weeks of work before validation   |
| LINE / Facebook integration | Telegram is sufficient for now         |
| Per-client customization    | Design for one client first            |
| Conversation memory         | Stateless is simpler and sufficient    |
| Automated follow-up         | Phase 4+                               |
| Real database               | Only after Sheets becomes a bottleneck |

---

_SPEC.md v1.0 — Real Estate AI Bot_
_Next document: TASKS.md_
(CLAUDE Sonnet 4.6)
