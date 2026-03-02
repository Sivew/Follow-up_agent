# Sarah Dashboard Plan 📊

## 🎯 Objective
Create a simple, real-time web dashboard to monitor Sarah's health, follow-up stats, and message logs. This will help the user trust that the automation is working without needing to check logs manually.

## 🏗️ Architecture
- **Framework:** Extend the existing Flask app (`Follow-up_agent/app.py`).
- **Frontend:** Lightweight HTML/JS (using Bootstrap or Tailwind via CDN) served by Flask.
- **Data Source:** Core API (via `SarahDBClient`) + Local Status Checks.

---

## 🛠️ Implementation Steps

### 1. Update `sarah_db_client.py`
Add methods to fetch message history and dashboard stats.

```python
    def get_messages(self, limit: int = 50) -> dict:
        """Fetch recent message logs."""
        url = f"{self.BASE_URL}/messages?limit={limit}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"messages": [], "error": str(e)}
```

### 2. Backend Routes (`app.py`)
Add these new endpoints to serve the dashboard data:

#### `GET /`
- **Response:** Renders `dashboard.html`.

#### `GET /api/stats`
- **Purpose:** Return live counts of leads in automation.
- **Logic:**
    1. Fetch all customers (or active conversations).
    2. Count based on `intent` field:
        - `WAITING_FOR_ANSWER`
        - `FOLLOWUP_1`
        - `FOLLOWUP_2`
        - `ENGAGED` (Replied)
    3. Return JSON: `{"waiting": 5, "stage_1": 2, "stage_2": 1, "engaged": 12}`

#### `GET /api/logs`
- **Purpose:** Show recent activity.
- **Logic:** Call `db_client.get_messages(limit=20)` and return the list.

#### `GET /api/health`
- **Purpose:** Check if everything is green.
- **Logic:**
    - Check if `cron_worker.py` is running (check log file timestamp or process list).
    - Check if Redis/DB connection is alive.
    - Return: `{"status": "healthy", "last_run": "2 mins ago"}`

### 3. Frontend (`templates/dashboard.html`)
Create a single HTML file with auto-refresh (every 30s).

**Wireframe Layout:**

| Header: Sarah Automation Status [🟢 Online] |
| :--- |
| **Stats Row:** |
| [ 🕒 Waiting: 12 ] [ 📧 Follow-up 1: 3 ] [ 🚀 Follow-up 2: 1 ] [ ✅ Engaged: 45 ] |
| |
| **Recent Logs (Last 20):** |
| [14:05] Outbound to +1555...: "Hi John, checking in..." |
| [14:02] Inbound from +1555...: "Yes, interested." |
| ... |

---

## 📝 Developer Checklist

1.  [ ] **Modify `sarah_db_client.py`:** Add `get_messages()` method.
2.  [ ] **Create `templates/` folder:** Add `dashboard.html`.
3.  [ ] **Update `app.py`:**
    -   Add `render_template` import.
    -   Add `/`, `/api/stats`, `/api/logs` routes.
4.  [ ] **Update `requirements.txt`:** No new requirements needed (Flask is already there).
5.  [ ] **Test:** Ensure dashboard loads and data refreshes.

## 💡 Notes for Dev
- Use **Bootstrap 5 CDN** for quick styling.
- For the "Health" check, you can check the modification time of `sarah_worker.log`. If it's older than 10 mins, show status as **🔴 Stalled**.
- Keep it simple. No complex React/Vue build steps. Just server-side rendered HTML or simple fetch() in script tag.
