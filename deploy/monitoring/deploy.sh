#!/bin/bash
# VoxPulse Monitoring Stack Deploy Script
# Usage: ./deploy.sh <VPS_IP> [DOMAIN]

set -e

VPS_IP=${1:-"YOUR_VPS_IP"}
DOMAIN=${2:-"monitoring.agentio.pro"}
VPS_USER="root"

if [ "$VPS_IP" == "YOUR_VPS_IP" ]; then
    echo "Usage: ./deploy.sh <VPS_IP> [DOMAIN]"
    echo "Example: ./deploy.sh 1.2.3.4 monitoring.agentio.pro"
    exit 1
fi

echo "=== Deploying VoxPulse Monitoring Stack ==="
echo "VPS: $VPS_IP"
echo "Domain: $DOMAIN"

# 1. Create directories on VPS
echo ">>> Creating directories..."
ssh $VPS_USER@$VPS_IP "mkdir -p /opt/monitoring/{prometheus,blackbox,nginx/conf.d,nginx/ssl,site-dist}"

# 2. Copy configuration files
echo ">>> Copying configs..."
scp docker-compose.yml $VPS_USER@$VPS_IP:/opt/monitoring/
scp prometheus/prometheus.yml $VPS_USER@$VPS_IP:/opt/monitoring/prometheus/
scp blackbox/blackbox.yml $VPS_USER@$VPS_IP:/opt/monitoring/blackbox/
scp nginx/conf.d/default.conf $VPS_USER@$VPS_IP:/opt/monitoring/nginx/conf.d/

# 3. Copy built UI
echo ">>> Copying UI build..."
scp -r site-dist/* $VPS_USER@$VPS_IP:/opt/monitoring/site-dist/

# 4. Install Docker if not present
echo ">>> Checking Docker..."
ssh $VPS_USER@$VPS_IP "command -v docker || (curl -fsSL https://get.docker.com | sh)"

# 5. Install certbot and get SSL certificate
echo ">>> Setting up SSL..."
ssh $VPS_USER@$VPS_IP "
    apt-get update && apt-get install -y certbot
    certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@agentio.pro || true
    
    # Copy certs to nginx ssl dir
    if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/monitoring/nginx/ssl/
        cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/monitoring/nginx/ssl/
    else
        # Create self-signed cert for testing
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /opt/monitoring/nginx/ssl/privkey.pem \
            -out /opt/monitoring/nginx/ssl/fullchain.pem \
            -subj '/CN=$DOMAIN'
    fi
"

# 6. Start services
echo ">>> Starting services..."
ssh $VPS_USER@$VPS_IP "cd /opt/monitoring && docker compose up -d"

# 7. Check status
echo ">>> Checking status..."
ssh $VPS_USER@$VPS_IP "docker ps"

echo ""
echo "=== Deployment Complete ==="
echo "UI: https://$DOMAIN"
echo "Prometheus: https://$DOMAIN/api/prometheus/"
echo ""
echo "Don't forget to:"
echo "1. Point DNS $DOMAIN -> $VPS_IP"
echo "2. Open ports 80, 443 in firewall"
