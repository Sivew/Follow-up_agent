# API Reference

This project uses the Core API (Sarah DB) for CRM functionality.

## API Documentation

The complete API documentation is available in: **`API Usage Guide_v2.md`**

That file contains:
- Authentication instructions
- All available endpoints (Customers, Context, Messages, Conversations)
- Request/response formats
- Common workflows
- Error codes

## Key Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/context/{identifier}?by=phone_normalized` | Get customer context by phone |
| `POST` | `/context/{customer_id}/update` | Update conversation state |
| `POST` | `/log` | Log inbound/outbound messages |
| `POST` | `/customers` | Create new customer |
| `GET` | `/customers` | List all customers |

## Important Notes

1. **URL Encoding**: When using phone numbers with `+`, URL-encode them (e.g., `+14165551234` → `%2B14165551234`)

2. **phone_normalized**: Use `phone_normalized` (not `phone`) for phone lookups

3. **403 Workaround**: The `/conversations?status=active` endpoint may return 403. The `cron_worker.py` uses a workaround: fetches all customers via `/customers` and iterates to get context individually.
