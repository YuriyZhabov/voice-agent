# Self-hosted LiveKit в Yandex Cloud

## Требования

- VM в Yandex Cloud (минимум 2 vCPU, 4 GB RAM)
- Ubuntu 22.04 LTS
- Домен с DNS записью (livekit.agentio.pro)
- Открытые порты: 80, 443 (TCP/UDP), 7881, 50000-60000/UDP

## Быстрый старт

### 1. Создать VM в Yandex Cloud

```bash
# Через CLI
yc compute instance create \
  --name livekit-server \
  --zone ru-central1-a \
  --platform standard-v3 \
  --cores 2 \
  --memory 4 \
  --core-fraction 100 \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2204-lts,size=30 \
  --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4 \
  --ssh-key ~/.ssh/id_rsa.pub
```

### 2. Настроить DNS

Добавить A-запись в reg.ru:
- Имя: `livekit`
- Тип: `A`
- Значение: `<IP адрес VM>`

### 3. Настроить Security Group

Открыть порты:
- 22/TCP - SSH
- 80/TCP - HTTP (для Let's Encrypt)
- 443/TCP - HTTPS
- 443/UDP - TURN
- 7881/TCP - WebRTC TCP fallback
- 50000-60000/UDP - WebRTC media

### 4. Установить LiveKit

```bash
# Подключиться к VM
ssh yc-user@<IP>

# Скачать файлы
git clone <repo> /tmp/repo
cd /tmp/repo/deploy/livekit

# Запустить установку
sudo ./setup.sh
```

### 5. Запустить

```bash
# Запуск
sudo systemctl start livekit

# Проверка
docker compose -f /opt/livekit/docker-compose.yml logs -f

# Тест
curl https://livekit.agentio.pro
```

## Конфигурация агента

После установки обновите `.env` агента:

```bash
LIVEKIT_URL=wss://livekit.agentio.pro
LIVEKIT_API_KEY=<из /opt/livekit/.env>
LIVEKIT_API_SECRET=<из /opt/livekit/.env>
```

## Мониторинг

- Prometheus метрики: `http://localhost:6789/metrics`
- Логи: `docker compose logs -f`
- Статус: `docker compose ps`

## Troubleshooting

### SSL не работает
```bash
# Проверить DNS
nslookup livekit.agentio.pro

# Проверить Caddy логи
docker logs caddy
```

### WebRTC не подключается
```bash
# Проверить порты
sudo netstat -tulpn | grep -E '(7880|7881|443)'

# Проверить firewall
sudo ufw status
```

### Перезапуск
```bash
sudo systemctl restart livekit
```

## Стоимость

~3,250 ₽/месяц:
- VM 2 vCPU, 4 GB: ~2,500 ₽
- SSD 30 GB: ~300 ₽
- Статический IP: ~300 ₽
- Трафик ~100 GB: ~150 ₽
