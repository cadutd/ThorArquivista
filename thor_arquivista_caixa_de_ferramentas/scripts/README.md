# Manual dos Scripts - Thor Arquivista

Esta pasta contém os scripts de linha de comando usados pelo Thor Arquivista. Eles também são chamados pela interface gráfica por meio do `Worker`, mas podem ser executados diretamente no terminal.

Execute os comandos a partir da raiz do projeto:

```bash
python scripts/<script>.py --help
```

No Windows, use aspas em caminhos com espaços. Os manifestos BagIt gravam caminhos relativos com `/`, mesmo quando o comando recebe caminhos com `\`.

Quando uma opção de progresso está disponível, os scripts usam logs econômicos: total inicial, atualização em marcos de 5%, quantidade restante e resumo final de duração/média. Esse formato evita excesso de saída em lotes grandes e reduz escrita em disco quando os scripts são executados pela interface gráfica.

---

## Sumário

- [`hash_files.py`](#hash_filespy)
- [`verify_fixity.py`](#verify_fixitypy)
- [`build_bag.py`](#build_bagpy)
- [`validate_bag.py`](#validate_bagpy)
- [`incremental_backup_from_fixity.py`](#incremental_backup_from_fixitypy)
- [`build_sip.py`](#build_sippy)
- [`format_identify.py`](#format_identifypy)
- [`replicate_storage.py`](#replicate_storagepy)
- [`backup_plan.py`](#backup_planpy)
- [`duplicate_finder.py`](#duplicate_finderpy)
- [`delete_duplicates_by_manifest.py`](#delete_duplicates_by_manifestpy)
- [`premis_converter.py`](#premis_converterpy)
- [`premis_log.py`](#premis_logpy)
- [Módulo de apoio: `pd_common.py`](#modulo-de-apoio-pd_commonpy)
- [Utilitário de raiz: `gerador_bat.py`](#utilitario-de-raiz-gerador_batpy)
- [Boas práticas](#boas-praticas)
- [Licença](#licenca)

---

## `hash_files.py`

Gera manifesto BagIt de uma pasta.

Formato de saída:

```text
<hash>  <caminho/relativo>
```

Uso básico:

```bash
python scripts/hash_files.py --raiz "D:/acervo" --saida "D:/acervo/manifest-sha256.txt"
```

Uso com opções:

```bash
python scripts/hash_files.py \
  --raiz "D:/acervo" \
  --saida "D:/relatorios/manifest-sha256.txt" \
  --algo sha256 \
  --ignore-hidden \
  --pattern "**/*.pdf" \
  --workers 8 \
  --progress
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta raiz a varrer. Obrigatório. |
| `--saida` | Arquivo de manifesto a gravar. Obrigatório. |
| `--algo` | Algoritmo de hash. Padrão: `sha256`. |
| `--include-ext` | Extensões a incluir, sem ponto. Ex.: `pdf tif jpg`. |
| `--exclude-ext` | Extensões a excluir, sem ponto. |
| `--min-size` | Tamanho mínimo em bytes. |
| `--max-size` | Tamanho máximo em bytes. |
| `--modified-after` | Inclui arquivos modificados após `YYYY-MM-DD`. |
| `--modified-before` | Inclui arquivos modificados antes de `YYYY-MM-DD`. |
| `--pattern` | Glob relativo. Ex.: `**/*.pdf`. |
| `--ignore-hidden` | Ignora itens ocultos iniciados por ponto. Desativado por padrão; na interface gráfica, a opção correspondente abre desmarcada. |
| `--follow-symlinks` | Segue links simbólicos. |
| `--workers` | Número de threads. |
| `--progress` | Mostra progresso no `stderr` em marcos de 5%, com quantidade restante e resumo final. |

Saída esperada:

```text
f2ca1bb6c7e907d06dafe4687e579fce  documento.pdf
9f86d081884c7d659a2feaa0c55ad015  subpasta/imagem.tif
```

---

## `verify_fixity.py`

Verifica fixidez comparando uma pasta com um manifesto BagIt.

Uso básico:

```bash
python scripts/verify_fixity.py --raiz "D:/acervo" --manifesto "D:/acervo/manifest-sha256.txt"
```

Uso com relatório de extras:

