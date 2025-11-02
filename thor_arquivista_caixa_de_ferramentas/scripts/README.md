# Scripts de Preservação Digital — Thor Arquivista

Este diretório contém os **scripts autônomos** utilizados pelo sistema *Thor Arquivista – Orquestrador de Preservação Digital*.  
Cada script pode ser executado de forma independente pela linha de comando, ou controlado pelo *Worker* interno da aplicação.

---

## Sumário
- [hash_files.py — Geração de Manifesto BagIt](#hash_filespy--geração-de-manifesto-bagit)
- [verify_fixity.py — Verificação de Fixidez](#verify_fixitypy--verificação-de-fixidez)
- [build_bag.py — Empacotamento BagIt (em desenvolvimento)](#build_bagpy--empacotamento-bagit-em-desenvolvimento)
- [build_sip.py — Geração de SIP (em desenvolvimento)](#build_sippy--geração-de-sip-em-desenvolvimento)
- [format_identify.py — Identificação de Formatos (em desenvolvimento)](#format_identifypy--identificação-de-formatos-em-desenvolvimento)
- [replicate.py — Replicação de Diretórios (em desenvolvimento)](#replicatepy--replicação-de-diretórios-em-desenvolvimento)
- [Boas práticas de execução](#boas-práticas-de-execução)
- [Analise e eliminação de duplicatas](#duplicate_finderpy--localizador-de-duplicidades-e-geração-de-scripts-de-tratamento)
---

## `hash_files.py` — Geração de Manifesto BagIt

Script responsável por gerar manifestos **BagIt** no formato:
```
<hash>␠␠<caminho/relativo>
```

### Uso
```bash
python scripts/hash_files.py --raiz <pasta> --saida <manifesto> [--algo sha256] [--ignore-hidden] [--progress]
```

### Principais parâmetros
| Parâmetro | Descrição |
|------------|------------|
| `--raiz` | Caminho da pasta onde estão os arquivos a serem processados |
| `--saida` | Caminho do manifesto de saída (ex.: manifest-sha256.txt) |
| `--algo` | Algoritmo de hash (`sha256`, `sha512`, `md5`, `sha1`, `blake2b`, `blake2s`) |
| `--ignore-hidden` | Ignora arquivos/pastas iniciados por ponto |
| `--progress` | Exibe progresso no stderr |
| `--include-ext` / `--exclude-ext` | Filtra extensões específicas |
| `--pattern` | Glob relativo (ex.: `**/*.pdf`) |
| `--workers` | Número de threads de hashing |

### Exemplo prático
```bash
python scripts/hash_files.py   --raiz "D:/acervo"   --saida "D:/acervo/manifest-sha256.txt"   --algo sha256   --ignore-hidden   --progress
```

### Entrada
```
D:/acervo/
├─ carta1.pdf
├─ carta2.pdf
└─ subpasta/
   └─ imagem1.jpg
```

### Saída (`manifest-sha256.txt`)
```
d2c7c963f83b2f92e4f18f46c92a89f0  carta1.pdf
7ad0c4583a61e894bc1c1ccdc22cf34b  carta2.pdf
fb7ffb8f67bba7b5a612aab524e667a9  subpasta/imagem1.jpg
```

---

## `verify_fixity.py` — Verificação de Fixidez

Compara os hashes do manifesto BagIt com os arquivos existentes.

### Uso
```bash
python scripts/verify_fixity.py --raiz <pasta> --manifesto <arquivo> [--report-extras] [--progress]
```

### Parâmetros principais
| Parâmetro | Descrição |
|------------|------------|
| `--raiz` | Pasta onde estão os arquivos originais |
| `--manifesto` | Caminho do manifesto a validar |
| `--algo` | (opcional) Força o algoritmo |
| `--report-extras` | Mostra arquivos em disco não listados |
| `--progress` | Exibe progresso durante a execução |

### Exemplo prático
```bash
python scripts/verify_fixity.py   --raiz "D:/acervo"   --manifesto "D:/acervo/manifest-sha256.txt"   --report-extras   --progress
```

### Entrada
```
D:/acervo/
├─ carta1.pdf
├─ carta2.pdf
├─ subpasta/
│  └─ imagem1.jpg
└─ manifest-sha256.txt
```

### Saída esperada
```
=== Verificação de fixidez ===
Manifesto : D:/acervo/manifest-sha256.txt
Raiz      : D:/acervo
Algoritmo : sha256
Total     : 3
OK        : 3
Faltando  : 0
Divergências: 0
Extras    : 0
```

Se um arquivo estiver faltando:
```
=== Verificação de fixidez ===
OK        : 2
Faltando  : 1
Divergências: 0

-- Faltando --
subpasta/imagem1.jpg
```

---

## `build_bag.py` — Empacotamento BagIt

Cria pacotes completos no padrao BagIt 0.97, com `bagit.txt`, `bag-info.txt`, `data/`, `manifest-ALGO.txt` e opcionalmente `tagmanifest-ALGO.txt`. Suporta preenchimento de `bag-info.txt` a partir de **profiles** em `profiles/*-profileBagit.json`.

### Uso
```bash
python scripts/build_bag.py SRC DST
  [--algo ALGO]
  [--mode {copy,link,move}]
  [--pattern GLOB]
  [--include-hidden]
  [--follow-symlinks]
  [--tagmanifest]
  [--organization ORG]
  [--source-organization SRCORG]
  [--contact-name NAME]
  [--contact-email EMAIL]
  [--description TEXT]
  [--profile NAME_OR_JSON_PATH]
  [--profile-param KEY=VALUE]    # pode repetir
```

### Principais parametros
| Parametro | Descricao |
|---|---|
| `SRC` | Pasta fonte do payload a ser empacotado em `data/` |
| `DST` | Pasta destino do pacote BagIt. Deve estar vazia ou nao existir |
| `--algo` | Algoritmo do manifesto. Padrao: `sha256` |
| `--mode` | Transferencia para `data/`: `copy` (padrao), `link` (hardlink, com fallback para copia), `move` |
| `--pattern` | Glob para selecionar arquivos da origem. Ex.: `*.pdf`, `**/*.tif` |
| `--include-hidden` | Inclui arquivos ocultos (nomes iniciando com ponto) |
| `--follow-symlinks` | Segue symlinks ao varrer a origem |
| `--tagmanifest` | Gera tagmanifest para `bagit.txt`, `bag-info.txt` e `manifest-ALGO.txt` |
| `--organization` | Valor que pode alimentar o profile (`Organization`) |
| `--source-organization` | Valor que pode alimentar o profile (`Source-Organization`) |
| `--contact-name` | Valor que pode alimentar o profile (`Contact-Name`) |
| `--contact-email` | Valor que pode alimentar o profile (`Contact-Email`) |
| `--description` | Valor que pode alimentar o profile (`External-Description`) |
| `--profile` | Nome logico do profile em `profiles/[NAME]-profileBagit.json` ou caminho para um JSON de profile |
| `--profile-param KEY=VALUE` | Parametros extras para preencher placeholders do profile. Pode repetir a opcao |

### Exemplo pratico
```bash
python scripts/build_bag.py "./fonte" "./bag_apesp"   --organization APESP   --source-organization "Secretaria X"   --contact-name "Carlos Eduardo"   --contact-email "carlos@example.org"   --description "Transferencia 2025-10-30 - Serie Y"   --profile apesp   --profile-param transfer_id=TRF-2025-001   --profile-param transfer_desc="Recolhimento serie Y, unidade Z"   --tagmanifest
```

### Entrada
```
./fonte/
├─ carta1.pdf
├─ carta2.pdf
└─ subpasta/
   └─ imagem1.jpg
```

### Saida
```
./bag_apesp/
├─ bagit.txt
├─ bag-info.txt
├─ manifest-sha256.txt
├─ data/
│  ├─ carta1.pdf
│  ├─ carta2.pdf
│  └─ subpasta/
│     └─ imagem1.jpg
└─ tagmanifest-sha256.txt    # se --tagmanifest for usado
```

### Sobre profiles BagIt
- Local de busca por nome logico: `profiles/[NAME]-profileBagit.json`.
- Estrutura minima do profile:
  ```json
  {
    "bag_info": {
      "Source-Organization": "{source_organization}",
      "Organization": "{organization}",
      "Contact-Name": "{contact_name}",
      "Contact-Email": "{contact_email}",
      "External-Description": "{external_description}",
      "Internal-Sender-Identifier": "{transfer_id}",
      "Internal-Sender-Description": "{transfer_desc}"
    },
    "required_tags": ["Source-Organization", "Contact-Email"]
  }
  ```
- Placeholders resolvidos automaticamente:
  - Calculados: `bagging_date`, `payload_oxum`, `algo`, `total_bytes`, `file_count`, `src`, `dst`, `bag_software_agent`
  - Via flags: `organization`, `source_organization`, `contact_name`, `contact_email`, `external_description`
  - Via `--profile-param`: quaisquer chaves adicionais, por exemplo `transfer_id`, `serie`, `produtor`
- Observacao: `Bagging-Date`, `Payload-Oxum` e `Bag-Software-Agent` sao sempre escritos com valores calculados pelo script.

### Codigos de retorno
- `0`: sucesso
- `2`: erro de execucao ou parametros invalidos

### Observacoes
- Caminhos no manifesto usam separador `/` e fim de linha LF.
- Se `--mode link` nao for suportado pelo filesystem, o script faz fallback para copia.
- Para usar via interface, o painel `build_bag` enfileira um job `BUILD_BAG` que e mapeado por `core/scripts_map.py` para este script com os argumentos correspondentes.

---

## `build_sip.py` — Geração de SIP (em desenvolvimento)

Cria **Submission Information Packages (SIP)**, com metadados e estrutura definida.

### Uso (planejado)
```bash
python scripts/build_sip.py --fonte <pasta> --saida <pasta> [--id <identificador>]
```

---

## `format_identify.py` — Identificação de Formatos (em desenvolvimento)

Identifica formatos de arquivo, gera CSV com MIME type e extensão detectada.

### Uso (planejado)
```bash
python scripts/format_identify.py --raiz <pasta> --saida <relatorio.csv>
```

---

## `replicate.py` — Replicação de Diretórios (em desenvolvimento)

Copia uma árvore de diretórios para múltiplos destinos, podendo validar hash após a cópia.

### Uso (planejado)
```bash
python scripts/replicate.py --fonte <pasta> --destino <dest1> --destino <dest2> [--verificar-hash]
```

### Exemplo (planejado)
```bash
python scripts/replicate.py --fonte "./dados" --destino "./backup1" --destino "./backup2" --verificar-hash
```

---

## Boas práticas de execução

- Prefira **caminhos relativos** e formato POSIX (`/`).
- Gere manifestos separados por algoritmo (`manifest-sha256.txt`, etc.).
- Use `--ignore-hidden` para evitar arquivos de sistema.
- Utilize `--progress` em coleções grandes.
- Mantenha manifesto e dados juntos.

---

## Exemplo de fluxo completo

1. **Gerar manifesto:**
   ```bash
   python scripts/hash_files.py --raiz "./colecao" --saida "./colecao/manifest-sha256.txt"
   ```

2. **Transferir** ou replicar o conjunto.

3. **Validar integridade:**
   ```bash
   python scripts/verify_fixity.py --raiz "./colecao" --manifesto "./colecao/manifest-sha256.txt"
   ```

4. **Saída esperada:**
   ```
   OK        : 100%
   Faltando  : 0
   Divergências: 0
   ```

---
# `duplicate_finder.py` — Localizador de Duplicidades e Geração de Scripts de Tratamento

Este script detecta **arquivos duplicados** em um diretório, gera **relatórios CSV** e **modelos de decisão**, além de criar **scripts de tratamento** (Linux `.sh` ou Windows `.cmd`) para **mover duplicatas para quarentena** ou **removê-las definitivamente**.  
Todas as operações registram um **log detalhado** das ações realizadas.

---

## ⚙️ Funcionalidades principais

1. **Inventário de arquivos** com hash SHA-256 e metadados (`ctime`, `mtime`, `tamanho`, `caminho_relativo`)  
2. **Detecção de duplicatas** por `(hash, tamanho)`  
3. **Geração de modelo de decisões** para indicar o arquivo a manter e os que podem ser eliminados  
4. **Geração de script de tratamento** para Linux ou Windows:
   - Quarentena (movimentação não destrutiva)
   - Remoção definitiva (com confirmação)
   - Criação automática de log (`.log`)
5. **Geração de dashboards**:
   - **Potencial de recuperação** (base duplicatas)
   - **Recuperação planejada** (base decisões)

---

## 🧭 Uso geral

### 1️⃣ Inventariar arquivos

```bash
python scripts/duplicate_finder.py \\
  --raiz "/caminho/para/storage" \\
  --inventario inventario.csv \\
  --mostrar-progresso
```

Cria `inventario.csv` com SHA-256 e metadados de cada arquivo.

---

### 2️⃣ Detectar duplicatas

```bash
python scripts/duplicate_finder.py \\
  --inventario inventario.csv \\
  --duplicatas duplicatas.csv
```

Gera `duplicatas.csv` listando grupos de arquivos com mesmo hash e tamanho.

---

### 3️⃣ Gerar modelo de decisões

```bash
python scripts/duplicate_finder.py \\
  --from-duplicatas duplicatas.csv \\
  --decisoes decisoes.csv
```

Cria um **modelo de planilha** para revisão humana e justificativa de decisão.

---

### 4️⃣ Gerar script de tratamento

O script pode ser criado para **Linux (.sh)** ou **Windows (.cmd)**, com **ação de quarentena ou remoção definitiva**.

#### 🐧 Linux — mover para quarentena (padrão)

```bash
python scripts/duplicate_finder.py \\
  --decisoes decisoes.csv \\
  --gerar-script-remocao tratar.sh \\
  --sistema linux \\
  --acao quarentena \\
  --prefixo-quarentena QUARENTENA_DUP \\
  --script-log-nome tratamento_duplicatas.log
```

**O que faz:**
- Cria `tratar.sh` e uma pasta `QUARENTENA_DUP_YYYYMMDD_HHMMSS/`
- Move arquivos para quarentena preservando a estrutura
- Gera log detalhado em `tratamento_duplicatas.log`
- Exige confirmação digitando `YES`

#### 🐧 Linux — remover definitivamente

```bash
python scripts/duplicate_finder.py \\
  --decisoes decisoes.csv \\
  --gerar-script-remocao tratar.sh \\
  --sistema linux \\
  --acao remover
```

**O que faz:**
- Cria `tratar.sh` que remove os arquivos após confirmação digitando `DELETE`
- Gera log automático `tratamento_YYYYMMDD_HHMMSS.log`

#### 🪟 Windows — mover para quarentena

```bat
python scripts\duplicate_finder.py ^
  --decisoes decisoes.csv ^
  --gerar-script-remocao tratar.cmd ^
  --sistema windows ^
  --acao quarentena ^
  --prefixo-quarentena QUARENTENA_DUP ^
  --script-log-nome tratamento_duplicatas.log
```

**O que faz:**
- Usa PowerShell para criar pastas e mover arquivos preservando a estrutura
- Gera log em `%cd%\tratamento_duplicatas.log`
- Exige confirmação digitando `YES`

#### 🪟 Windows — remover definitivamente

```bat
python scripts\duplicate_finder.py ^
  --decisoes decisoes.csv ^
  --gerar-script-remocao tratar.cmd ^
  --sistema windows ^
  --acao remover
```

**O que faz:**
- Remove os arquivos após confirmação digitando `DELETE`
- Gera log `tratamento_YYYYMMDD_HHMMSS.log`

---

## 📊 Dashboards

### Potencial de recuperação (duplicatas)

```bash
python scripts/duplicate_finder.py \\
  --inventario inventario.csv \\
  --duplicatas duplicatas.csv \\
  --dashboard-duplicatas-csv dashboard_duplicatas.csv \\
  --dashboard-duplicatas-xlsx dashboard_duplicatas.xlsx
```

### Recuperação planejada (decisões)

```bash
python scripts/duplicate_finder.py \\
  --inventario inventario.csv \\
  --decisoes decisoes.csv \\
  --dashboard-decisoes-csv dashboard_decisoes.csv \\
  --dashboard-decisoes-xlsx dashboard_decisoes.xlsx
```

---

## 📋 Parâmetros principais

| Parâmetro | Descrição |
|------------|------------|
| `--raiz` | Pasta raiz a ser inventariada |
| `--inventario` | Arquivo CSV de inventário |
| `--duplicatas` | Arquivo CSV de duplicatas |
| `--from-duplicatas` | Base de duplicatas para gerar modelo de decisões |
| `--decisoes` | Arquivo CSV de decisões |
| `--gerar-script-remocao` | Gera script de tratamento (`.sh` ou `.cmd`) |
| `--sistema` | `linux` ou `windows` |
| `--acao` | `quarentena` (mover) ou `remover` (excluir) |
| `--prefixo-quarentena` | Prefixo do diretório de quarentena |
| `--script-log-nome` | Nome do arquivo de log do script |
| `--dashboard-duplicatas-*` | Geração de dashboards de duplicatas |
| `--dashboard-decisoes-*` | Geração de dashboards de decisões |

---

## ⚠️ Observações importantes

- **Nunca execute scripts de remoção diretamente em produção.**  
  Revise sempre os caminhos e o arquivo `decisoes.csv` antes de aplicar.
- O modo **quarentena** é **não destrutivo**, ideal para validação e testes.
- Os scripts gerados são **auto-documentados e registram log** com `[OK]`, `[WARN]` e `[INFO]`.
- O log é gravado tanto no terminal quanto em arquivo (`.log`).



## Licença
Este projeto, **Thor Arquivista – Caixa de Ferramentas de Preservação Digital**,  
é licenciado sob a **GNU General Public License v3.0 (GPLv3)**.  

© 2025 Carlos Eduardo Carvalho Amand.  
Você é livre para usar, modificar e redistribuir este software,  
desde que preserve esta licença e atribua o crédito ao autor original.  

Mais informações: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)

