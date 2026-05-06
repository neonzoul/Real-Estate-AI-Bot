# TASKS.md — Development Task Breakdown

## Real Estate AI Bot · Day-by-Day Execution Plan

**Reference:** SPEC.md (read first)
**Format:** Each task has a clear input, output, and done condition.
**Rule:** Do not start the next task until the current one passes its done condition.

---

## Phase 1 — MVP Build (Day 1–3)

---

### DAY 1 — Bot Running + /summarize Working

---

#### TASK 1.1 — Project Setup

**What to do:**

- Create the directory structure exactly as defined in SPEC.md Section 3
- Initialize git repository
- Create `.gitignore` with: `.env`, `service_account.json`, `__pycache__/`, `*.pyc`, `.DS_Store`
- Create `requirements.txt` with initial dependencies:
    ```
    python-telegram-bot==21.11.1
    openai==1.12.0
    gspread==6.0.2
    google-auth==2.28.0
    python-dotenv==1.0.1
    httpx==0.27.2
    ```
    Notes on deviations from the original spec pins:
    - `python-telegram-bot` bumped from `20.7` → `21.11.1`. 20.7 has a Python 3.13 incompatibility (`Updater.__slots__` regression) that crashes at startup. The API surface used by this project is unchanged across 20.x→21.x.
    - `httpx==0.27.2` pinned explicitly. PTB 21.x allows `httpx~=0.27` (resolves to 0.28+), but `openai==1.12.0` calls `httpx.Client(proxies=...)` and the `proxies` kwarg was removed in httpx 0.28. 0.27.2 is the intersection that satisfies both.
- Create `.env.example` as defined in SPEC.md Section 4
- Create empty `__init__.py` files in `bot/`, `ai/`, `data/`

**Done when:**

- [x] Directory structure matches SPEC.md exactly
- [x] `git init` done, `.gitignore` in place
- [x] `pip install -r requirements.txt` runs without errors
- [x] No `.env` file committed to git

---

#### TASK 1.2 — Config & Environment Validation

**File:** `config.py`

**What to do:**
Write a config module that loads all env vars and raises a clear error at startup if any are missing.

```python
# Expected behavior
from config import config

config.TELEGRAM_BOT_TOKEN   # string
config.OPENAI_API_KEY       # string
config.GOOGLE_SHEET_ID      # string
config.SERVICE_ACCOUNT_PATH # string (path to json file)
config.ALLOWED_IDS          # set of integers
```

**Done when:**

- [x] Running with a complete `.env` loads all values correctly
- [x] Running with a missing variable raises `EnvironmentError` with the variable name in the message
- [x] `ALLOWED_TELEGRAM_IDS` is parsed into a `set` of `int`

---

#### TASK 1.3 — Telegram Bot Skeleton

**File:** `main.py`, `bot/handlers.py`

**What to do:**

- Create bot application using `python-telegram-bot`
- Register handlers for: `/start`, `/summarize`, `/match`, `/help`
- Implement access control — every handler checks user ID against `config.ALLOWED_IDS` first
- For now, `/summarize`, `/match`, `/help` can just reply `"Coming soon"` as placeholder
- `/start` must return the full welcome message as defined in SPEC.md Section 5

**Done when:**

- [x] Bot starts without errors (`python main.py`)
- [x] `/start` returns correct welcome message
- [x] A user ID not in `ALLOWED_IDS` gets no response or `"Access denied"`
- [x] An allowed user ID gets the placeholder response for other commands

---

#### TASK 1.4 — Summarize Prompt

**File:** `prompts/summarize.txt`

**What to do:**
Write the prompt that instructs the model to extract lead information from a raw chat.

The prompt must:

- Instruct the model to return **only valid JSON** — no explanation, no markdown fences
- Define the exact output schema:
    ```json
    {
        "budget": "25,000 THB/month",
        "location": "BTS Asok ± 2 stations",
        "property_type": "1BR Condo",
        "move_in": "Early November",
        "intent_level": "High",
        "next_step": "Send listings and schedule a viewing",
        "notes": [
            "Has a cat",
            "Needs 1 parking space",
            "Prefers below floor 15"
        ]
    }
    ```