```bash
python scripts/verify_fixity.py \
  --raiz "D:/acervo" \
  --manifesto "D:/acervo/manifest-sha256.txt" \
  --report-extras \
  --max-list-items 200 \
  --report-file "D:/acervo/relatorios/fixity_2026-08-01.txt" \
  --progress
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta onde os arquivos esperados estão. Obrigatório. |
| `--manifesto` | Manifesto BagIt a validar. Obrigatório. |
| `--algo` | Força o algoritmo. Se omitido, tenta inferir de `manifest-<algo>.txt`. |
| `--workers` | Número de threads de verificação. |
| `--progress` | Mostra progresso em marcos de 5%, com quantidade restante e resumo de tempo/média. |
| `--strict-missing` | Deixa explícito que faltantes geram erro. |
| `--report-extras` | Compatibilidade. O relatório final sempre lista arquivos extras. |
| `--max-list-items` | Máximo de itens por lista no stdout/log. Padrão: `200`; use `0` para listar tudo. |
| `--report-file` | Caminho para gravar o relatório TXT completo e estruturado. Se omitido, o script gera automaticamente ao lado do manifesto. |

Códigos de saída:

| Código | Significado |
|---|---|
| `0` | Hashes conferem, sem faltantes nem erros de leitura ou enumeração. A presença de extras, isoladamente, não altera o código. |
| `1` | Há faltantes, hashes divergentes, erro de leitura ou busca de extras incompleta. |
| `2` | Raiz ou manifesto inválido/inacessível na validação inicial, manifesto sem entradas válidas ou algoritmo não suportado. |

### Caminhos longos e pastas de rede

No Windows, as operações de leitura e enumeração usam automaticamente caminhos estendidos: `\\?\C:\...` para caminhos locais e `\\?\UNC\servidor\compartilhamento\...` para UNC. Os caminhos do manifesto continuam relativos, com `/`; não é necessário adicionar esses prefixos ao comando.

Exemplo no PowerShell:

```powershell
python scripts/verify_fixity.py --raiz "\\servidor\compartilhamento\acervo" --manifesto "C:/relatorios/manifest-sha256.txt" --report-file "C:/relatorios/fixity.txt" --workers 4 --progress
```

Erros transitórios de leitura, rede e ausência momentânea têm até três tentativas, com pausas de 0,25 e 0,5 segundo. Uma nova tentativa de leitura reinicia o cálculo do hash. Falhas permanentes, como permissão negada, são registradas sem repetição desnecessária. A enumeração de extras também é repetida em falhas transitórias; os resultados parciais de uma tentativa que falhou são descartados.

| Status TSV | Significado |
|---|---|
| `MISSING` | O sistema informou ausência após as tentativas e a raiz permaneceu acessível. |
| `CORRUPT` | Leitura concluída, mas o hash difere do manifesto. |
| `ERROR` | Não foi possível verificar o arquivo; não é contado como corrompido. O detalhe inclui o erro original, caminho completo e comprimento, ou informa que a raiz ficou inacessível. |
| `EXTRA` | Arquivo encontrado na pasta e ausente no manifesto. |
| `SCAN_ERROR` | Busca por extras incompleta; usa `.` no campo `path` e não representa arquivo a restaurar. |

O relatório mantém contagens separadas de hashes divergentes e erros de acesso ou leitura. Quando a enumeração falha, exibe **Busca de extras: incompleta (a contagem não é conclusiva)** e retorna `1`. Registros íntegros (`OK`) são omitidos do TSV.

Para rever falsos ausentes de relatórios antigos, execute novamente com a versão atual, especialmente quando o caminho completo tiver 260 caracteres ou mais. As novas tentativas não garantem acesso se a rede ou as permissões continuarem indisponíveis.

Relatório final:

```text
=== Verificação de fixidez ===
Manifesto : D:\acervo\manifest-sha256.txt
Raiz      : D:\acervo
Algoritmo : sha256
Total no manifesto: 100
Arquivos verificados íntegros: 100
Arquivos verificados corrompidos: 0
Erros de acesso ou leitura: 0
Arquivos no manifesto ausentes na pasta analisada: 0
Divergências: 0
Arquivos na pasta analisada ausentes no manifesto: 0
Busca de extras: concluída

-- Arquivos no manifesto ausentes na pasta analisada --
Nenhum

-- Arquivos verificados corrompidos ou com erro --
Nenhum

-- Arquivos na pasta analisada ausentes no manifesto --
Nenhum

=== Resumo final da verificação ===
Total no manifesto: 100
Arquivos verificados íntegros: 100
Arquivos verificados corrompidos: 0
Erros de acesso ou leitura: 0
Arquivos no manifesto ausentes na pasta analisada: 0
Arquivos na pasta analisada ausentes no manifesto: 0
Tempo de verificação: 12.34s
Média por arquivo verificado: 0.1234s/arquivo
```

Exemplo de stdout/log quando há lista grande compactada:

```text
[INFO] Verificação finalizada: 30860 arquivo(s) verificado(s) em 2364.43s; média 0.0766s/arquivo
[INFO] Procurando arquivos extras em disco...
=== Verificação de fixidez ===
Total no manifesto: 30860
Arquivos verificados íntegros: 28363
Arquivos verificados corrompidos: 0
Erros de acesso ou leitura: 0
Arquivos no manifesto ausentes na pasta analisada: 2497
Arquivos na pasta analisada ausentes no manifesto: 0
Busca de extras: concluída

-- Arquivos no manifesto ausentes na pasta analisada --
data/foto_0001.jpg
data/foto_0002.jpg
... 2297 item(s) omitidos nesta visualização.

Relatório completo: D:\acervo\relatorios\fixity_2026-08-01.txt

