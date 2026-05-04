# AI Internal Tool for Real Estate Agencies

## Project Overview & Initial Roadmap

---

## 1. Project Summary

**Project Name:** AI Internal Assistant (Real Estate Teams)
**Type:** Internal Tool (Done-for-you solution, not SaaS at this stage)

**Goal:**
Build a lightweight AI-powered internal tool that helps real estate agents:

- Process leads faster
- Extract key information from conversations
- Match clients with suitable properties instantly

**Core Value Proposition:**
Reduce repetitive work and decision time for agents, enabling them to focus on closing deals.

---

## 2. Problem Statement

Real estate agencies (especially small teams) face:

- High volume of incoming chat messages (LINE, WhatsApp, Facebook)
- Time wasted reading long conversations
- Repetitive qualification questions (budget, location, move-in date)
- Slow response → lost leads
- Difficulty matching properties quickly from scattered data

---

## 3. Solution

A simple **AI-powered internal assistant** accessible via Telegram that:

### 1. Lead Summarization

- Input: Raw customer chat
- Output:
    - Budget
    - Location
    - Property type
    - Move-in date
    - Intent level
    - Suggested next action

---

### 2. Property Matching

- Input: Short requirement (e.g., “BTS Asok, 25k, 1BR”)
- Output:
    - Top 3–5 matching properties
    - Structured summary
    - Ready-to-send reply message

---

## 4. Target Users

- Small to mid-size real estate agencies
- Teams of 2–10 agents
- Agents dealing with rental/condo clients (especially high-frequency leads)

---

## 5. MVP Scope (Strict)

### Included:

- Telegram bot interface
- `/summarize` command
- `/match` command
- Google Sheets as database
- OpenAI API for reasoning

### Excluded (for now):

- No web dashboard
- No authentication system
- No multi-tenant architecture
- No integrations with LINE/Facebook
- No advanced automation

---

## 6. System Architecture

### Components:

**1. Interface Layer**

- Telegram Bot

**2. Backend**

- Python (single service)
- Handles commands and routing

**3. AI Layer**

- OpenAI API (LLM for:
    - summarization
    - recommendation)

**4. Data Layer**

- Google Sheets (property listings)

---

### Flow Overview

#### Summarization Flow:

1. User sends `/summarize + chat`
2. Backend sends text to LLM
3. LLM returns structured summary
4. Bot returns formatted result

---

#### Matching Flow:

1. User sends `/match + requirement`
2. Backend pulls data from Google Sheets
3. Sends requirement + data to LLM
4. LLM returns best matches + reply text
5. Bot returns result

---

## 7. Data Structure (Google Sheet)

Columns:

- name
- location
- price
- type
- BTS
- description

---

## 8. Success Criteria (Phase 1)

- Agent can use tool without training
- Summarization output is usable immediately
- Matching results feel “relevant enough”
- Demo impresses client within 3 minutes
- First 1–3 paying clients acquired

---

## 9. Development Roadmap

### Phase 1: MVP Build (Day 1–3)

**Day 1**

- Setup project structure
- Create Telegram bot
- Implement `/summarize`

**Day 2**

- Integrate Google Sheets
- Implement `/match`

**Day 3**

- Improve prompts
- Clean output formatting
- Internal testing

---

### Phase 2: First Client Deployment (Day 4–7)

- Import real client property data
- Customize prompts per agency
- Run live demo
- Close first deal
- Deploy working version

---

### Phase 3: Refinement (Week 2–3)

- Improve matching accuracy
- Add basic filtering (price/location)
- Improve response formatting
- Add simple logging (optional)

---

### Phase 4: Expansion (Optional)

Only after validation:

- Add chatbot (customer-facing)
- Add CRM-lite features
- Add memory per client
- Move from Google Sheets → database
- Multi-agent workflows

---

## 10. Key Risks

- Overengineering too early
- Poor data quality from clients
- Irrelevant property matching
- Slow response time from API
- Lack of real user feedback

---

## 11. Development Principles

- Ship fast, not perfect
- Optimize for demo, not scalability
- Solve one real problem deeply
- Avoid feature creep
- Validate with real users ASAP

---

## 12. Next Actions

- Finalize tech stack (Python confirmed)
- Setup repository structure
- Assign development tasks:
    - Bot setup
    - LLM integration
    - Sheet integration

- Begin MVP build immediately

---

## Final Note

This is not a product yet.
This is a **revenue-first tool** designed to:

1. Validate demand
2. Generate early income
3. Build real-world use cases

Only after that, it evolves into a scalable system.

---