- Handle cases where information is not mentioned — use `"Not specified"` for strings, `[]` for arrays
- Be explicit that `intent_level` must be one of: `Low`, `Medium`, `High`

**Done when:**

- [x] Prompt file exists at `prompts/summarize.txt`
- [x] Manually pasting the prompt + a sample chat into ChatGPT returns valid JSON matching the schema
- [x] Missing fields return `"Not specified"` not `null` or empty string

---

#### TASK 1.5 — Summarizer Module

**File:** `ai/summarizer.py`

**What to do:**
Implement the `summarize_chat` function as defined in SPEC.md Section 7.

```python
def summarize_chat(raw_chat: str) -> dict:
    # Load prompt from prompts/summarize.txt
    # Call OpenAI with response_format={"type": "json_object"}
    # Parse and return dict
    # Raise exception on failure — do not return error strings
```

**Rules:**

- Always use `response_format={"type": "json_object"}` — never parse freeform text
- Load prompt from file, not hardcoded in the function
- Raise a descriptive exception on failure — let the handler decide what to show the user

**Done when:**

- [x] `summarize_chat("Hi I'm looking for a 1BR near BTS Asok, budget 25k")` returns a valid dict
- [x] All keys from the schema are present in the output
- [x] Function raises an exception (not returns `None`) on OpenAI failure

---

#### TASK 1.6 — Output Formatter for /summarize

**File:** `bot/formatters.py`

**What to do:**
Implement `format_summary(data: dict) -> str` that converts the dict from `summarize_chat` into a Telegram Markdown string matching the format in SPEC.md Section 5.

**Done when:**

- [x] Output uses Telegram MarkdownV2 or Markdown (pick one and be consistent)
- [x] All fields are displayed with the correct emoji and label
- [x] `notes` list renders as bullet points
- [x] Empty `notes` does not show the notes section

---

#### TASK 1.7 — Wire /summarize End-to-End

**File:** `bot/handlers.py`

**What to do:**
Connect the summarize handler to the full pipeline:

1. Extract text after the command
2. If no text → reply with usage hint
3. Send typing action while processing
4. Call `summarize_chat(text)`
5. Format with `format_summary(result)`
6. Reply with formatted output
7. On any exception → reply with `"Something went wrong. Please try again."`

**Done when:**

- [x] `/summarize [chat text]` returns correct formatted summary
- [x] `/summarize` with no text returns the usage hint
- [x] An OpenAI failure returns the error message — bot does not crash
- [x] Typing indicator appears while processing

---

### DAY 2 — Google Sheets Connected + /match Working

---

#### TASK 2.1 — Google Sheets Connector

**File:** `data/sheets.py`

**What to do:**
Implement `get_listings() -> list[dict]` that:

- Authenticates using the Service Account JSON file
- Opens the sheet by `GOOGLE_SHEET_ID` from config
- Reads all rows from the `Properties` sheet
- Converts each row to a dict using the header row as keys
- Filters out rows where `available != "TRUE"`
- Returns a list of clean dicts

```python
def get_listings() -> list[dict]:
    # Returns only available listings
    # Each dict has keys: name, location, bts, price, type,
    #                     size_sqm, floor, furnished,
    #                     pet_friendly, parking, description
```

**Done when:**

- [x] `get_listings()` returns a non-empty list when the sheet has data
- [x] Rows with `available = FALSE` are excluded from results
- [x] Function raises a clear exception if authentication fails or sheet is not found
- [x] `price` is returned as a number (int or float), not a string

---

#### TASK 2.2 — Match Prompt

**File:** `prompts/match.txt`

**What to do:**
Write the prompt that instructs the model to rank properties and generate a client reply.

The prompt must:

- Accept two inputs injected at runtime: `{requirement}` and `{listings_json}`
- Instruct the model to return **only valid JSON** — no explanation, no markdown fences
- Define the exact output schema:
    ```json
    {
        "matches": [
            {
                "rank": 1,
                "name": "Lumpini Ville Sukhumvit 77",
                "reason": "Matches budget, pet-friendly, has parking",
                "highlight": "Floor 8 · Pool view · Fully furnished"
            }
        ],
        "reply_message": "Hi! Thank you for your interest. Here are 3 options..."
    }
    ```