=== Resumo final da verificação ===
Total no manifesto: 30860
Arquivos verificados íntegros: 28363
Arquivos verificados corrompidos: 0
Erros de acesso ou leitura: 0
Arquivos no manifesto ausentes na pasta analisada: 2497
Arquivos na pasta analisada ausentes no manifesto: 0
```

As contagens e seções de listas aparecem mesmo quando o valor é `0`; listas vazias usam `Nenhum`. Quando o manifesto está dentro da pasta analisada, o próprio arquivo de manifesto não é contado como extra. Para listas grandes, o stdout/log mostra apenas os primeiros itens de cada seção e informa o caminho do relatório TXT completo.

O relatório TXT é sempre emitido. Além da visualização humana, ele contém a seção `Dados estruturados para backup incremental` em TSV:

```text
# Registros OK são omitidos para reduzir o tamanho do relatório.
status	path	expected_hash	actual_hash	detail
MISSING	data/b.txt	<hash>		Arquivo listado no manifesto ausente na pasta analisada
CORRUPT	data/c.txt	<hash>	<hash_atual>	Hash gerado diferente do hash no manifesto
ERROR	data/restrito.txt	<hash>		Erro de acesso; caminho completo e comprimento registrados no detalhe
EXTRA	data/d.txt			Arquivo presente na pasta analisada e ausente no manifesto
SCAN_ERROR	.			Busca de extras incompleta: erro de acesso ao diretório
```

---

## `build_bag.py`

Cria pacote BagIt completo.

Saídas principais:

```text
bagit.txt
bag-info.txt
manifest-sha256.txt
data/
tagmanifest-sha256.txt   # opcional
```

Uso básico:

```bash
python scripts/build_bag.py "D:/acervo/fonte" "D:/bags/bag_001"
```

Uso com metadados e tagmanifest:

```bash
python scripts/build_bag.py "D:/acervo/fonte" "D:/bags/bag_001" \
  --algo sha256 \
  --mode copy \
  --pattern "**/*.pdf" \
  --tagmanifest \
  --organization "APESP" \
  --source-organization "Secretaria X" \
  --contact-name "Nome do contato" \
  --contact-email "contato@example.org" \
  --description "Transferência 2026-04" \
  --profile apesp \
  --profile-param transfer_id=TRF-2026-001
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `src` | Pasta fonte do payload. Obrigatório. |
| `dst` | Pasta destino do BagIt. Obrigatório. |
| `--algo` | Algoritmo do manifesto. Padrão: `sha256`. |
| `--mode` | `copy`, `link` ou `move`. Padrão: `copy`. |
| `--pattern` | Glob dos arquivos a empacotar. Padrão: `*`. |
| `--include-hidden` | Inclui arquivos ocultos. |
| `--follow-symlinks` | Segue links simbólicos. |
| `--tagmanifest` | Gera tagmanifest dos arquivos de tag. |
| `--organization` | Valor de `Organization`. |
| `--source-organization` | Valor de `Source-Organization`. |
| `--contact-name` | Valor de `Contact-Name`. |
| `--contact-email` | Valor de `Contact-Email`. |
| `--description` | Valor de `External-Description`. |
| `--profile` | Nome lógico em `profiles/[nome]-profileBagit.json` ou caminho JSON. |
| `--profile-param` | Parâmetro extra `chave=valor`. Pode repetir. |

Observações:

- O destino deve não existir ou estar vazio.
- Em `--mode link`, se hardlink não for suportado, o script faz fallback para cópia.
- Profiles podem preencher campos obrigatórios de `bag-info.txt`.
- Transferência e geração do manifesto do payload registram progresso em marcos de 5% e resumo de tempo/média.

---

## `validate_bag.py`

Valida um pacote BagIt gerado pelo Thor Arquivista.

Uso básico:

```bash
python scripts/validate_bag.py "D:/bags/bag_001"
```

Uso com progresso e algoritmo específico:

```bash
python scripts/validate_bag.py "D:/bags/bag_001" --algo sha256 --progress
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `bag` | Pasta raiz do pacote BagIt. Obrigatório. |
| `--algo` | Valida apenas manifestos do algoritmo informado. Se omitido, valida todos os `manifest-*.txt` e `tagmanifest-*.txt`. |
| `--progress` | Mostra progresso no `stderr` em marcos de 5%, com quantidade restante e resumo final. |

Validações executadas:

- presença de `bagit.txt`, `bag-info.txt` e `data/`;
- conteúdo mínimo de `bagit.txt` para BagIt 0.97 e UTF-8;
- hash dos arquivos listados em `manifest-*.txt`;
- arquivos de payload ausentes, corrompidos ou extras em `data/`;
- hash dos arquivos listados em `tagmanifest-*.txt`, quando existirem.

O script retorna `0` quando o pacote é válido e `2` quando encontra inconsistências.

---

## `incremental_backup_from_fixity.py`

Aplica um backup incremental usando o relatório TXT estruturado emitido por `verify_fixity.py`.
Nos relatórios novos, registros `OK` são omitidos da seção TSV para reduzir o tamanho do arquivo. O script continua aceitando relatórios antigos que tenham linhas `OK`, ignorando-as.

Uso básico:

```bash
python scripts/incremental_backup_from_fixity.py \
  --relatorio-fixidez "D:/acervo/verify_fixity_report.txt" \
  --origem "D:/origem" \
  --destino "E:/backup" \
  --progress
