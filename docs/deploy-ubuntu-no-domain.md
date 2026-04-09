# Быстрый деплой на Ubuntu 22.04 (без домена)

Этот сценарий рассчитан на публичный IP и уже установленный Docker.

## 1) Один раз на сервере

```bash
sudo apt update
sudo apt install -y git curl openssl ufw
```

## 2) Запуск деплоя

```bash
git clone <REPO_URL> /opt/website
cd /opt/website
bash scripts/deploy_ubuntu_ip.sh \
  --repo-url <REPO_URL> \
  --branch <BRANCH> \
  --target-dir /opt/website \
  --server-ip <SERVER_IP> \
  --site-port 3000
```

Сайт будет доступен по адресу:

```text
http://<SERVER_IP>:3000
```

## 3) Обновление после новых коммитов

```bash
cd /opt/website
bash scripts/deploy_ubuntu_ip.sh \
  --repo-url <REPO_URL> \
  --branch <BRANCH> \
  --target-dir /opt/website \
  --server-ip <SERVER_IP> \
  --site-port 3000
```

## 4) Что делает скрипт

- Обновляет или клонирует репозиторий.
- Создаёт `.env` из `env.example` (если нет).
- Обновляет прод-переменные (`JWT_SECRET_KEY`, URL, CORS).
- Запускает `docker compose up -d --build`.
- Проверяет health API (`/health`) и web.
- Закрывает внешние порты `8000`, `5432`, `6379` через UFW.

## 5) Быстрая проверка

```bash
docker compose -f /opt/website/docker-compose.yml ps
curl -f http://127.0.0.1:8000/health
curl -I http://<SERVER_IP>:3000
```