- Limit matches to a maximum of 5
- If no listings match, return `"matches": []` and a polite `reply_message`
- `reply_message` must be professional and ready to send to a client without editing

**Done when:**

- [x] Prompt file exists at `prompts/match.txt`
- [x] Manually testing the prompt with sample listings returns valid JSON matching the schema
- [x] `reply_message` sounds natural and professional — not robotic

---

#### TASK 2.3 — Matcher Module

**File:** `ai/matcher.py`

**What to do:**
Implement `match_properties` as defined in SPEC.md Section 7.

```python
def match_properties(requirement: str, listings: list[dict]) -> dict:
    # Load prompt from prompts/match.txt
    # Inject requirement and listings (as JSON) into the prompt
    # Call OpenAI with response_format={"type": "json_object"}
    # Return parsed dict with keys: matches, reply_message
```

**Rules:**

- Convert `listings` to JSON string before injecting into prompt
- If `listings` is empty, skip the OpenAI call and return a no-results response immediately
- Raise exception on OpenAI failure

**Done when:**

- [x] `match_properties("BTS Asok 25k 1BR", listings)` returns a dict with `matches` and `reply_message`
- [x] Returned `matches` list contains 1–5 items
- [x] Empty `listings` input returns `{"matches": [], "reply_message": "..."}` without calling OpenAI

---

#### TASK 2.4 — Output Formatter for /match

**File:** `bot/formatters.py`

**What to do:**
Implement `format_matches(data: dict) -> str` that converts the matcher output into a readable Telegram message matching the format in SPEC.md Section 5.

**Rules:**

- Show rank, name, location, price, key features for each match
- Separate the `reply_message` section with a divider
- If `matches` is empty, show a friendly no-results message instead

**Done when:**

- [x] Output matches the format in SPEC.md exactly
- [x] Each property is clearly separated
- [x] `reply_message` appears after a `---` divider
- [x] Empty matches shows the no-results message

---

#### TASK 2.5 — Wire /match End-to-End

**File:** `bot/handlers.py`

**What to do:**
Connect the match handler to the full pipeline:

1. Extract text after the command
2. If no text → reply with usage hint
3. Send typing action while processing
4. Call `get_listings()` from `data/sheets.py`
5. Call `match_properties(text, listings)` from `ai/matcher.py`
6. Format with `format_matches(result)`
7. Reply with formatted output
8. On Sheets failure → reply `"Could not load property data. Please contact admin."`
9. On OpenAI failure → reply `"Something went wrong. Please try again."`

**Done when:**

- [x] `/match BTS Asok 25k 1BR` returns ranked properties with reply message
- [x] `/match` with no text returns the usage hint
- [x] Sheet failure returns the correct error message — bot does not crash
- [x] OpenAI failure returns the correct error message — bot does not crash

---

### DAY 3 — Polish + Deploy

---

#### TASK 3.1 — Implement /help

**File:** `bot/handlers.py`

**What to do:**
Return a clear usage guide with real examples for both commands.

```
🤖 *How to use*

*/summarize*
Paste a customer chat to get a structured lead summary.

Example:
/summarize
Hi, I'm looking for a 1BR near BTS Asok...

*/match*
Describe what the client needs to find matching properties.

Example:
/match BTS Asok 25k 1BR pet-friendly parking
```

**Done when:**

- [x] `/help` returns the full guide
- [x] Examples are real and usable

---

#### TASK 3.2 — Error Handling Audit

**What to do:**
Go through every handler and confirm it follows the error rules in SPEC.md Section 9.

Checklist:

- [x] No unhandled exceptions can crash the bot process
- [x] Every exception is caught at the handler level
- [x] Every caught exception logs the full traceback to console
- [x] User always receives a readable message — never a Python error trace

Audit findings: a real bug was found and fixed during the audit — `_send_typing` was calling itself (infinite recursion), which the broad `except` was swallowing as `"send_action failed"`. The persistent warning seen during Day 2 testing was the recursion limit being hit, not a network issue. Fix: helper now correctly calls `update.message.chat.send_action(ChatAction.TYPING)`.