```

Uso em simulação:

```bash
python scripts/incremental_backup_from_fixity.py \
  --relatorio-fixidez "D:/acervo/verify_fixity_report.txt" \
  --origem "D:/origem" \
  --destino "E:/backup" \
  --saida-relatorio "D:/acervo/incremental_report.txt" \
  --dry-run
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--relatorio-fixidez` | Relatório TXT gerado por `verify_fixity.py`. Obrigatório. |
| `--origem` | Pasta de origem do backup. Obrigatório. |
| `--destino` | Pasta de destino a atualizar. Obrigatório. |
| `--saida-relatorio` | Relatório TXT da aplicação incremental. Se omitido, gera no destino. |
| `--dry-run` | Simula sem copiar arquivos. |
| `--progress` | Mostra progresso em marcos de 5%. |

Regras por status do relatório de fixidez:

| Status | Ação |
|---|---|
| `OK` | Ignora quando presente em relatórios antigos. |
| `MISSING` | Copia o arquivo da origem para o destino. |
| `CORRUPT` | Substitui o arquivo do destino pelo arquivo da origem. |
| `ERROR` | Tenta copiar novamente da origem. |
| `EXTRA` | Reporta, mas não exclui automaticamente. |
| `SCAN_ERROR` | Ignora: é falha de enumeração, não arquivo a copiar. Corrija o acesso e gere uma nova verificação para completar a busca de extras. |

Exemplo de relatório de aplicação:

```text
=== Backup incremental por relatório de fixidez ===
Relatório de fixidez: D:\acervo\verify_fixity_report.txt
Origem: D:\origem
Destino: E:\backup
Modo simulação: não
Registros lidos: 4
Registros OK ignorados: 0
Registros EXTRA ignorados: 1
Arquivos candidatos a copiar: 3
Arquivos copiados: 3
Arquivos ausentes na origem: 0
Caminhos inválidos no relatório: 0
Falhas de cópia: 0
```

Quando o caminho do relatório começa com `data/`, a origem também é testada sem esse prefixo. Isso permite usar relatórios de pacotes BagIt em que o destino mantém payload sob `data/`, mas a origem do backup é a pasta original.

---

## `build_sip.py`

Cria um SIP simples com objetos, metadados e manifesto SHA-256.

Estrutura gerada:

```text
<saida>/<sip-id>/
  objects/
  metadata/metadata.json
  manifest-sha256.txt
```

Uso básico:

```bash
python scripts/build_sip.py --fonte "D:/acervo/fonte" --saida "D:/sips" --sip-id "SIP_001"
```

Gerar também ZIP:

```bash
python scripts/build_sip.py \
  --fonte "D:/acervo/fonte" \
  --saida "D:/sips" \
  --sip-id "SIP_001" \
  --zip
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--fonte` | Pasta de origem dos objetos. Obrigatório. |
| `--saida` | Diretório onde o SIP será criado. Obrigatório. |
| `--sip-id` | Identificador/nome do SIP. Obrigatório. |
| `--zip` | Compacta o SIP em ZIP. |
| `--no-zip` | Não compacta. Padrão. |
| `--config` | Arquivo YAML/JSON opcional. |
| `--log-jsonl` | Caminho de log JSONL opcional. |
| `--quiet` | Modo silencioso. |

---

## `format_identify.py`

Identifica formato de arquivos em uma pasta.

Se o utilitário externo `sf` (Siegfried) estiver disponível no `PATH`, o script usa Siegfried. Caso contrário, usa fallback por `mimetypes`.

Uso imprimindo no terminal:

```bash
python scripts/format_identify.py --raiz "D:/acervo"
```

Uso gravando JSONL:

```bash
python scripts/format_identify.py --raiz "D:/acervo" --saida "D:/relatorios/formatos.jsonl"
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta a varrer. Obrigatório. |
| `--saida` | Arquivo JSONL de saída. Se omitido, imprime no terminal. |
| `--config` | Arquivo YAML/JSON opcional. |
| `--log-jsonl` | Caminho de log JSONL opcional. |
| `--quiet` | Modo silencioso. |

Exemplo de linha JSONL:

```json
{"path":"D:/acervo/doc.pdf","sha256":"...","mime":"application/pdf","id":"fmt/18","format":"Acrobat PDF","basis":"...","relpath":"doc.pdf"}
```

---

## `replicate_storage.py`

Replica arquivos para um ou mais destinos e valida a cópia por manifesto.

Fluxo:

1. Gera `manifest-sha256.txt` da pasta fonte dentro de cada destino.
2. Copia os arquivos.
3. Valida cada destino com `verify_fixity.py`.

As etapas de manifesto, cópia e verificação usam progresso em marcos de 5% quando o script não está em `--quiet`.

Uso com um destino:

```bash
python scripts/replicate_storage.py --fonte "D:/acervo" --destino "E:/backup"
```

Uso com múltiplos destinos:

```bash
python scripts/replicate_storage.py \
  --fonte "D:/acervo" \
  --destino "E:/backup_1" \
  --destino "F:/backup_2"
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--fonte` | Pasta de origem. Obrigatório. |
| `--destino` | Pasta de destino. Obrigatório; pode repetir. |
| `--verificar-hash` | Compatibilidade. A verificação por manifesto é sempre executada. |
| `--config` | Arquivo YAML/JSON opcional. |
| `--log-jsonl` | Caminho de log JSONL opcional. |
| `--quiet` | Modo silencioso. |

Proteção:

- O destino não pode estar dentro da origem.
- Se a verificação falhar, o script encerra com erro.

---

## `backup_plan.py`

Executa backup preservacional incremental com pastas e manifestos independentes por origem. Os arquivos ficam em `<destino>/<origem>/`; o manifesto atual fica em `<destino>/thor-backup/manifests/<origem>/manifest-<algo>.txt`. Os caminhos dentro de cada manifesto são relativos à pasta da respectiva origem no destino.

