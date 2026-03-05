#!/bin/bash
# SOP Script for Deploying Project Sarah (Follow-up_agent)
# This ensures the container is attached to the correct Nginx network after a restart.

set -e

echo "🚀 Deploying Project Sarah (Follow-up_agent)..."
cd /home/ubuntu/.openclaw/workspace/Follow-up_agent

echo "🛑 Stopping existing containers..."
docker-compose down

echo "🏗️ Building and starting containers..."
docker-compose up -d --build

echo "🧹 Cleaning up old dangling images and stopped containers to save disk space..."
docker image prune -f
docker container prune -f

echo "🔗 Connecting Sarah web container to frontend Nginx network..."
# Ignore error if it's already connected
docker network connect frontend_app-network follow-up_agent_web_1 || echo "⚠️ Network connect command failed or already connected, proceeding..."

echo "🔄 Reloading Nginx proxy to apply routing..."
docker exec frontend_nginx_1 nginx -s reload

echo "✅ Checking container status..."
docker ps | grep follow-up_agent

echo "🎉 Deployment complete. Sarah is ready to receive messages!"
