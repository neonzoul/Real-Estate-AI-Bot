# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current State

**Day 1 complete.** Bot runs, `/start` and `/help` reply, `/summarize` performs end-to-end OpenAI extraction, `/match` is a `"Coming soon"` placeholder. Day 2 (Google Sheets connector + `/match` wiring) and Day 3 (polish + Railway deploy) remain. Follow the day-by-day plan in [doc/TASKS.md](doc/TASKS.md) and the contracts in [doc/SPEC.md](doc/SPEC.md) and [doc/Schema.md](doc/Schema.md).

### Deviations from spec already in code

- `python-telegram-bot` is pinned to **`21.11.1`**, not the spec's `20.7`. Reason: 20.7 has a Python 3.13 incompatibility (`Updater.__slots__` regression) that crashes at startup. The API surface used (`ApplicationBuilder`, `CommandHandler`, `ContextTypes`, `ChatAction`, `ParseMode`) is unchanged across 20.x→21.x.
- `httpx==0.27.2` is pinned explicitly. Reason: PTB 21.x allows `httpx~=0.27` (which resolves to 0.28+), but `openai==1.12.0` calls `httpx.Client(proxies=...)` — the `proxies` kwarg was removed in httpx 0.28. Pinning to 0.27.2 is the intersection that satisfies both.

## Authoritative Documents — Read Before Coding

The specs are the source of truth and are tightly coupled. Read them in this order:

1. [doc/SPEC.md](doc/SPEC.md) — Master blueprint (project structure, tech stack, command behavior, error rules, acceptance criteria).
2. [doc/Schema.md](doc/Schema.md) — Every data shape: Sheets columns, internal listing dict, summarizer/matcher I/O, Telegram message formats, error message strings, config object shape.
3. [doc/Prompts.md](doc/Prompts.md) — Full prompt text for `summarize.txt` and `match.txt`, plus the variable-injection pattern.
4. [doc/TASKS.md](doc/TASKS.md) — Ordered task list with done-conditions per step.
5. [doc/Project Initial.md](doc/Project%20Initial.md) — Background and roadmap context.

If a schema or behavior must change, **update the spec first, then the code** — never let them drift.

## Planned Architecture

A single-process Python service that runs a Telegram bot. Two user-facing commands drive the entire system:

- `/summarize <chat>` → `bot/handlers.py` → `ai/summarizer.py` (loads `prompts/summarize.txt`, calls OpenAI in JSON mode) → `bot/formatters.py:format_summary` → Telegram reply.
- `/match <requirement>` → `bot/handlers.py` → `data/sheets.py:get_listings()` (filters `available != TRUE`) → `ai/matcher.py` (loads `prompts/match.txt`, injects `{requirement}` and `{listings}`, calls OpenAI in JSON mode) → `bot/formatters.py:format_matches` → Telegram reply.

Layer responsibilities are strict: `bot/` only handles Telegram I/O and formatting, `ai/` only does OpenAI calls and prompt loading, `data/` only talks to Sheets, `config.py` is the only place env vars are read. No customer data is persisted — every request is stateless.

## Project Conventions That Are Easy to Get Wrong

- **Prompts are files, not strings.** Prompt text lives in `prompts/*.txt` and is loaded at runtime. Never hardcode prompt text inside Python. To improve output quality, edit the prompt file — not the Python code.
- **OpenAI calls always use `response_format={"type": "json_object"}`.** The summarizer and matcher return parsed dicts, never raw text. Failures raise exceptions; handlers convert exceptions to user-facing strings.
- **Error message strings are fixed.** The exact wording for each error case is defined in [doc/Schema.md §6](doc/Schema.md). Use those strings verbatim — do not paraphrase.
- **Telegram parse mode is `Markdown`, not `MarkdownV2`.** Pick `Markdown` and stay consistent across all formatters.
- **Access control on every handler.** Every handler must check `update.effective_user.id` against `config.ALLOWED_IDS` (a `set[int]` parsed from the comma-separated `ALLOWED_TELEGRAM_IDS` env var) before doing any work.
- **Sheets type-casting is the connector's job.** `data/sheets.py` casts `"24500"` → `int`, `"TRUE"`/`"FALSE"` → `bool`, drops the `available` column after filtering. Downstream code expects the typed dict shape in [doc/Schema.md §2](doc/Schema.md).
- **Config validates at startup.** Missing env vars raise `EnvironmentError` with the variable name. Never silent-fail.
- **Ship-fast philosophy.** This is an MVP optimized for a 3-minute demo, not scalability. Avoid premature abstraction, per-client customization, multi-tenancy, or anything in the deferred list ([doc/SPEC.md §11](doc/SPEC.md)).

## Commands

```
pip install -r requirements.txt   # Install deps (use a venv)
python main.py                    # Start the bot (long-running process)
```

No test runner, lint, or build script is specified yet — `tests/test_summarizer.py` and `tests/test_matcher.py` are listed in the spec's structure but no framework is chosen and no test files exist on disk. If you add tests, pick `pytest` and document the invocation here.

## Required Environment Variables

Defined in [doc/SPEC.md §4](doc/SPEC.md). All five are required; startup must fail loudly if any are missing:

```
TELEGRAM_BOT_TOKEN
OPENAI_API_KEY
GOOGLE_SHEET_ID
GOOGLE_SERVICE_ACCOUNT_JSON   # path to service_account.json
ALLOWED_TELEGRAM_IDS          # comma-separated integers
```

`.env` and `service_account.json` are secrets — they must be in `.gitignore` and never committed.

## Deployment

Target is Railway.app via GitHub auto-deploy. The process is run as a `worker` (not `web`) — the Procfile entry is `worker: python main.py`. Env vars are set in the Railway dashboard, not committed.