Uso básico e retomada (remova `thor-backup/checkpoints/STOP` antes de retomar pela linha de comando):

```bash
python scripts/backup_plan.py --config "D:/planos/backup.json" --progress
python scripts/backup_plan.py --resume --config "D:/planos/backup.json" --progress
```

Exemplo de plano:

```json
{
  "name": "acervo_institucional",
  "destination": "E:/Backup",
  "sources": [
    {"name": "documentos", "path": "D:/Acervo/Documentos"},
    {"name": "imagens", "path": "D:/Acervo/Imagens"}
  ],
  "options": {
    "algo": "sha256",
    "ignore_hidden": true,
    "follow_symlinks": false
  }
}
```

O algoritmo padrão é `sha256`; o editor também oferece `sha512` e `md5`. A opção `ignore_hidden` filtra nomes iniciados por ponto, e `follow_symlinks` controla o seguimento de links simbólicos.

Estrutura criada para esse plano:

```text
Backup/
  documentos/
  imagens/
  thor-backup/
    configs/acervo_institucional_<execucao>.json
    manifests/
      documentos/manifest-sha256.txt
      imagens/manifest-sha256.txt
    historico/<execucao>/
      documentos/manifest-sha256.txt
      imagens/manifest-sha256.txt
      alteracoes.json
    checkpoints/acervo_institucional.state.json
    relatorios/acervo_institucional_<execucao>_relatorio.txt
    logs/premis_events.jsonl
    versoes/<execucao>/<origem>/
```

`versoes/` recebe arquivos somente quando há versões anteriores a preservar. O arquivo `STOP` aparece em `checkpoints/` quando uma pausa é solicitada.

Scripts relacionados:

```bash
python scripts/backup_manifest_build.py --raiz "D:/Acervo/Documentos" --saida "D:/manifest-sha256.txt"
python scripts/backup_manifest_diff.py --origem "D:/manifest-sha256.txt" --destino "E:/Backup/thor-backup/manifests/documentos/manifest-sha256.txt"
python scripts/backup_verify.py --destino "E:/Backup" --progress
python scripts/backup_report.py --destino "E:/Backup" --backup "acervo_institucional"
```

| Script | Responsabilidade |
|---|---|
| `backup_manifest_build.py` | Gera manifesto com caminhos relativos, prefixo opcional, algoritmo configurável e opções de ocultos e links simbólicos. |
| `backup_manifest_diff.py` | Classifica diferenças como `new`, `changed`, `same` e `removed`. |
| `backup_verify.py` | Descobre os manifestos por origem, identifica seus algoritmos e verifica cada pasta correspondente. |
| `backup_report.py` | Lista checkpoints, relatórios e manifestos históricos. |

`backup_verify.py` verifica todos os manifestos encontrados por padrão. `--algo sha512`, por exemplo, filtra a verificação por algoritmo. Origens vazias também possuem manifesto e podem ser verificadas. Os relatórios são gravados em `thor-backup/relatorios/verificacao_<execucao>/`, sem acrescentar arquivos às pastas das origens.

Para registrar um evento PREMIS `FIXITY_CHECK` por manifesto:

```bash
python scripts/backup_verify.py --destino "E:/Backup" --premis-log "E:/Backup/thor-backup/logs/premis_events.jsonl" --progress
```

Relatório final:

- O arquivo `relatorios/<backup>_<execucao>_relatorio.txt` é gravado em UTF-8, com identificação do plano, execução, destino, algoritmo e indicação de retomada.
- Apresenta as origens e seus manifestos, contagens e seções para arquivos novos, alterados, iguais, ausentes na origem e falhas. Seções vazias exibem `Nenhum`.
- Cada item mostra caminho relativo, origem e destino quando disponíveis, hashes completos e detalhes da preservação de versões.
- O resumo final informa o total de arquivos relacionados, cópias conferidas, resultados por categoria e duração. Arquivos iguais não são apresentados como verificados novamente no destino.
- O TXT contém todas as listas; o log do Worker recebe apenas o resumo e o caminho do relatório completo. O checkpoint e o evento `BACKUP_COMPLETED` apontam para esse TXT.
- As contagens referem-se à execução atual, inclusive na retomada. O relatório final é emitido ao concluir o backup.

Exemplo ilustrativo do TXT (hashes abreviados; no relatório real são gravados integralmente):

