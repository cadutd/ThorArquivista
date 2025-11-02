# Thor Arquivista — Orquestrador de Preservação Digital

Aplicativo desktop (Tkinter + ttkbootstrap) para **orquestrar tarefas de preservação digital**: geração de manifestos BagIt, verificação de fixidez, registro/consulta de eventos PREMIS, replicação e empacotamento, com **fila local de jobs** e execução assíncrona por *worker*.

> **Estado atual:** versão portátil (sem banco externo). A persistência usa **arquivos JSON** na raiz do projeto.

---

## Sumário
- [Principais recursos](#principais-recursos)
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Instalação do ambiente](#instalação-do-ambiente)
- [Execução do aplicativo](#execução-do-aplicativo)
- [Estrutura de diretórios](#estrutura-de-diretórios)
- [Configuração (`preservacao_app.json`)](#configuração-preservacao_appjson)
- [Fila de jobs (`jobs_db.json`)](#fila-de-jobs-jobs_dbjson)
- [Painéis da interface](#painéis-da-interface)
  - [Manifesto (Hash)](#painel-manifesto-hash)
  - [Verificação de Fixidez](#painel-verificação-de-fixidez)
  - [PREMIS — Registrar Evento](#painel-premis-—-registrar-evento)
  - [PREMIS — Visualizar](#painel-premis-—-visualizar)
  - [Replicação / Bag / SIP / Identificar Formatos](#painéis-replicação--bag--sip--identificar-formatos)
  - [Controle do Worker](#painel-controle-do-worker)
- [Execução dos scripts via CLI](#execução-dos-scripts-via-cli)
- [Mapeamento de jobs → scripts](#mapeamento-de-jobs--scripts)
- [Boas práticas e desempenho](#boas-práticas-e-desempenho)
- [Solução de problemas](#solução-de-problemas)
- [Roadmap](#roadmap)
- [Licença](#licença)

---

## Principais recursos
- **Portabilidade total:** sem dependências externas; usa JSON em disco.
- **Fila local de jobs:** `jobs_db.json` com estados `pending|running|done|error|canceled`.
- **Worker** em *thread* dedicada com **pausar / retomar / reiniciar** e modal de **logs por job**.
- **PREMIS**: registro de eventos (*append-only* em JSONL) e painel de consulta.
- **Geração de manifesto BagIt** com múltiplos algoritmos e filtros.
- **Verificação de fixidez** (mismatch, faltantes e *extras* opcionais).
- **UI modular** com *tabs* por funcionalidade e **Fechar aba** em todos (exceto tela inicial).
- **Imagem inicial configurável** (`assets/logo_inicial.png`).

---

## Arquitetura

```
app.py ── inicializa configuração, JobStore e Worker; carrega UI
core/
  config.py        ─ carrega/salva config do app (JSON)
  jobstore.py      ─ fila persistente em JSON (thread-safe)
  worker.py        ─ executa jobs chamando scripts (subprocess)
  scripts_map.py   ─ mapeia job_type → script + builder de argumentos
negocio/
  premis.py        ─ funções de negócio PREMIS (append JSONL, helpers)
ui/
  main_window.py   ─ janela principal e roteamento para painéis
  panels/
    hash_manifest.py    ─ UI do manifesto BagIt
    verify_fixity.py    ─ UI da verificação de fixidez
    worker_control.py   ─ UI de controle do worker e visualização de logs
    premis_event.py     ─ UI de registro manual de eventos PREMIS
    premis_view.py      ─ UI de consulta/exportação de eventos PREMIS
    (... demais painéis modulares ...)
scripts/
  hash_files.py     ─ gera manifestos BagIt
  verify_fixity.py  ─ valida manifestos BagIt
  (outros scripts opcionais)
```

---

## Requisitos
- **Python 3.10+** (recomendado 3.12/3.13)
- Windows, Linux ou macOS
- Permissão de leitura/escrita na pasta do projeto

> Se usar Windows PowerShell, habilite a execução da venv: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (se necessário).

---

## Instalação do ambiente

```bash
# 1) criar ambiente virtual
python -m venv .venv

# 2) ativar
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS (bash/zsh):
source .venv/bin/activate

# 3) instalar dependências mínimas
pip install ttkbootstrap
```

> Caso exista `requirements.txt`, use `pip install -r requirements.txt`.

---

## Execução do aplicativo

```bash
python app.py
```

Na primeira execução serão criados automaticamente, se ausentes:
- `preservacao_app.json` (configurações do app) — **na raiz** do projeto
- `jobs_db.json` (fila e logs) — **na raiz** do projeto

---

## Estrutura de diretórios

```
orquestrador_preservacao_digital/
├─ app.py
├─ README.md
├─ preservacao_app.json          # config local do projeto
├─ jobs_db.json                  # fila de jobs + logs
├─ assets/
│  └─ logo_inicial.png          # imagem da tela inicial (configurável)
├─ core/
│  ├─ config.py
│  ├─ jobstore.py
│  ├─ scripts_map.py
│  └─ worker.py
├─ negocio/
│  └─ premis.py
├─ ui/
│  ├─ main_window.py
│  └─ panels/
│     ├─ hash_manifest.py
│     ├─ verify_fixity.py
│     ├─ worker_control.py
│     ├─ premis_event.py
│     ├─ premis_view.py
│     └─ (...)
└─ scripts/
   ├─ hash_files.py
   └─ verify_fixity.py
```

---

## Configuração (`preservacao_app.json`)

Exemplo de configuração padrão (criada automaticamente se ausente):

```json
{
  "scripts_dir": "./scripts",
  "premis_log": "./dados/premis_events.jsonl",
  "premis_agent": "Thor Arquivista",
  "logo_path": "./assets/logo_inicial.png",
  "jobs_path": "./jobs_db.json"
}
```

- `scripts_dir`: pasta dos scripts chamados pelo *worker*.
- `premis_log`: arquivo **JSONL** de eventos PREMIS (um evento por linha).
- `premis_agent`: nome do agente aplicado aos eventos.
- `logo_path`: caminho da imagem PNG da tela inicial.
- `jobs_path`: base JSON da fila.

> Ajuste caminhos conforme necessidade. Diretórios ausentes são criados quando possível.

---

## Fila de jobs (`jobs_db.json`)

Estrutura (simplificada):
```json
{
  "jobs": [
    {
      "_id": "uuid4",
      "job_type": "HASH_MANIFEST",
      "status": "pending|running|done|error|canceled",
      "params": { "...": "..." },
      "created_at": "UTC-ISO",
      "updated_at": "UTC-ISO",
      "error_msg": null
    }
  ],
  "logs": {
    "uuid4": [
      {"ts":"UTC-ISO","level":"INFO|ERROR|...","msg":"texto"}
    ]
  }
}
```

Operações expostas pelo `JobStore` (usadas pelo *worker* e pelo painel):
- `add_job`, `add_log`, `get_logs(job_id)`
- `pop_next_pending()` (marca como `running`)
- `set_status(job_id, ...)`
- `list_jobs(status=None)`
- `counts_by_status()`
- `clear_by_status(status)`
- `requeue_from_status(status)`
- `cancel_job(job_id)`

Gravação atômica e lock por *thread* para consistência local.

---

## Painéis da interface

### Painel: Manifesto (Hash)
- Gera arquivos `manifest-<algo>.txt` no **padrão BagIt**:
  ```text
  <hash>␠␠<caminho/relativo>
  ```
- **Opções**: algoritmo (`sha256`, `sha512`, `md5`, `sha1`, `blake2b`, `blake2s`), *ignorar ocultos*, *mostrar progresso*.
- **Sugestão automática** do nome de saída conforme algoritmo e pasta raiz.
- Enfileira um job `HASH_MANIFEST` no *worker*.

### Painel: Verificação de Fixidez
- Lê um manifesto BagIt e compara com os arquivos na **pasta raiz**.
- **Opções**: *reportar extras* (arquivos presentes e não listados), *mostrar progresso*.
- Deduz o algoritmo pelo nome (`manifest-<algo>.txt`) ou aceita `--algo` explícito.
- Enfileira um job `VERIFY_FIXITY`.

### Painel: PREMIS — Registrar Evento
- Form para inserir um evento PREMIS (*eventType*, *eventDetail*, *linkingObjectIdentifier*, etc.).
- Persistência *append-only* em JSONL.

### Painel: PREMIS — Visualizar
- Filtros por tipo, período e agente.
- Lista paginada de eventos.
- Exportação CSV.

### Painéis: Replicação / Bag / SIP / Identificar Formatos
- *Placeholders* ou versões iniciais, conforme os scripts disponibilizados no diretório `scripts/`.

### Painel: Controle do Worker
- Estado do *worker*: **Em execução / Pausado / Parado**.
- **Ações**: Iniciar, Parar, Pausar, Retomar, Reiniciar.
- **Contadores por status** + **lista de jobs** com filtro.
- **Ações de fila**: Reenfileirar erros, Reenfileirar todos, Limpar pendentes, Cancelar selecionado.
- **Ver logs** (modal) do job selecionado (copiar/atualizar).

---

## Execução dos scripts via CLI

Além da UI, os scripts podem ser executados diretamente:

- **Gerar manifesto BagIt**:
  ```bash
  python scripts/hash_files.py --raiz "D:/colecao" --saida "D:/colecao/manifest-sha256.txt" --algo sha256 --ignore-hidden --progress
  ```

- **Verificar fixidez**:
  ```bash
  python scripts/verify_fixity.py --raiz "D:/colecao" --manifesto "D:/colecao/manifest-sha256.txt" --report-extras --progress
  ```

> Caminhos com espaços devem ser colocados entre aspas. Em Windows, `\` é aceito; os manifestos usam caminho **relativo POSIX** (`/`).

---

## Mapeamento de jobs → scripts

`core/scripts_map.py` determina como cada `job_type` vira chamada de script:

```python
{
  "HASH_MANIFEST": (
      "hash_files.py",
      lambda p, cfg: [
          "--raiz", p["raiz"],
          "--saida", p["saida"],
          "--algo", p.get("algo", "sha256"),
          *(["--progress"] if p.get("progress") else []),
          *(["--ignore-hidden"] if p.get("ignore_hidden") else []),
      ]
  ),
  "VERIFY_FIXITY": (
      "verify_fixity.py",
      lambda p, cfg: [
          "--raiz", p["raiz"],
          "--manifesto", p["manifesto"],
          *(["--report-extras"] if p.get("report_extras") else []),
          *(["--progress"] if p.get("progress") else []),
      ]
  ),
  # ...demais jobs...
}
```

---

## Boas práticas e desempenho
- Prefira **`sha256`** para manifestos; `md5`/`sha1` são mais rápidos mas menos robustos.
- Utilize `--ignore-hidden` para evitar lixo de metadados (`.DS_Store`, `.git`, etc.).
- Ative `--progress` em coleções grandes para acompanhamento.
- Em SSDs/RAIDs rápidos, aumentar `--workers` pode ajudar, mas evite saturar o I/O.
- Mantenha os **caminhos relativos** no manifesto (portabilidade).

---

## Solução de problemas

- **ImportError: attempted relative import beyond top-level package**  
  Garanta que o `app.py` execute o app como pacote e que `ui/main_window.py` use imports absolutos coerentes (`from core.config import AppConfig`, etc.).

- **Mistura de barras em caminhos (Windows)**  
  A UI usa `pathlib` para sugerir caminhos; ajuste manualmente se necessário. Os manifestos usam **POSIX** (`/`).

- **Worker não inicia / não para**  
  Use o painel *Controle do Worker*. Se necessário, feche o app para matar a *thread*. Arquivos de log de job ficam no `jobs_db.json` (seção `logs`).

- **Permissões de escrita**  
  Rode o app em uma pasta onde você tenha permissão de leitura/escrita.

---

## Roadmap
- Integração com ferramentas externas (Siegfried/DROID/ExifTool).
- Empacotamento **BagIt** completo (bagit.txt, manifests, `data/`).
- Geração de **SIP** com metadados e estrutura recomendada.
- Replicação com checksum pós-cópia e relatórios.

---

## Licença
Este projeto, **Thor Arquivista – Caixa de Ferramentas de Preservação Digital**,  
é licenciado sob a **GNU General Public License v3.0 (GPLv3)**.  

© 2025 Carlos Eduardo Carvalho Amand.  
Você é livre para usar, modificar e redistribuir este software,  
desde que preserve esta licença e atribua o crédito ao autor original.  

Mais informações: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)
