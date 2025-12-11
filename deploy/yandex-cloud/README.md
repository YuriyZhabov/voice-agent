# Деплой Voice Agent в Yandex Cloud

## Быстрый старт

### 1. Создать VM в Yandex Cloud

```bash
# Создать VM с Ubuntu 22.04
yc compute instance create \
  --name voice-agent-vm \
  --zone ru-central1-a \
  --cores 2 \
  --memory 4GB \
  --core-fraction 100 \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2204-lts,size=20 \
  --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4 \
  --ssh-key ~/.ssh/id_rsa.pub
```

### 2. Подключиться к VM

```bash
# Получить IP
yc compute instance get voice-agent-vm --format json | jq -r '.network_interfaces[0].primary_v4_address.one_to_one_nat.address'

# SSH
ssh yc-user@<VM_IP>
```

### 3. Установить Docker на VM

```bash
# На VM выполнить:
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Перелогиниться
```

### 4. Деплой через Docker

```bash
# На VM:
git clone https://github.com/YuriyZhabov/voice-agent.git
cd voice-agent

# Создать .env с продакшн настройками
cp .env.example .env
nano .env  # заполнить ключи

# Запустить
docker compose up -d --build
```

## Альтернатива: Container Registry

### Локально (на Windows):

```bash
# 1. Авторизоваться в реестре
yc container registry configure-docker

# 2. Собрать и запушить образ
docker build -t cr.yandex/<REGISTRY_ID>/voice-agent:latest .
docker push cr.yandex/<REGISTRY_ID>/voice-agent:latest
```

### На VM:

```bash
# Авторизоваться и запустить
yc container registry configure-docker
docker pull cr.yandex/<REGISTRY_ID>/voice-agent:latest
docker run -d --env-file .env -p 8081:8081 cr.yandex/<REGISTRY_ID>/voice-agent:latest
```

## Переменные окружения (.env.prod)

```env
# LiveKit
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# Yandex Cloud
YC_FOLDER_ID=your_folder_id
YC_API_KEY=your_api_key

# Providers
STT_PROVIDER=yandex
TTS_PROVIDER=yandex
LLM_PROVIDER=yandex
```

## Мониторинг

```bash
# Логи
docker logs -f voice-agent

# Статус
docker ps

# Health check
curl http://localhost:8081/health
```