```text
=== Backup preservacional ===
Backup    : acervo_institucional
Execução  : <execucao>
Plano     : D:/planos/backup.json
Destino   : E:/Backup
Algoritmo : sha256
Resultado : CONCLUÍDO
Retomada de checkpoint: não

-- Origens e manifestos --
Origem: documentos
  Pasta de origem: D:/Acervo/Documentos
  Pasta no destino: E:/Backup/documentos
  Manifesto: E:/Backup/thor-backup/manifests/documentos/manifest-sha256.txt
Origem: imagens
  Pasta de origem: D:/Acervo/Imagens
  Pasta no destino: E:/Backup/imagens
  Manifesto: E:/Backup/thor-backup/manifests/imagens/manifest-sha256.txt

-- Contagens da execução --
Total de arquivos no relatório: 4
Arquivos novos copiados: 1
Arquivos alterados copiados: 1
Cópias com hash conferido: 2
Arquivos iguais ao manifesto (sem nova cópia): 1
Arquivos ausentes na origem e preservados no destino: 1
Arquivos com falha: 0
Tempo total de execução: 12.34s

-- Arquivos novos copiados (1) --
documentos/contrato.pdf
  Origem: D:/Acervo/Documentos/contrato.pdf
  Destino: E:/Backup/documentos/contrato.pdf
  Hash registrado: a81f...

-- Arquivos alterados copiados (1) --
documentos/ata.pdf
  Origem: D:/Acervo/Documentos/ata.pdf
  Destino: E:/Backup/documentos/ata.pdf
  Hash anterior: b92e...
  Hash registrado: c73a...
  Detalhe: Versão anterior preservada em E:/Backup/thor-backup/versoes/<execucao>/documentos/ata.pdf

-- Arquivos iguais ao manifesto (1) --
imagens/fotografia.jpg
  Hash registrado: d64b...

-- Arquivos ausentes na origem e preservados no destino (1) --
documentos/antigo.pdf
  Hash anterior: e55c...
  Detalhe: Ausente na origem; preservado no backup e mantido no manifesto.

-- Arquivos com falha (0) --
Nenhum

-- Critérios de leitura --
Os caminhos dos arquivos são relativos à raiz do destino e incluem o nome da origem.
Novos e alterados: o hash da cópia foi conferido contra o hash da origem.
Iguais: o hash da origem coincide com o manifesto; o conteúdo no destino não foi verificado novamente.
Ausentes na origem: os arquivos e seus registros no manifesto foram mantidos no destino.
As contagens descrevem esta execução; em uma retomada, cópias já persistidas podem aparecer como iguais.

=== Resumo final do backup ===
Total de arquivos no relatório: 4
Arquivos novos copiados: 1
Arquivos alterados copiados: 1
Cópias com hash conferido: 2
Arquivos iguais ao manifesto (sem nova cópia): 1
Arquivos ausentes na origem e preservados no destino: 1
Arquivos com falha: 0
Tempo total de execução: 12.34s
Relatório completo: E:/Backup/thor-backup/relatorios/acervo_institucional_<execucao>_relatorio.txt
```

Parada e retomada:

- Crie `thor-backup/checkpoints/STOP` no destino.
- Após processar um arquivo, inclusive um arquivo igual, a rotina consulta o marcador, salva manifestos e checkpoint, registra PREMIS e encerra como `PAUSED`.
- A geração dos manifestos de origem não é interrompida por `STOP`.
- Remova o marcador antes de usar `--resume`; o botão **Retomar** da interface faz essa remoção no destino definido pelo plano.
- O checkpoint deve pertencer a uma execução interrompida com a mesma estrutura, algoritmo, destino e origens. Na retomada, o incremental recalcula os manifestos das origens e compara com o estado persistido no destino.

Eventos registrados por `backup_plan.py`:

```text
BACKUP_STARTED
BACKUP_INCREMENTAL
BACKUP_PAUSED
BACKUP_RESUMED
BACKUP_COMPLETED
BACKUP_FAILED
```

`BACKUP_INCREMENTAL` é registrado quando existem entradas nos manifestos anteriores. Na execução direta, o log padrão é `thor-backup/logs/premis_events.jsonl`; `--premis-log` permite alterar o caminho. Pela interface, o Worker fornece o log configurado na aplicação tanto para o backup quanto para a verificação. `backup_verify.py` registra `FIXITY_CHECK` somente quando recebe `--premis-log`.

Regras de preservação:

- Cada cópia nova ou alterada tem o hash conferido contra o manifesto gerado da origem.
- A versão anterior de um arquivo alterado é movida para `thor-backup/versoes/<execucao>/<origem>/`, preservando o caminho relativo.
- Arquivos removidos da origem continuam no destino e no respectivo manifesto.
- Arquivos iguais são identificados comparando o hash da origem com o manifesto do destino. O incremental não verifica novamente seu conteúdo no destino nem recompõe automaticamente arquivos ausentes ou corrompidos; use `backup_verify.py` para detectá-los.
- Manifestos são gravados em arquivo temporário e substituídos após a escrita. Cada execução concluída guarda uma cópia por origem em `historico/<execucao>/`.
- Nomes de origem são normalizados; colisões após normalização, inclusive diferenças apenas de maiúsculas e minúsculas, são recusadas. `thor-backup` é reservado.
- Origem e destino não podem estar contidos um no outro.
- Destinos da estrutura anterior são recusados sem conversão automática. Use um novo destino e mantenha os arquivos existentes preservados.
- Os manifestos do destino são a fonte de verdade do incremental; nenhum banco SQL é usado.
- Com `--progress`, a geração dos manifestos de origem e a aplicação incremental registram progresso em marcos de 5%.

Testes:

```powershell
python -B tests/run_backup_tests_html.py
```

O comando executa os testes de scripts e de interface com widgets simulados e grava `tests/reports/backup_tests_report.html`.

## `duplicate_finder.py`

Ferramenta multifunção para inventariar arquivos, detectar duplicatas, gerar planilha de decisão, gerar scripts de tratamento e dashboards.

### 1. Inventariar arquivos

```bash
python scripts/duplicate_finder.py \
  --raiz "D:/acervo" \
  --inventario "D:/relatorios/inventario.csv" \
  --mostrar-progresso
```

