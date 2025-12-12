#!/bin/bash
# LiveKit Self-Hosted Setup Script for Yandex Cloud
# Usage: ./setup.sh

set -e

echo "=== LiveKit Self-Hosted Setup ==="

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./setup.sh)"
    exit 1
fi

# 1. Обновление системы
echo ">>> Updating system..."
apt-get update && apt-get upgrade -y

# 2. Установка Docker
echo ">>> Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $SUDO_USER
else
    echo "Docker already installed"
fi

# 3. Установка Docker Compose
echo ">>> Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt-get install -y docker-compose-plugin
else
    echo "Docker Compose already installed"
fi

# 4. Создание директории
echo ">>> Creating directories..."
mkdir -p /opt/livekit
mkdir -p /var/log/caddy

# 5. Копирование файлов (если запускается из директории с файлами)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/livekit.yaml" ]; then
    echo ">>> Copying configuration files..."
    cp "$SCRIPT_DIR/livekit.yaml" /opt/livekit/
    cp "$SCRIPT_DIR/docker-compose.yml" /opt/livekit/
    cp "$SCRIPT_DIR/Caddyfile" /opt/livekit/
fi

# 6. Генерация API ключей (если .env не существует)
if [ ! -f /opt/livekit/.env ]; then
    echo ">>> Generating API keys..."
    API_KEY="API$(openssl rand -hex 8)"
    API_SECRET=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
    
    cat > /opt/livekit/.env << EOF
# LiveKit API Keys
# ВАЖНО: Сохраните эти ключи в безопасном месте!
LIVEKIT_KEYS="${API_KEY}: ${API_SECRET}"

# Для использования в агенте:
# LIVEKIT_API_KEY=${API_KEY}
# LIVEKIT_API_SECRET=${API_SECRET}
EOF
    
    echo ">>> API keys generated and saved to /opt/livekit/.env"
    echo ">>> API_KEY: $API_KEY"
    echo ">>> API_SECRET: $API_SECRET"
    echo ">>> SAVE THESE KEYS!"
else
    echo ">>> .env file already exists, skipping key generation"
fi

# 7. Настройка firewall (если ufw установлен)
if command -v ufw &> /dev/null; then
    echo ">>> Configuring firewall..."
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow 443/udp   # TURN UDP
    ufw allow 7881/tcp  # WebRTC TCP
    ufw allow 50000:60000/udp  # WebRTC media
    echo ">>> Firewall rules added (run 'ufw enable' to activate)"
fi

# 8. Создание systemd service
echo ">>> Creating systemd service..."
cat > /etc/systemd/system/livekit.service << 'EOF'
[Unit]
Description=LiveKit Server
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/livekit
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable livekit

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Configure DNS: livekit.agentio.pro → $(curl -s ifconfig.me)"
echo "2. Review /opt/livekit/.env and save the keys"
echo "3. Start LiveKit: systemctl start livekit"
echo "4. Check logs: docker compose -f /opt/livekit/docker-compose.yml logs -f"
echo ""
echo "Test connection:"
echo "  curl https://livekit.agentio.pro"
