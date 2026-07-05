# Referência da API

URL base de exemplo: `http://localhost:8000`

A documentação interativa (Swagger UI) está sempre disponível em `/docs`
e a especificação OpenAPI em `/openapi.json`.

## Autenticação

Todas as rotas em `/admin/*` (exceto `/admin/auth/login` e
`/admin/auth/bootstrap`) exigem um header:

```
Authorization: Bearer <token>
```

O token é obtido em `POST /admin/auth/login`.

---

## Administrador - Autenticação

### `POST /admin/auth/bootstrap`
Cria o primeiro administrador do sistema. Só funciona se ainda não existir
nenhum admin cadastrado.

```json
{ "username": "admin", "password": "SenhaForte123!" }
```

### `POST /admin/auth/login`
```json
{ "username": "admin", "password": "SenhaForte123!" }
```
Resposta:
```json
{ "access_token": "...", "token_type": "bearer", "expires_in_minutes": 120 }
```

### `POST /admin/auth/admins` (requer super admin)
Cria um novo administrador.

---

## Administrador - Licenças

| Método | Rota | Descrição |
|---|---|---|
| POST | `/admin/licenses` | Cria uma ou mais licenças |
| GET  | `/admin/licenses` | Pesquisa licenças (filtros: `license_key`, `customer_name`, `hwid`, `status`) |
| GET  | `/admin/licenses/{id}` | Detalhes de uma licença |
| GET  | `/admin/licenses/{id}/history` | Histórico de logins da licença |
| PATCH | `/admin/licenses/{id}/ban` | Bane a licença |
| PATCH | `/admin/licenses/{id}/suspend` | Suspende temporariamente |
| PATCH | `/admin/licenses/{id}/reactivate` | Reativa uma licença suspensa/banida |
| PATCH | `/admin/licenses/{id}/reset-hwid` | Remove o HWID vinculado |
| PATCH | `/admin/licenses/{id}/expiry` | Altera validade (`expires_at`, `is_lifetime` ou `add_days`) |
| PATCH | `/admin/licenses/{id}/notes` | Atualiza observações/cliente |
| DELETE | `/admin/licenses/{id}` | Exclui permanentemente |

Exemplo de criação de licença:
```json
POST /admin/licenses
{
  "license_type": "30_dias",
  "use_hwid": true,
  "customer_name": "João Silva",
  "notes": "Revendedor XPTO / Compra Mercado Pago",
  "quantity": 1
}
```

## Administrador - Dashboard

### `GET /admin/dashboard`
Retorna estatísticas gerais, gráficos (licenças por mês, logins por dia) e
as 10 licenças mais recentes.

## Administrador - Versões

| Método | Rota | Descrição |
|---|---|---|
| POST | `/admin/versions` | Publica uma nova versão do programa |
| GET  | `/admin/versions` | Lista todas as versões |

## Administrador - Manutenção

| Método | Rota | Descrição |
|---|---|---|
| GET | `/admin/maintenance` | Consulta o estado atual |
| PUT | `/admin/maintenance` | Ativa/desativa e define a mensagem |

---

## Cliente

| Método | Rota | Descrição |
|---|---|---|
| POST | `/client/login` | Login usando apenas a chave de licença + HWID |
| POST | `/client/heartbeat` | Mantém a sessão "online" (chamar a cada 30-60s) |
| GET  | `/client/maintenance` | Verifica se o sistema está em manutenção |
| GET  | `/client/version/check?current_version=1.0.0` | Verifica se há atualização disponível |
| GET  | `/client/history/{license_key}` | Histórico de logins da licença |

Exemplo de login do cliente:
```json
POST /client/login
{
  "license_key": "ABCDE-FGHIJ-KLMNO-PQRST",
  "hwid": "a1b2c3...",
  "version": "1.0.0"
}
```
Resposta em caso de sucesso:
```json
{
  "success": true,
  "message": "Login realizado com sucesso.",
  "session_token": "...",
  "days_remaining": 29,
  "expires_at": "2026-08-04T12:00:00Z",
  "is_lifetime": false,
  "status": "ativa",
  "customer_name": "João Silva"
}
```

## Limites de requisição (rate limit)

- `/admin/auth/login`: 10 requisições/minuto por IP
- `/client/login`: 15 requisições/minuto por IP
- `/client/heartbeat`: 60 requisições/minuto por IP
