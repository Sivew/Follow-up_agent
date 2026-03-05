# Deployment Checklist

## Standard Deployment

```bash
cd /home/ubuntu/.openclaw/workspace/Follow-up_agent
docker-compose down
docker-compose up -d --build
```

## Post-Deployment (CRITICAL)

### 1. Reload Nginx
Container IP changes on rebuild. Force Nginx to resolve new IP:
```bash
docker exec frontend_nginx_1 nginx -s reload
```

### 2. Verify Network
Ensure Nginx is on app network:
```bash
docker network inspect follow-up_agent_default | grep nginx
```
If missing: `docker network connect follow-up_agent_default frontend_nginx_1`

### 3. Test
```bash
docker logs -f follow-up_agent_web_1
```
Send test SMS and verify logs show activity.

## Checklist
- [ ] Code pulled & built
- [ ] Containers running
- [ ] **Nginx reloaded**
- [ ] Network verified
- [ ] Test message confirmed