Gera CSV com hash SHA-256, tamanho e metadados.

### 2. Detectar duplicatas

```bash
python scripts/duplicate_finder.py \
  --inventario "D:/relatorios/inventario.csv" \
  --duplicatas "D:/relatorios/duplicatas.csv"
```

Gera CSV com grupos de duplicatas.

### 3. Gerar modelo de decisões

```bash
python scripts/duplicate_finder.py \
  --from-duplicatas "D:/relatorios/duplicatas.csv" \
  --decisoes "D:/relatorios/decisoes.csv"
```

Gera CSV para revisão humana. Use esse arquivo para indicar o que manter e o que tratar.

### 4. Gerar script de tratamento

Mover para quarentena no Windows:

```bash
python scripts/duplicate_finder.py \
  --decisoes "D:/relatorios/decisoes.csv" \
  --gerar-script-remocao "D:/relatorios/tratar.cmd" \
  --sistema windows \
  --acao quarentena \
  --prefixo-quarentena "QUARENTENA_DUP"
```

Mover para quarentena no Linux/macOS:

```bash
python scripts/duplicate_finder.py \
  --decisoes "D:/relatorios/decisoes.csv" \
  --gerar-script-remocao "D:/relatorios/tratar.sh" \
  --sistema linux \
  --acao quarentena \
  --prefixo-quarentena "QUARENTENA_DUP"
```

Gerar script de remoção definitiva:

```bash
python scripts/duplicate_finder.py \
  --decisoes "D:/relatorios/decisoes.csv" \
  --gerar-script-remocao "D:/relatorios/remover.cmd" \
  --sistema windows \
  --acao remover
```

### 5. Gerar dashboards

Dashboard de potencial de recuperação:

```bash
python scripts/duplicate_finder.py \
  --inventario "D:/relatorios/inventario.csv" \
  --duplicatas "D:/relatorios/duplicatas.csv" \
  --dashboard-duplicatas-csv "D:/relatorios/dashboard_duplicatas.csv" \
  --dashboard-duplicatas-xlsx "D:/relatorios/dashboard_duplicatas.xlsx"
```

Dashboard de recuperação planejada:

```bash
python scripts/duplicate_finder.py \
  --inventario "D:/relatorios/inventario.csv" \
  --decisoes "D:/relatorios/decisoes.csv" \
  --dashboard-decisoes-csv "D:/relatorios/dashboard_decisoes.csv" \
  --dashboard-decisoes-xlsx "D:/relatorios/dashboard_decisoes.xlsx"
```

Parâmetros principais:

| Parâmetro | Descrição |
|---|---|
| `--raiz` | Pasta a inventariar. |
| `--inventario` | CSV de inventário. |
| `--duplicatas` | CSV de duplicatas. |
| `--from-duplicatas` | CSV de duplicatas usado para gerar decisões. |
| `--decisoes` | CSV de decisões. |
| `--gerar-script-remocao` | Caminho do script `.sh` ou `.cmd` a gerar. |
| `--sistema` | `linux` ou `windows`. |
| `--acao` | `quarentena` ou `remover`. |
| `--prefixo-quarentena` | Prefixo da pasta de quarentena. |
| `--script-log-nome` | Nome do log gerado pelo script de tratamento. |
| `--mostrar-progresso` | Mostra progresso no inventário em marcos de 5%, com quantidade restante e resumo final. |
| `--dashboard-duplicatas-csv` | CSV de dashboard de duplicatas. |
| `--dashboard-duplicatas-xlsx` | XLSX de dashboard de duplicatas. |
| `--dashboard-decisoes-csv` | CSV de dashboard de decisões. |
| `--dashboard-decisoes-xlsx` | XLSX de dashboard de decisões. |

Aviso:

- Revise `decisoes.csv` antes de executar qualquer script de tratamento.
- Prefira `quarentena` antes de usar `remover`.

---

## `delete_duplicates_by_manifest.py`

Apaga arquivos de uma pasta de possíveis duplicatas quando o hash SHA-256 já existe no manifesto gerado a partir de uma pasta origem.

Fluxo:

1. Gera `manifest-sha256.txt` da pasta origem.
2. Percorre a pasta de possíveis duplicatas.
3. Apaga arquivos cujo SHA-256 aparece no manifesto.
4. Gera `relatorio_exclusao_duplicatas.csv` com arquivos apagados e espaço recuperado.

Uso básico:

```bash
python scripts/delete_duplicates_by_manifest.py \
  --origem "D:/acervo/originais" \
  --duplicatas "D:/acervo/possiveis_duplicatas"
```

Uso com pastas de saída:

```bash
python scripts/delete_duplicates_by_manifest.py \
  --origem "D:/acervo/originais" \
  --duplicatas "D:/acervo/possiveis_duplicatas" \
  --manifesto "D:/relatorios/manifesto_origem" \
  --relatorio "D:/relatorios/exclusao_duplicatas" \
  --progress
```

Saídas:

```text
D:/relatorios/manifesto_origem/manifest-sha256.txt
D:/relatorios/exclusao_duplicatas/relatorio_exclusao_duplicatas.csv
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--origem` | Pasta usada como referência. Obrigatório. |
| `--duplicatas` | Pasta a percorrer e limpar. Obrigatório. |
| `--manifesto` | Pasta onde será gravado `manifest-sha256.txt`. |
| `--relatorio` | Pasta onde será gravado `relatorio_exclusao_duplicatas.csv`. |
| `--progress` | Mostra progresso em marcos de 5%, com quantidade restante e resumo final. |

