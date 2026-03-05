# Follow-up Agent

SMS automation bot for real estate lead follow-up. Built with Python (Flask), Twilio, Redis, and OpenAI.

## Features
- Auto-replies to inbound SMS with AI-generated responses
- Scheduled follow-up campaigns (30min, 24h, 48h)
- Calendar integration via Make.com webhooks
- Voice call logging (optional Vapi integration)
- CRM auto-enrichment (extracts name/email from conversations)

## Quick Start

```bash
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d --build
```

## Documentation

- `docs/README_DEVELOPER.md` - Architecture & development guide
- `docs/AGENTS.md` - Code style & testing for AI agents
- `docs/DEPLOYMENT_SOP.md` - Production deployment checklist
- `docs/MAKE_SETUP.md` - Make.com webhook configuration
- `docs/API.md` - Quick API reference
- `docs/API Usage Guide_v2.md` - Detailed API documentation

## Configuration

See `.env.example` for all available options. Critical variables:
- `MAKE_WEBHOOK_URL` - **Required per client** (calendar integration)
- `CORE_API_URL` - Sarah DB API endpoint
- `CORE_API_KEY` - API authentication
- `TWILIO_*` - SMS integration
- `OPENAI_API_KEY` - AI responses
