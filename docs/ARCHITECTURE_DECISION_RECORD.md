# Architecture Decision Record (ADR) - Sarah Follow-Up Agent

## ADR 001: Decoupling Automation State from Conversational Intent

**Date:** March 6, 2026
**Status:** Accepted / Active Directive
**Authors:** Shiva & Wonderbot

### 1. The Context & The Problem
In V1 and V2.0 of the Sarah project, we utilized the `intent` column in the `Conversations` database table as a hack to act as a State Machine. 
The cron worker (`cron_worker.py`) relied on the `intent` field string (e.g., `WAITING_FOR_ANSWER` -> `FOLLOWUP_1` -> `NURTURE`) to determine when to trigger the 5-minute, 24-hour, and 3-day follow-up messages.

**The Breaking Point:** As we upgraded the "Brain" of Sarah (adding Make.com voice integration, DISCOVER/QUALIFY prompts, etc.), the LLM began correctly classifying the user's *actual conversational intent* (e.g., "interested in pricing", "wants a demo"). When the AI updated the `intent` field with these natural conversational states, it overwrote the state machine (e.g., `WAITING_FOR_ANSWER`), instantly breaking the Cron Worker's timing logic. 
Every new prompt feature caused the cron relay to fail.

### 2. The Decision (The Core Truth)
Going forward, we must strictly decouple **The Relay (Automation State)** from **The Brain (Conversational Data)**. They cannot share the same database field.

All bridging actions and future code MUST anchor to this dual-field truth:

#### A. The Relay: `status` (or dedicated `automation_stage`)
This field strictly controls the automated drip sequence. The Cron Worker only cares about this field.
**Valid States:**
*   `ACTIVE_PHASE_1`: Waiting for 5-minute non-response threshold.
*   `ACTIVE_PHASE_2`: Waiting for 24-hour non-response threshold.
*   `ACTIVE_PHASE_3`: Waiting for 3-day non-response threshold.
*   `NURTURE`: Completed all automated sequences (cold).
*   `ENGAGED`: The user has replied or answered a call. **(This instantly halts the cron worker from sending drip messages).**
*   `CLOSED`: Manually closed/won.

#### B. The Brain: `intent`
This field is strictly for the LLM to classify what the user wants based on natural language analysis. The Cron Worker must **ignore** this field.
**Valid Examples (Determined by LLM):**
*   `pricing_inquiry`
*   `demo_requested`
*   `technical_question`
*   `not_interested`
*   `initial_contact`

### 3. Implementation Rules for Developers
*   **Rule 1 (Inbound Webhooks/SMS/Voice):** Whenever a human sends an SMS or answers a voice call, the script handling that inbound event (`app.py` or Make.com webhook) MUST immediately set `status = "ENGAGED"`. This acts as the kill-switch for the automated drip.
*   **Rule 2 (Outbound Cron):** `cron_worker.py` must ONLY evaluate the `status` field to execute `followup_strategy.json`. When the worker fires a message, it updates `status` to the next phase (e.g., `ACTIVE_PHASE_2`).
*   **Rule 3 (LLM Context Updates):** When `update_conversation_state()` is called to save the LLM's analysis of the conversation, it should freely overwrite the `intent`, `summary`, `sentiment`, and `product_interest` fields, but it should **never** touch the `status` field (unless explicitly switching them to `ENGAGED` or `CLOSED`).

### 4. Consequences
By implementing this split, prompt engineering and conversation tracking can evolve indefinitely without ever breaking the core 5m/24h/3d bridging actions again.