Proteções:

- Origem e duplicatas não podem ser iguais.
- Origem e duplicatas não podem ser pastas sobrepostas.
- O manifesto e o relatório não são varridos como candidatos de exclusão.

---

## `premis_converter.py`

Converte registros PREMIS entre XML, CSV e JSON e pode validar XML contra XSD.

Uso para validar XML:

```bash
python scripts/premis_converter.py --in "D:/premis/premis.xml" --validate
```

Converter XML para CSV:

```bash
python scripts/premis_converter.py \
  --in "D:/premis/premis.xml" \
  --out "D:/premis/premis.csv" \
  --validate \
  --schema "schemas/premis-v3-0.xsd"
```

Converter CSV para XML:

```bash
python scripts/premis_converter.py \
  --in "D:/premis/premis.csv" \
  --out "D:/premis/premis.xml" \
  --schema "schemas/premis-v3-0.xsd"
```

Converter JSON para XML:

```bash
python scripts/premis_converter.py \
  --in "D:/premis/premis.json" \
  --out "D:/premis/premis.xml" \
  --validate
```

Gerar exemplos:

```bash
python scripts/premis_converter.py --example
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--in` | Arquivo de entrada `.xml`, `.csv` ou `.json`. |
| `--out` | Arquivo de saída `.xml`, `.csv` ou `.json`. |
| `--validate` | Valida XML de entrada ou saída. |
| `--schema` | Caminho alternativo para `premis-v3-0.xsd`. |
| `--example` | Gera exemplos em `./examples`. |

Observação para Windows:

- Se `--help` falhar por encoding do console, execute em um terminal UTF-8 ou use `chcp 65001` antes do comando.

---

## `premis_log.py`

Acrescenta um evento PREMIS simples em um arquivo JSONL.

Uso básico:

```bash
python scripts/premis_log.py \
  --arquivo-log "logs/premis_events.jsonl" \
  --tipo "fixity check" \
  --obj-id "D:/acervo/manifest-sha256.txt"
```

Uso completo:

```bash
python scripts/premis_log.py \
  --arquivo-log "logs/premis_events.jsonl" \
  --tipo "replication" \
  --obj-id "D:/acervo" \
  --detalhe "Cópia para E:/backup validada com manifesto" \
  --resultado "success" \
  --agente "Thor Arquivista"
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `--arquivo-log` | Arquivo JSONL de eventos PREMIS. Obrigatório. |
| `--tipo` | Tipo do evento. Obrigatório. |
| `--obj-id` | Identificador do objeto. Obrigatório. |
| `--detalhe` | Detalhe textual do evento. |
| `--resultado` | Resultado do evento. Padrão: `success`. |
| `--agente` | Nome do agente. Padrão: `Sistema de Preservação`. |

Exemplo de linha JSONL:

```json
{"eventIdentifier":"local-...","eventType":"fixity check","eventDateTime":"...Z","eventDetail":"","eventOutcome":"success","linkingObjectIdentifier":"D:/acervo","linkingAgentName":"Thor Arquivista"}
```

---

## Módulo de apoio: `pd_common.py`

`pd_common.py` não é uma ferramenta de uso direto. Ele concentra funções compartilhadas por outros scripts, como:

- cálculo SHA-256;
- cópia segura;
- iteração de arquivos;
- leitura de configuração YAML/JSON;
- suporte opcional a `tqdm`.

Não execute este arquivo como uma tarefa de preservação.

---

## Utilitário de raiz: `gerador_bat.py`

`gerador_bat.py` fica na raiz do projeto, não na pasta `scripts/`, porque gera arquivos de inicialização ao lado de `app.py`.

Uso padrão:

```powershell
python gerador_bat.py
```

Arquivos gerados:

| Arquivo | Finalidade |
|---|---|
| `executar_thor_arquivista.bat` | Inicia a aplicação no Windows. |
| `Thor Arquivista.lnk` | Atalho do Windows com o ícone `icons/favicon.ico`. |

O `.bat` usa `.venv\Scripts\python.exe` quando existir e recorre ao `python` do sistema quando o ambiente virtual local não estiver presente.

Opções:

| Parâmetro | Descrição |
|---|---|
| `--bat` | Nome do arquivo `.bat` gerado. |
| `--atalho` | Nome do atalho `.lnk` gerado. |
| `--sem-atalho` | Gera apenas o `.bat`, sem criar o atalho com ícone. |

---

## Boas Práticas

- Use `sha256` como algoritmo padrão para preservação.
- Sempre coloque caminhos com espaços entre aspas.
- Faça testes em cópias antes de executar comandos que movem ou apagam arquivos.
- Guarde manifestos e relatórios junto com a documentação da operação.
- Para lotes grandes, use `--progress` ou `--mostrar-progresso`; a saída é limitada a marcos de 5%.
- Em Windows, se um comando exibir caracteres incorretos, tente `chcp 65001`.

---

## Licença

Este projeto é licenciado sob a GNU Affero General Public License v3.0 (AGPLv3).

© 2025 Carlos Eduardo Carvalho Amand.
