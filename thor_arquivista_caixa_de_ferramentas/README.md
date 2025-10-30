# Orquestrador de Preservação Digital — Versão Final
**Nome do pacote:** `orquestrador_preservacao_digital_final.zip`  
**Componentes:** UI desktop (ttkbootstrap + MongoDB) + scripts OAIS parametrizáveis (hash/fixidez, verificação, BagIt, SIP, identificação de formatos, replicação) + painel de eventos **PREMIS**.

---

## 1. Introdução
Este pacote consolida uma base operacional para implementação de um **pipeline OAIS** no APESP, com foco em:
- Geração e verificação de **fixidez** (SHA-256);
- **Empacotamento** (BagIt mínimo e SIP simples);
- **Identificação de formatos** (Siegfried, quando disponível);
- **Replicação** entre armazenamentos;
- **Registro de eventos PREMIS** (automático e manual) e **monitoramento** na UI.

A camada desktop de orquestração permite **enfileirar tarefas**, acompanhar **logs** em tempo real e visualizar/exportar **eventos PREMIS** com filtros, paginação e ordenação.

---

## 2. Estrutura do Projeto
```
orquestrador_preservacao_digital_final/
├─ app.py
├─ requirements.txt
├─ .env.example
├─ README.md  ← (este arquivo)
├─ core/
│  ├─ config.py         # Config (.env e ~/.preservacao_app.json); PREMIS_LOG/AGENT
│  ├─ db.py             # Conexão e coleções (jobs, job_logs)
│  └─ jobs.py           # Fila/worker, execução dos scripts e PREMIS automático
├─ ui/
│  └─ main_window.py    # Interface ttkbootstrap (abas + painel “Eventos PREMIS”)
└─ scripts/             # Scripts OAIS-like (CLI)
   ├─ pd_common.py
   ├─ hash_files.py
   ├─ verify_fixity.py
   ├─ build_bag.py
   ├─ build_sip.py
   ├─ premis_log.py
   ├─ format_identify.py
   ├─ replicate_storage.py
   ├─ config.example.yaml
   └─ README.md         # Guia rápido dos scripts
```

---

## 3. Pré‑requisitos
- **Python** 3.10+
- **MongoDB** acessível (local ou remoto)  
  - Para autenticação: usuário com permissão no DB de aplicação (padrão `preservacao`) ou em `admin` com `authSource=admin`.
- (Opcional) **Siegfried (`sf`)** no `PATH` para identificação robusta de formatos.
- (Opcional) `PyYAML` e `tqdm` (já listados em `requirements.txt`).

> **Observação**: Em Windows, substitua `python` por `py` quando necessário.

---

## 4. Preparação do Ambiente
### 4.1. Clonar/Extrair
Extraia o pacote final para uma pasta de trabalho.

