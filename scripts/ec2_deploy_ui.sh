#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/opt/amis-agent"
UI_DIR="$REPO_DIR/ui"
WEB_ROOT="/var/www/amis-agent"

echo "Pull latest code"
cd "$REPO_DIR"
git pull

echo "Ensure Python deps"
source "$REPO_DIR/.venv/bin/activate"
pip install -e "$REPO_DIR"

echo "Install Node if missing"
if ! command -v node >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y nodejs npm
fi

echo "Build UI"
cd "$UI_DIR"
npm install
npm run build

echo "Install Nginx if missing"
if ! command -v nginx >/dev/null 2>&1; then
  sudo apt-get install -y nginx
fi

echo "Deploy Nginx config"
sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete "$UI_DIR/dist/" "$WEB_ROOT/"
sudo cp "$REPO_DIR/deploy/nginx/amis-agent.conf" /etc/nginx/sites-available/amis-agent
if [ ! -e /etc/nginx/sites-enabled/amis-agent ]; then
  sudo ln -s /etc/nginx/sites-available/amis-agent /etc/nginx/sites-enabled/amis-agent
fi
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable --now nginx

echo "Install systemd service for API"
sudo cp "$REPO_DIR/deploy/systemd/amis-agent-api.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now amis-agent-api

echo "Install systemd service for worker"
sudo cp "$REPO_DIR/deploy/systemd/amis-agent-worker.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now amis-agent-worker

echo "Restart services"
sudo systemctl restart amis-agent-scheduler
sudo systemctl restart amis-agent-api
sudo systemctl restart amis-agent-worker
sudo systemctl restart nginx

echo "Done"
