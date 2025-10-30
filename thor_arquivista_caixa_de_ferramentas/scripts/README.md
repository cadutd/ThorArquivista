# Scripts base para um Sistema de Preservação Digital (OAIS-like)

Conjunto inicial de scripts CLI em Python, parametrizados via `argparse`, pensados para compor um pipeline **OAIS** simplificado: geração de fixidez, verificação, empacotamento (BagIt/SIP), identificação de formatos, replicação e registro de eventos **PREMIS** mínimos.

> Requisitos: Python 3.9+, opcionalmente `tqdm` (barra de progresso), `PyYAML` (para ler YAML) e **Siegfried** (`sf`) para identificação de formatos.

## Instalação rápida
```bash
python -m venv .venv && . .venv/bin/activate  # (Linux/macOS)
pip install tqdm pyyaml
# (Opcional) Instale o Siegfried (sf) conforme a documentação oficial do projeto.
```

## Arquivos
- `pd_common.py` — Helpers (hash, leitura de config, JSONL, etc.).
- `hash_files.py` — Varre uma pasta e cria `manifest.tsv` com SHA-256.
- `verify_fixity.py` — Recalcula e compara com `manifest.tsv`.
- `build_bag.py` — Cria pacote **BagIt** mínimo (0.97) com `manifest-sha256.txt`.
- `build_sip.py` — Monta um **SIP** simples (`objects/`, `metadata/`, `manifest-sha256.txt`) e opcionalmente compacta.
- `premis_log.py` — Registra eventos **PREMIS** mínimos (JSONL).
- `format_identify.py` — Identifica formatos via **Siegfried** (`sf`) quando disponível; caso contrário, usa `mimetypes`.
- `replicate_storage.py` — Replica dados para múltiplos destinos, com verificação opcional por hash.
- `config.example.yaml` — Exemplo de configuração compartilhada.

## Exemplos de uso

### 1) Manifesto de fixidez
```bash
python hash_files.py --raiz /dados/origem --saida /pacote/manifest.tsv
```

### 2) Verificação de fixidez
```bash
python verify_fixity.py --raiz /dados/origem --manifesto /pacote/manifest.tsv
```

### 3) Criar BagIt mínimo
```bash
python build_bag.py --fonte /dados/origem --destino /bags --bag-name 2025-10-27_projeto --org APESP
```

### 4) Construir SIP
```bash
python build_sip.py --fonte /dados/origem --saida /sips --sip-id SIP_0001 --zip
```

### 5) Registrar evento PREMIS
```bash
python premis_log.py --arquivo-log /logs/premis.jsonl \
  --tipo "fixity check" --obj-id "SIP_0001/objects/doc.pdf" \
  --detalhe "Verificação de manifesto" --resultado success --agente "Gerenciador"
```

### 6) Identificar formatos
```bash
python format_identify.py --raiz /dados/origem --saida formatos.jsonl
```

### 7) Replicar para múltiplos destinos
```bash
python replicate_storage.py --fonte /sips/SIP_0001 --destino /replicaA --destino /replicaB --verificar-hash
```

## Observações
- Os scripts são modulares e podem ser encadeados por um orquestrador.
- Logs operacionais e de eventos podem ser centralizados em arquivos JSONL e correlacionados por IDs.
- **BagIt** aqui é mínimo; para uso em produção considerar validação externa e tags adicionais.
- **PREMIS** reduzido: ajuste os campos conforme suas políticas institucionais.
- **Siegfried** é recomendado para identificação robusta de formatos.
