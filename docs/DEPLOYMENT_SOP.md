# Sarah Agent Deployment SOP 🚀

**STOP! READ THIS BEFORE DEPLOYING.**
Every deployment of the Follow-up Agent (`follow-up_agent_web_1`) changes its internal IP address.
If you do not follow these steps, Nginx will point to a dead IP, and **Sarah will go silent.**

## 1. deployment (The Update)
```bash
cd /home/ubuntu/.openclaw/workspace/Follow-up_agent
docker-compose down
docker-compose up -d --build
```

## 2. 🚨 CRITICAL: Fix Nginx Connection 🚨
**Why?** Nginx caches the old container IP. The new container has a different IP. You MUST reload Nginx to force a DNS lookup.

**Step A: Verify New IP (Optional but good for sanity)**
```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' follow-up_agent_web_1
```

**Step B: RELOAD NGINX (Mandatory)**
```bash
docker exec frontend_nginx_1 nginx -s reload
```
*If reload fails or behaves weirdly, restart the container:*
```bash
docker restart frontend_nginx_1
```

## 3. 🕸️ Network Check
Ensure Nginx is connected to Sarah's network. If `docker-compose down` removed the network, Nginx might have been kicked off.

```bash
# Check if frontend_nginx_1 is in follow-up_agent_default
docker network inspect follow-up_agent_default
```
*If missing:*
```bash
docker network connect follow-up_agent_default frontend_nginx_1
docker restart frontend_nginx_1
```

## 4. ✅ Verification (The "Can you hear me now?" Test)
Do not assume it works. Check the logs immediately.

1.  **Tail Sarah's Logs:**
    ```bash
    docker logs -f follow-up_agent_web_1
    ```
2.  **Send a Test Message** (or use curl if possible, but SMS is best).
3.  **Tail Nginx Logs (if Sarah is silent):**
    ```bash
    docker logs --tail 20 frontend_nginx_1
    ```
    *Look for `connect() failed (111: Connection refused)` - this means you skipped Step 2.*

---
**Summary Checklist:**
- [ ] Code Pulled & Built
- [ ] Containers Up
- [ ] **Nginx Reloaded** (CRITICAL)
- [ ] Network Verified
- [ ] Test Message Confirmed in Logs
