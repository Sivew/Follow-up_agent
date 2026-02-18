# Follow-up Agent

A standalone, resellable SMS automation bot designed for real estate lead follow-up.
Built with Python (Flask), Twilio, and Redis for scheduling.

## Features
- **Instant Response**: Auto-replies to inbound leads.
- **Drip Campaigns**: Schedules follow-up messages (10 mins, 24 hours, etc.).
- **Human Handoff**: Detects keywords (e.g., "call me") and alerts a human.
- **Resellable**: Configurable via `.env` file (white-label ready).
- **Stateless/Stateful**: Uses Redis for conversation state and scheduling.

## Architecture
- `app.py`: Main Flask application handling Twilio webhooks.
- `worker.py`: Background worker for sending scheduled follow-ups.
- `config.py`: Configuration loader.
- `utils.py`: Helper functions (logging, validation).

## Setup
1. `pip install -r requirements.txt`
2. `cp .env.example .env` (Fill in Twilio credentials)
3. `docker-compose up -d` (Runs Flask + Redis + Worker)
