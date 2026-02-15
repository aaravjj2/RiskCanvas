# DigitalOcean Deployment Guide

## Prerequisites

- Docker & Docker Compose v2 installed
- Git clone of this repository

## Quick Start

```bash
cd deploy/digitalocean
cp .env.template .env
# Edit .env if needed
docker compose up -d --build
```

The web UI will be available at `http://<your-ip>:80` and the API at `http://<your-ip>:8090`.

## Architecture

```
┌──────────┐     ┌──────────┐
│  nginx   │────▶│  FastAPI  │
│  (web)   │     │   (api)   │
│  :80     │     │  :8090    │
└──────────┘     └──────────┘
```

- **web**: Nginx serving the Vite-built React SPA. Proxies `/api/*` to the API container.
- **api**: Python FastAPI with the deterministic risk engine. Runs in DEMO_MODE by default (no external API keys required).

## DigitalOcean Droplet Setup

1. Create a Droplet (Ubuntu 22.04, 1 GB RAM minimum)
2. SSH in and install Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. Clone the repo and deploy:
   ```bash
   git clone <repo-url> /opt/riskcanvas
   cd /opt/riskcanvas/deploy/digitalocean
   cp .env.template .env
   docker compose up -d --build
   ```

## Health Check

```bash
curl http://localhost:8090/health
# {"status":"healthy","engine_version":"0.1.0","api_version":"1.0.0","demo_mode":true}
```

## Updating

```bash
cd /opt/riskcanvas
git pull
cd deploy/digitalocean
docker compose up -d --build
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| API unhealthy | Check logs: `docker compose logs api` |
| 502 Bad Gateway | API container not ready; wait or check healthcheck |
| Build fails | Ensure Docker BuildKit: `DOCKER_BUILDKIT=1 docker compose build` |