### 4.2. Ambiente virtual e dependências
```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.3. Configuração por `.env` (ou `~/.preservacao_app.env`)
Crie um arquivo `.env` na raiz com, por exemplo:
```env
MONGO_URI=mongodb://usuario:senha@localhost:27017/?authSource=admin
MONGO_DB=preservacao
PREMIS_LOG=/caminho/para/premis_events.jsonl
PREMIS_AGENT=Gerenciador de Arquivos — Orquestração
```
Na primeira execução, o app também cria **`~/.preservacao_app.json`**, onde você pode ajustar `mongo_uri`, `mongo_db`, `scripts_dir` e `premis_log`.

---

## 5. Execução do Sistema (UI)
```bash
python app.py
```
A janela principal dispõe de abas para:
- **Manifesto (Hash)**;
- **Verificar Fixidez**;
- **BagIt**;
- **SIP** (com opção de compactação);
- **Identificar Formatos**;
- **Replicar**;
- **Evento PREMIS** (inclusão manual);
- **Fila e Logs de Jobs** (monitoramento);
- **Eventos PREMIS** (painel analítico: filtros por Tipo, Outcome, Agente, Objeto, datas, busca; **paginação**; **ordenação com setas**; **exportação CSV**; botão **Abrir log…**).

> **Registro PREMIS automático**: ao término de cada job, o sistema emite evento com `eventType` apropriado (*fixity check*, *message digest calculation*, *packaging*, *ingestion preparation*, *format identification*, *replication*), resultado (**success/failure**) e detalhe (exit code).

---

## 6. Exemplos de Uso (CLI — scripts/)
Os scripts podem ser orquestrados pela UI ou usados diretamente no terminal.

### 6.1. Gerar manifesto de fixidez
```bash
python scripts/hash_files.py --raiz /dados/origem --saida /pacote/manifest.tsv
```

### 6.2. Verificar fixidez
```bash
python scripts/verify_fixity.py --raiz /dados/origem --manifesto /pacote/manifest.tsv
# Código de saída: 0 (ok), 1 (divergências/erros)
```

### 6.3. Criar pacote BagIt mínimo
```bash
python scripts/build_bag.py --fonte /dados/origem --destino /bags --bag-name 2025-10-27_projeto --org APESP
```

### 6.4. Construir SIP simples
```bash
python scripts/build_sip.py --fonte /dados/origem --saida /sips --sip-id SIP_0001 --zip
```

### 6.5. Registrar um evento PREMIS (manual)
```bash
python scripts/premis_log.py --arquivo-log /logs/premis.jsonl   --tipo "fixity check" --obj-id "SIP_0001/objects/doc.pdf"   --detalhe "Verificação de manifesto" --resultado success --agente "Gerenciador"
```

### 6.6. Identificar formatos
```bash
python scripts/format_identify.py --raiz /dados/origem --saida formatos.jsonl
# Usa Siegfried (sf) se disponível; fallback para mimetypes.
```

### 6.7. Replicar para múltiplos destinos
```bash
python scripts/replicate_storage.py --fonte /sips/SIP_0001   --destino /replicaA --destino /replicaB --verificar-hash
```

---

## 7. Fluxo de Trabalho Sugerido (OAIS resumido)
1. **Preparação & Fixidez**  
   `hash_files.py` → gera `manifest.tsv` com SHA-256.
2. **Verificação de Integridade**  
   `verify_fixity.py` → confere a cópia ou o conjunto recebido.
3. **Identificação de Formatos (opcional)**  
   `format_identify.py` → registra MIME/PRONOM (se `sf`).
4. **Empacotamento**  
   `build_bag.py` (BagIt) **ou** `build_sip.py` (SIP simples).
5. **Replicação**  
   `replicate_storage.py` → escreve em múltiplos alvos com verificação.
6. **Eventos PREMIS**  
   Automático (ao fim dos jobs) e/ou manual via `premis_log.py` e pela UI.

---

## 8. Painel “Eventos PREMIS” (UI)
- **Filtros**: Tipo (eventType), Resultado (Outcome), Agente, Objeto, intervalo de datas, busca textual.
- **Paginação**: 50–1000 itens por página; botões *Anterior/Próxima*.
- **Ordenação**: clique no cabeçalho para ordenar; o título exibe **▲/▼**.
- **Exportação**: CSV com **todos os registros filtrados** (não só a página).
- **Abrir log…**: selecione outro arquivo JSONL rapidamente.

Formato mínimo de cada evento (JSONL):
```json
{
  "eventIdentifier": "uuid",
  "eventType": "fixity check",
  "eventDateTime": "2025-10-27T12:34:56Z",
  "eventDetail": "Exit code 0",
  "eventOutcome": "success",
  "linkingObjectIdentifier": "SIP_0001/objects/doc.pdf",
  "linkingAgentName": "Gerenciador de Arquivos — Orquestração"
}
```

---

## 9. Boas Práticas e Observações
- **BagIt**: implementação mínima; recomende-se validar com ferramentas externas e adicionar *tag files* institucionais conforme política.
- **PREMIS**: o esquema aqui é **reduzido**; ajuste campos/dicionários conforme sua política interna.
- **Logs**: a coleção `job_logs` centraliza stdout/stderr dos jobs.
- **Siegfried**: preferível para identificação confiável; instale e mantenha as *signatures* atualizadas.
- **Caminhos**: use caminhos sem espaço quando possível; em Windows, revise permissões da pasta de trabalho.
- **Backups**: mantenha cópia do `premis_events.jsonl` (ou roteamento para storage institucional).

---

## 10. Solução de Problemas (FAQ rápido)
- **A UI abre, mas não vejo logs**  
  Verifique o **MongoDB** (URI, credenciais, firewall) e a coleção `job_logs`.
- **Erro de permissão ao copiar/criar Bag**  
  Confirme permissões de escrita na pasta de destino.
- **Siegfried não encontrado**  
  Instale o `sf` e confirme que está no `PATH` do sistema.
- **PREMIS não registra automaticamente**  
  Cheque `PREMIS_LOG` no `.env`/`~/.preservacao_app.json` e se há permissão para escrita.
- **Ordenação/Exportação**  
  A ordenação aparece com **▲/▼**; o CSV exporta **todos** os filtrados que estão na memória.

---

## 11. Licença e Autoria
- Código base licenciado sob **MIT** (ajuste conforme política institucional, se necessário).
- Autor: **Carlos Eduardo C. Amand** (APESP).  
- Colab.: Camada de orquestração, painel PREMIS e scripts OAIS-like preparados como base para o **Gerenciador de Arquivos**.

---

## 12. Roadmap (sugestões)
- Validação BagIt completa; *payload manifests* adicionais.
- Painel PREMIS com agregações (dashboard), e suporte a múltiplos logs.
- Geração de AIP e DIP com metadados ampliados (PREMIS + METS).
- Integração com *watchers* para ingest automático.



📘 Notas para o README (trecho)

Portabilidade: o sistema não depende mais de banco externo.

Fila de jobs: mantida no arquivo jobs_db.json (na raiz).

Logs PREMIS: continuam em ./logs/premis_events.jsonl.

Execução:

python app.py


Estrutura do jobs_db.json:

jobs: lista de tarefas com status pending|running|done|error;

job_logs: registros textuais (stdout/stderr resumidos, estados);

seq: contador de IDs.