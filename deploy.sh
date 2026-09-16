#!/usr/bin/env bash
set -e

echo "🚀 Starting Rewind Bot Production Deployment..."

# 1. Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "❗ Please configure your BOT_TOKEN and secret keys in .env and rerun this script."
    exit 1
fi

# 2. Build and launch docker containers
echo "📦 Building and starting Docker services..."
docker compose -f docker/docker-compose.yml up -d --build

# 3. Wait for database and execute migrations
echo "⏳ Waiting for database to be ready and running Alembic migrations..."
sleep 5
docker compose -f docker/docker-compose.yml exec -T api python run.py --mode migrate

echo "✅ Deployment completed successfully!"
echo "📊 Check container status: docker compose -f docker/docker-compose.yml ps"
echo "📜 View live logs: docker compose -f docker/docker-compose.yml logs -f"
