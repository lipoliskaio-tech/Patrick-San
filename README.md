# Sistema de Licenciamento de Software

Sistema completo de licenciamento com backend (FastAPI + PostgreSQL), painel
administrativo web, API para clientes e cliente desktop de exemplo em Python.

## Estrutura do projeto

```
license-system/
├── backend/          # API FastAPI (regras de negócio, banco de dados)
│   ├── routers/      # Endpoints (auth, admin, client)
│   ├── models/       # Modelos SQLAlchemy (tabelas do banco)
│   ├── schemas/       # Schemas Pydantic (validação de entrada/saída)
│   ├── services/      # Regras de negócio (licenças, versões, autenticação)
│   ├── database/      # Configuração de conexão e settings
│   ├── utils/          # Funções utilitárias (segurança, geração de chaves)
│   ├── alembic/        # Migrações do banco de dados
│   └── main.py         # Ponto de entrada da API
├── panel/            # Painel administrativo (HTML + Bootstrap + JS puro)
├── client/           # Cliente desktop de exemplo (Tkinter)
└── docs/             # Documentação adicional
```

## 1. Configurando o backend

### Pré-requisitos
- Python 3.11+
- PostgreSQL 14+ (local, Render, Railway ou outro provedor)

### Passo a passo

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edite o .env com sua DATABASE_URL e uma SECRET_KEY forte e aleatória
```

### Criando as tabelas

Você tem duas opções:

**Opção A - Automática (mais simples para começar):**
O `main.py` já chama `Base.metadata.create_all()` na inicialização, então
basta rodar o servidor (próximo passo) que as tabelas serão criadas.

**Opção B - Usando Alembic (recomendado para produção):**
```bash
alembic upgrade head
```

### Rodando o servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A documentação interativa da API estará disponível em:
`http://localhost:8000/docs`

### Criando o primeiro administrador

Como o painel exige login, você precisa criar o primeiro administrador
usando a rota de bootstrap (só funciona enquanto não existir nenhum admin):

```bash
curl -X POST http://localhost:8000/admin/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SenhaForte123!"}'
```

## 2. Configurando o painel administrativo

O painel é um site estático (HTML + JS puro + Bootstrap), sem necessidade
de build. Basta:

1. Abrir `panel/static/js/config.js` e ajustar `API_BASE_URL` para o
   endereço do seu backend (ex: `https://minha-api.onrender.com`).
2. Servir os arquivos estáticos com qualquer servidor HTTP simples, por
   exemplo:

```bash
cd panel
python -m http.server 8080
```

3. Acessar `http://localhost:8080/login.html` e entrar com o administrador
   criado no passo anterior.

Em produção, você pode hospedar a pasta `panel/` em qualquer serviço de
arquivos estáticos (Netlify, Vercel, GitHub Pages, um bucket S3, ou o
próprio VPS via Nginx).

## 3. Cliente desktop

O cliente de exemplo usa Tkinter (já incluso no Python padrão no Windows).

```bash
cd client
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Edite `client/license_client.py` e ajuste `API_BASE_URL` para o endereço
do seu backend. Depois:

```bash
python main.py
```

Para distribuir como um `.exe` no Windows, recomenda-se usar o PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "MeuSoftware" main.py
```

## 4. Hospedagem (Render / Railway / VPS)

Veja `docs/DEPLOY.md` para instruções detalhadas de deploy do backend e
do banco PostgreSQL.

## 5. Referência da API

Veja `docs/API.md` para a lista completa de endpoints, ou acesse
`/docs` (Swagger) diretamente no backend rodando.

## 6. Segurança - Checklist antes de ir para produção

- [ ] Troque `SECRET_KEY` no `.env` por uma chave aleatória forte (nunca reutilize a de exemplo).
- [ ] Restrinja `allow_origins` no CORS (`backend/main.py`) para o domínio real do seu painel.
- [ ] Use HTTPS em produção (Render e Railway já fornecem isso automaticamente).
- [ ] Considere proteger a rota `/client/history/{license_key}` exigindo
      um token de sessão válido, caso queira restringir quem pode consultar
      o histórico de uma licença.
- [ ] Faça backup regular do banco de dados PostgreSQL.
- [ ] Desative a rota `/admin/auth/bootstrap` (ou adicione uma variável de
      ambiente extra de proteção) depois de criar o primeiro administrador,
      já que ela é bloqueada automaticamente assim que existir 1 admin,
      mas vale reforçar isso a nível de infraestrutura também.

## Licença

Este é um projeto de referência para você adaptar e usar em seus próprios
produtos. Ajuste as regras de negócio, autenticação e infraestrutura
conforme as necessidades e a legislação (ex: LGPD) aplicável ao seu caso.
