# VoxPulse Monitoring Stack Deploy Script (PowerShell)
# Usage: .\deploy.ps1 -VpsIp "1.2.3.4" -Domain "monitoring.agentio.pro"

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIp,
    
    [string]$Domain = "monitoring.agentio.pro",
    [string]$VpsUser = "root"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Deploying VoxPulse Monitoring Stack ===" -ForegroundColor Cyan
Write-Host "VPS: $VpsIp"
Write-Host "Domain: $Domain"

# 1. Create directories on VPS
Write-Host ">>> Creating directories..." -ForegroundColor Yellow
ssh "$VpsUser@$VpsIp" "mkdir -p /opt/monitoring/{prometheus,blackbox,nginx/conf.d,nginx/ssl,site-dist}"

# 2. Copy configuration files
Write-Host ">>> Copying configs..." -ForegroundColor Yellow
scp docker-compose.yml "$VpsUser@${VpsIp}:/opt/monitoring/"
scp prometheus/prometheus.yml "$VpsUser@${VpsIp}:/opt/monitoring/prometheus/"
scp blackbox/blackbox.yml "$VpsUser@${VpsIp}:/opt/monitoring/blackbox/"
scp nginx/conf.d/default.conf "$VpsUser@${VpsIp}:/opt/monitoring/nginx/conf.d/"

# 3. Copy built UI
Write-Host ">>> Copying UI build..." -ForegroundColor Yellow
scp -r site-dist/* "$VpsUser@${VpsIp}:/opt/monitoring/site-dist/"

# 4. Install Docker if not present
Write-Host ">>> Checking Docker..." -ForegroundColor Yellow
ssh "$VpsUser@$VpsIp" "command -v docker || (curl -fsSL https://get.docker.com | sh)"

# 5. Setup SSL (self-signed for now)
Write-Host ">>> Setting up SSL..." -ForegroundColor Yellow
$sslScript = @"
apt-get update && apt-get install -y certbot
certbot certonly --standalone -d $Domain --non-interactive --agree-tos --email admin@agentio.pro || true

if [ -f /etc/letsencrypt/live/$Domain/fullchain.pem ]; then
    cp /etc/letsencrypt/live/$Domain/fullchain.pem /opt/monitoring/nginx/ssl/
    cp /etc/letsencrypt/live/$Domain/privkey.pem /opt/monitoring/nginx/ssl/
else
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /opt/monitoring/nginx/ssl/privkey.pem \
        -out /opt/monitoring/nginx/ssl/fullchain.pem \
        -subj '/CN=$Domain'
fi
"@
ssh "$VpsUser@$VpsIp" $sslScript

# 6. Start services
Write-Host ">>> Starting services..." -ForegroundColor Yellow
ssh "$VpsUser@$VpsIp" "cd /opt/monitoring && docker compose up -d"

# 7. Check status
Write-Host ">>> Checking status..." -ForegroundColor Yellow
ssh "$VpsUser@$VpsIp" "docker ps"

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "UI: https://$Domain"
Write-Host "Prometheus: https://$Domain/api/prometheus/"
Write-Host ""
Write-Host "Don't forget to:" -ForegroundColor Yellow
Write-Host "1. Point DNS $Domain -> $VpsIp"
Write-Host "2. Open ports 80, 443 in firewall"