---

#### TASK 3.3 — Internal Testing with Real Data

**What to do:**
Test both commands with real customer chat samples and real property listings.

Test cases for `/summarize`:

- [ ] Long chat with all information present → all fields populated
- [ ] Short chat with missing fields → missing fields return `"Not specified"`
- [ ] Chat in Thai → output still in correct JSON format

Test cases for `/match`:

- [x] Requirement that matches 3+ listings → returns top 3–5
- [x] Requirement that matches nothing → returns no-results message
- [ ] Very short requirement (e.g., `"Asok 1BR"`) → still returns results

---

#### TASK 3.4 — Deploy to Railway

**What to do:**

- Create `Procfile`:
    ```
    worker: python main.py
    ```
- Push repository to GitHub
- Create new project on Railway, connect to GitHub repo
- Add all environment variables in Railway dashboard (same as `.env`)
- Deploy and confirm bot is running in Railway logs

**Done when:**

- [ ] Railway deployment succeeds with no errors
- [ ] Bot responds to `/start` on Telegram after deployment
- [ ] Logs in Railway show the bot is running
- [ ] Bot keeps running after closing your local machine

---

#### TASK 3.5 — Final Acceptance Check

Run through every acceptance criterion from SPEC.md Section 10:

- [ ] `/start` responds instantly with the help menu
- [ ] `/summarize` with a real customer chat returns correct structured output
- [ ] `/match` with a short requirement returns 3 relevant listings
- [ ] `/match` output includes a copy-paste ready reply message
- [ ] Bot ignores messages from users not in `ALLOWED_TELEGRAM_IDS`
- [ ] Bot recovers gracefully from OpenAI errors without crashing
- [ ] Bot is deployed on Railway and running 24/7
- [ ] A non-technical agent can use both commands without any training

**MVP is complete when all boxes above are checked.**

---

## Phase 2 — First Client Deployment (Day 4–7)

---

#### TASK 4.1 — Import Client Property Data

**What to do:**

- Get real property listings from the client
- Create a new Google Sheet following the schema in SPEC.md Section 6
- Import all listings
- Share the sheet with the Service Account email
- Update `GOOGLE_SHEET_ID` in Railway environment variables

**Done when:**

- [ ] `/match` returns real client listings (not sample data)
- [ ] Client can open and edit the sheet themselves

---

#### TASK 4.2 — Customize Prompts for Client Context

**What to do:**
Review `prompts/summarize.txt` and `prompts/match.txt` and adjust for the client's specific market:

- Area names relevant to their listings
- Price ranges typical for their inventory
- Tone of `reply_message` matching their brand voice

**Done when:**

- [ ] `/match` reply message sounds like it came from their agency — not a generic bot
- [ ] Area names in the output match how the client actually refers to locations

---

#### TASK 4.3 — Live Demo with Client

**What to do:**
Run a live demo using:

1. A real customer chat the client provides → `/summarize`
2. A real requirement from their pipeline → `/match`

**Done when:**

- [ ] Client confirms the summary is accurate
- [ ] Client confirms the matches are relevant
- [ ] Client confirms the reply message is usable
- [ ] Demo completed in under 3 minutes

---

#### TASK 4.4 — Handover

**What to do:**

- Add the client's agents to `ALLOWED_TELEGRAM_IDS` in Railway
- Show agents how to use `/summarize` and `/match` (5-minute walkthrough)
- Confirm they can use it independently

**Done when:**

- [ ] At least one agent successfully uses both commands without help
- [ ] Client knows how to add new listings to the sheet themselves

---

## Phase 3 — Refinement (Week 2–3)

Tasks in this phase are defined after Phase 2 feedback. Likely candidates:

- Improve matching accuracy based on real usage
- Add basic pre-filtering (price range, area) before sending to OpenAI — reduces cost and improves speed
- Improve response formatting based on agent feedback
- Add request logging to a separate Sheet tab for usage tracking

---

_TASKS.md v1.0 — Real Estate AI Bot_
_Next document: SCHEMA.md_
