# Backend — Thor Gestor de Arquivos Digitais

Backend do **Thor Gestor de Arquivos Digitais**, implementado em **FastAPI**, com persistência em **PostgreSQL**, controle de schema via **Alembic**, e integração com **Redis**, **Meilisearch** e **Keycloak**.

O backend é projetado para:
- gerenciar **Unidades de Acondicionamento** (digitais, físicas e híbridas);
- registrar **eventos de preservação**;
- escalar horizontalmente via containers;
- operar de forma segura e configurável por variáveis de ambiente.

---

## 🧱 Arquitetura (visão geral)

- FastAPI — API REST
- PostgreSQL — Banco de dados relacional
- Alembic — Versionamento de schema (SQL nativo PostgreSQL)
- Redis — Cache e filas (uso futuro)
- Meilisearch — Indexação e busca (uso futuro)
- Keycloak — Autenticação e gestão de identidades
- Docker / Docker Compose — Orquestração local

---

## 📁 Estrutura do backend (simplificada)

```
backend/
├── app/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── routers/
│   └── main.py
├── alembic/
│   ├── versions/
│   └── env.py
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Primeira execução (via Docker — recomendado)

### 1️⃣ Pré-requisitos

- Docker
- Docker Compose (v2+)

---

### 2️⃣ Variáveis de ambiente

```env
app_env=dev
app_name=Thor Gestor de Arquivos Digitais
database_url=postgresql+psycopg://thor:thor@postgres:5432/thor_db
```

---

### 3️⃣ Subir o ambiente

```bash
docker compose up --build
```

Se necessário:

```bash
docker compose down -v
docker compose up --build
```

---

## 🔐 Configuração inicial do Keycloak

### Acesso

http://localhost:8081  
Usuário: `admin`  
Senha: `admin`

### Configuração mínima

1. Criar realm: `thor`
2. Criar client: `thor-api`
   - Access Type: `public` (dev)
   - Valid Redirect URIs:
     ```
     http://localhost:8000/docs/oauth2-redirect
     ```
   - Web Origins:
     ```
     http://localhost:8000
     ```
3. Criar usuário e definir senha

---

## 🧪 Como testar (primeiro teste real)

1. Acesse o Swagger:
   ```
   http://localhost:8000/docs
   ```

2. Clique em **Authorize**
3. Faça login no Keycloak
4. Execute:
   ```
   GET /api/v1/auth/me
   ```

Resultado esperado: dados do usuário autenticado.

---

## 🧪 Rodar fora do Docker (opcional)

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📌 Próximos passos

- Configuração de produção (Keycloak confidential)
- Controle de permissões
- Indexação no Meilisearch
- Filas com Redis
- Auditoria de preservação (PREMIS)
