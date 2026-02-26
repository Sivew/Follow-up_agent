# AGENTS.md - Developer Guide for Follow-up Agent

## Project Overview

SMS automation bot for real estate lead follow-up. Built with Python (Flask), Twilio, Redis/RQ, and OpenAI. Uses Core API (Sarah DB) for CRM functionality.

## Architecture

- `app.py` - Main Flask app handling Twilio SMS webhooks with AI-generated replies
- `main.py` - Simplified inbound SMS handler (logs to Core API, resets state on reply)
- `cron_worker.py` - Cron job that checks unresponsive leads and sends follow-ups
- `tasks.py` - RQ worker for scheduled follow-ups
- `sarah_db_client.py` - API client for Lead Conversation Management System
- `utils.py` - Helper functions (logging, human handoff detection)

## State Machine (via `intent` Field)

The Core DB lacks native fields for `automation_status` or `followup_count`. The system uses the **`intent`** field to track automation state:

| Intent | Meaning | Action |
| :--- | :--- | :--- |
| `WAITING_FOR_ANSWER` | AI asked question, waiting for user | If >30m, send Follow-up 1 |
| `FOLLOWUP_1` | First nudge sent | If >24h, send Follow-up 2 |
| `FOLLOWUP_2` | Second nudge sent | If >24h, move to NURTURE |
| `NURTURE` | Lead unresponsive (Soft Close) | No action |
| `ENGAGED` | User replied | Stop all automation |

`cron_worker.py` handles state transitions. `main.py` resets to `ENGAGED` on reply.

## Development Commands

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Locally
```bash
# Flask dev server
python app.py

# Or with Gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 main:app

# Run cron worker manually
python3 cron_worker.py
```

### Docker
```bash
docker-compose up -d
docker-compose logs -f
docker-compose build --no-cache
```

### Linting
```bash
flake8 .
flake8 --max-line-length=120 .
```

### Testing
```bash
pytest
pytest tests/test_sarah_db_client.py
pytest tests/test_sarah_db_client.py::TestSarahDBClient::test_create_customer
pytest --cov=. --cov-report=term-missing
pytest -k "test_create"
```

## Code Style Guidelines

### General
- Python 3.10+
- Follow PEP 8 with 120 character line length
- Use type hints where beneficial
- Write docstrings for public functions
- No magic numbers - use constants or config

### Imports
- Standard library first
- Third-party packages second
- Local imports third
- Sort alphabetically within groups

### Naming Conventions
- `snake_case` for functions, variables, methods
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Descriptive names: `customer_id` not `cid`
- Private methods: `_internal_method()`

### Error Handling
- Use specific exception types
- Log errors with context before re-raising
- Return appropriate HTTP status codes
- Never expose secrets in error messages

### Flask Routes
- Use appropriate HTTP methods
- Validate input early
- Return proper status codes and responses

### Logging
- Use standard `logging` module
- Include relevant context (IDs, phone numbers)

## Environment Variables

Required in `.env`:
```
CORE_API_URL=https://lpodk9ddwa.execute-api.ca-central-1.amazonaws.com/prod
CORE_API_KEY=your_api_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1xxxxx
AGENT_NAME=Sarah
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
REDIS_URL=redis://localhost:6379/0
```

## Known Issues / Workarounds

1. **API Endpoint 403**: `GET /conversations?status=active` returns 403. Workaround: `cron_worker.py` calls `GET /customers` and iterates each to fetch context individually (O(N) but functional).

2. **Dependencies**: Ensure `twilio`, `requests`, and `python-dotenv` are installed alongside requirements.txt packages.

## API Documentation

See `API_REFERENCE.md` for quick reference to Core API endpoints.

Full API documentation: `API Usage Guide_v2.md`
