# Сертификаты

Эта папка не хранится в Git. Сгенерируйте сертификаты командой из корня проекта:

```bash
mkdir -p ./traefik/certs
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout ./traefik/certs/key.pem \
  -out ./traefik/certs/cert.pem \
  -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:*.localhost,DNS:app.localhost,DNS:api.localhost,DNS:grafana.localhost,DNS:prometheus.localhost,DNS:rabbitmq.localhost"
```
