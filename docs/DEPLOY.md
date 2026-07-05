# Guia de Deploy

## Opção 1: Render

1. Crie um novo **PostgreSQL** no Render (Dashboard → New → PostgreSQL).
   Copie a "Internal Database URL" gerada.
2. Crie um novo **Web Service** apontando para a pasta `backend/` do seu
   repositório.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Em "Environment", adicione as variáveis do seu `.env`:
   - `DATABASE_URL` → a Internal Database URL copiada no passo 1
   - `SECRET_KEY` → gere uma chave aleatória forte
   - demais variáveis conforme `.env.example`
4. Faça o deploy. O Render expõe automaticamente HTTPS.
5. Rode as migrações (opcional, se preferir Alembic ao invés do
   `create_all` automático): abra o "Shell" do serviço no Render e rode
   `alembic upgrade head`.

## Opção 2: Railway

1. Crie um novo projeto e adicione um plugin **PostgreSQL**.
2. Adicione um serviço a partir do seu repositório, apontando para
   `backend/`.
3. Configure as variáveis de ambiente (a `DATABASE_URL` pode ser
   referenciada automaticamente via `${{Postgres.DATABASE_URL}}` na aba
   Variables do Railway).
4. Defina o **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Deploy automático a cada push.

## Opção 3: VPS (Ubuntu 22.04+)

```bash
# Instalar dependências
sudo apt update && sudo apt install -y python3.11 python3.11-venv postgresql nginx

# Criar banco de dados
sudo -u postgres psql -c "CREATE DATABASE license_system;"
sudo -u postgres psql -c "CREATE USER license_user WITH PASSWORD 'senha_forte';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE license_system TO license_user;"

# Clonar e configurar o backend
git clone <seu-repositorio>
cd license-system/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite o .env com os dados do banco criado acima

alembic upgrade head

# Rodar com Gunicorn + Uvicorn workers (produção)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Configurando systemd (para manter o serviço rodando)

Crie `/etc/systemd/system/license-api.service`:

```ini
[Unit]
Description=License System API
After=network.target

[Service]
User=www-data
WorkingDirectory=/caminho/para/license-system/backend
Environment="PATH=/caminho/para/license-system/backend/venv/bin"
ExecStart=/caminho/para/license-system/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable license-api
sudo systemctl start license-api
```

### Configurando Nginx como proxy reverso + HTTPS

```nginx
server {
    listen 80;
    server_name api.seudominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Depois use o Certbot para HTTPS gratuito:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.seudominio.com
```

### Hospedando o painel no mesmo VPS

O painel é 100% estático. Basta apontar outro bloco `server` do Nginx
para a pasta `panel/`:

```nginx
server {
    listen 80;
    server_name painel.seudominio.com;
    root /caminho/para/license-system/panel;
    index login.html;
}
```

Lembre-se de atualizar `panel/static/js/config.js` com a URL pública da
sua API (`https://api.seudominio.com`).
