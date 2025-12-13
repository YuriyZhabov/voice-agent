# VoxPulse Monitoring Stack

Мониторинг для Voice AI платформы.

## Компоненты

- **Prometheus** - сбор метрик (порт 9090)
- **Blackbox Exporter** - HTTP/TCP probes (порт 9115)
- **Nginx** - reverse proxy + статика UI (порты 80, 443)
- **VoxPulse UI** - React дашборд

## Быстрый деплой

```bash
# На Windows (PowerShell)
./deploy.ps1 -VpsIp "YOUR_VPS_IP" -Domain "monitoring.agentio.pro"

# На Linux/Mac
./deploy.sh YOUR_VPS_IP monitoring.agentio.pro
```

## Ручной деплой

1. Скопировать файлы на VPS:
```bash
scp -r . root@VPS_IP:/opt/monitoring/
```

2. Настроить SSL:
```bash
certbot certonly --standalone -d monitoring.agentio.pro
cp /etc/letsencrypt/live/monitoring.agentio.pro/*.pem /opt/monitoring/nginx/ssl/
```

3. Запустить:
```bash
cd /opt/monitoring
docker compose up -d
```

## Структура

```
deploy/monitoring/
├── docker-compose.yml      # Основной compose файл
├── prometheus/
│   └── prometheus.yml      # Конфиг Prometheus
├── blackbox/
│   └── blackbox.yml        # Конфиг Blackbox Exporter
├── nginx/
│   ├── conf.d/
│   │   └── default.conf    # Nginx конфиг
│   └── ssl/                # SSL сертификаты
└── site-dist/              # Собранный UI
```

## Endpoints

- `https://monitoring.agentio.pro` - UI
- `https://monitoring.agentio.pro/api/prometheus/` - Prometheus API proxy
- `https://monitoring.agentio.pro/health` - Health check

## Метрики

Prometheus собирает метрики с:
- LiveKit Server (158.160.55.228:7881)
- Voice Agent (130.193.50.241:8081)
- Blackbox probes (HTTP/TCP)
