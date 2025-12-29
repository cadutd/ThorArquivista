# Backend — Thor Gestor de Arquivos Digitais

API em **FastAPI** com configuração via variáveis de ambiente e conexão com **PostgreSQL**.

## Rodar fora do Docker (opcional)
Crie um venv e instale dependências:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
