from __future__ import annotations


TEST_METADATA = {
    "test_backup_gui.BackupGuiTests.test_preservation_backup_operational_screen_exposes_all_actions": {
        "purpose": "Validar que a tela operacional de Backup Preservacional expõe todas as ações necessárias para operar um plano já existente.",
        "preconditions": "A tela é construída com widgets simulados, sem abrir janela real, e recebe uma função falsa de enfileiramento.",
        "postconditions": "A tela contém os botões de abrir plano, validar, executar, retomar, pausar, verificar integridade, histórico e fechar; também contém os campos principais.",
    },
    "test_backup_gui.BackupGuiTests.test_backup_plan_editor_screen_exposes_json_editing_controls": {
        "purpose": "Validar que a tela separada de edição/criação de plano JSON oferece os controles esperados para manipular o arquivo.",
        "preconditions": "A tela de editor é construída com widgets simulados e sem dependência de display gráfico.",
        "postconditions": "A tela contém controles de novo, abrir, salvar, salvar como, adicionar/editar/remover origem, pré-visualizar e validar plano.",
    },
    "test_backup_gui.BackupGuiTests.test_backup_plan_editor_builds_treeview_for_sources": {
        "purpose": "Garantir que o editor de plano cria a grade de origens com as colunas usadas pelo JSON de backup.",
        "preconditions": "A tela de editor é construída usando Treeview simulado.",
        "postconditions": "Existe exatamente uma Treeview de origens com colunas name e path.",
    },
    "test_backup_plan_editor.BackupPlanEditorTests.test_collect_plan_covers_screen_options": {
        "purpose": "Validar que os campos da tela são convertidos corretamente para a estrutura JSON do plano.",
        "preconditions": "Variáveis simuladas representam nome, destino, algoritmo, opções e duas origens cadastradas.",
        "postconditions": "O plano coletado contém name, destination, sources e options com algo, ignore_hidden e follow_symlinks.",
    },
    "test_backup_plan_editor.BackupPlanEditorTests.test_apply_plan_accepts_legacy_portuguese_keys": {
        "purpose": "Garantir compatibilidade ao carregar planos com chaves legadas ou em português.",
        "preconditions": "Um dicionário de plano usa nome, destino, pastas, opcoes, raiz e flags em português.",
        "postconditions": "Os campos do editor são preenchidos corretamente e a origem é carregada na lista.",
    },
    "test_backup_plan_editor.BackupPlanEditorTests.test_validate_editor_rejects_missing_required_fields": {
        "purpose": "Verificar que a validação do editor bloqueia plano sem campos obrigatórios.",
        "preconditions": "Nome, destino e lista de origens estão vazios.",
        "postconditions": "A validação falha com mensagens para nome, destino e origem obrigatória.",
    },
    "test_backup_plan_editor.BackupPlanEditorTests.test_validate_editor_rejects_duplicate_source_names": {
        "purpose": "Verificar que o editor não aceita duas origens com o mesmo nome lógico.",
        "preconditions": "Duas origens apontam para uma pasta existente, mas compartilham o mesmo nome.",
        "postconditions": "A validação falha e informa duplicidade de nome de origem.",
    },
    "test_backup_plan_editor.BackupPlanEditorTests.test_save_plan_writes_valid_json": {
        "purpose": "Validar que o editor grava um arquivo JSON válido a partir dos campos da tela.",
        "preconditions": "Existe uma pasta de origem temporária e um caminho de saída para o plano.",
        "postconditions": "O arquivo JSON é gravado e contém o nome do backup e a lista de origens esperada.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_manifest_build_covers_prefix_hidden_and_hash_algorithm": {
        "purpose": "Validar geração de manifesto de origem com prefixo BagIt, filtro de ocultos e algoritmo alternativo.",
        "preconditions": "Uma pasta temporária contém um arquivo visível e um arquivo oculto.",
        "postconditions": "O manifesto usa prefixo data/origem, exclui o arquivo oculto e gera hash SHA-512.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_manifest_build_follow_symlinks_when_available": {
        "purpose": "Verificar a opção follow_symlinks na geração de manifesto quando o sistema permite links simbólicos.",
        "preconditions": "Uma pasta temporária contém arquivo alvo e symlink para esse arquivo.",
        "postconditions": "Sem follow_symlinks o link não entra no manifesto; com follow_symlinks ele entra.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_manifest_diff_covers_new_changed_same_and_removed": {
        "purpose": "Validar a classificação de diferenças entre manifesto da origem e manifesto do destino.",
        "preconditions": "Dois manifestos em memória têm itens novos, alterados, iguais e removidos.",
        "postconditions": "O diff retorna listas corretas para new, changed, same e removed.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_backup_runner_creates_bagit_repository_and_premis_events": {
        "purpose": "Executar backup inicial e validar criação do repositório BagIt e eventos PREMIS mínimos.",
        "preconditions": "Plano temporário aponta para uma origem com um arquivo e para um destino vazio.",
        "postconditions": "São criados bagit.txt, bag-info.txt, tagmanifest, payload em data, manifesto e eventos BACKUP_STARTED/BACKUP_COMPLETED.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_backup_runner_incremental_versions_changed_and_preserves_removed": {
        "purpose": "Validar backup incremental com versionamento de arquivo alterado e preservação de arquivo removido da origem.",
        "preconditions": "Um backup inicial já foi executado; depois um arquivo é alterado e outro removido da origem.",
        "postconditions": "A nova versão é copiada, a antiga é preservada em thor-backup/versoes e o arquivo removido continua no destino/manifesto.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_backup_runner_pause_and_resume_via_stop_checkpoint": {
        "purpose": "Validar parada segura por STOP e retomada via checkpoint.",
        "preconditions": "Antes da execução existe um arquivo STOP em thor-backup/checkpoints.",
        "postconditions": "A primeira execução termina com checkpoint PAUSED; após remover STOP, a retomada conclui com status COMPLETED.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_backup_runner_options_ignore_hidden_and_sha512": {
        "purpose": "Cobrir opções de script algo=sha512, ignore_hidden e follow_symlinks=false durante execução real do backup.",
        "preconditions": "A origem temporária contém arquivo visível e arquivo oculto; o plano usa SHA-512 e ignora ocultos.",
        "postconditions": "É criado manifest-sha512.txt, o arquivo visível entra no manifesto e o oculto fica fora.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_backup_runner_reports_failure_for_invalid_source": {
        "purpose": "Validar tratamento de erro quando o plano referencia uma origem inexistente.",
        "preconditions": "O plano aponta para uma pasta de origem que não existe.",
        "postconditions": "A execução retorna erro e o checkpoint registra status FAILED.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_backup_verify_records_fixity_event": {
        "purpose": "Validar verificação de fixidez do backup e registro do evento PREMIS específico.",
        "preconditions": "Um backup válido já foi executado e existe manifesto BagIt no destino.",
        "postconditions": "backup_verify retorna sucesso e grava evento FIXITY_CHECK com outcome success.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_validate_bag_accepts_package_created_by_build_bag": {
        "purpose": "Validar que o novo script de validação aceita um pacote BagIt criado pela funcionalidade Gerar Pacote BagIt.",
        "preconditions": "Uma pasta temporária é empacotada com build_bag usando manifest e tagmanifest SHA-256.",
        "postconditions": "validate_bag retorna sucesso e o relatório indica payload e tags íntegros, sem extras.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_validate_bag_reports_corrupt_and_extra_payload_files": {
        "purpose": "Validar que o novo script de validação detecta payload corrompido e arquivo extra em data/.",
        "preconditions": "Um BagIt válido é gerado, depois um arquivo de payload é alterado e outro é adicionado fora do manifesto.",
        "postconditions": "validate_bag retorna falha controlada e lista o arquivo com hash divergente e o arquivo extra.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_verify_fixity_report_lists_integrity_missing_and_extra_counts": {
        "purpose": "Validar que o relatório final de verificação de fixidez lista contagens e detalhes de íntegros, corrompidos, faltantes e extras.",
        "preconditions": "Uma pasta temporária contém um arquivo íntegro, um corrompido, um extra e um manifesto com um item faltante.",
        "postconditions": "verify_fixity retorna falha controlada e o relatório final contém as contagens e listas esperadas.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_verify_fixity_report_shows_zero_sections": {
        "purpose": "Garantir que o relatório final de verificação de fixidez mostra contagens zero, seções vazias e emite TXT estruturado.",
        "preconditions": "Uma pasta temporária contém apenas um arquivo íntegro e um manifesto correspondente.",
        "postconditions": "verify_fixity retorna sucesso, imprime todas as seções com contagens zero e grava seção TSV para uso por backup incremental.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_verify_fixity_large_lists_are_capped_in_stdout_and_written_to_file": {
        "purpose": "Garantir que listas grandes da verificação de fixidez não inundem o log do Worker.",
        "preconditions": "Um manifesto temporário contém mais itens ausentes do que o limite configurado para stdout.",
        "postconditions": "O stdout mostra lista truncada com aviso e o relatório TXT completo contém todos os itens na seção humana e na seção TSV.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_incremental_backup_from_fixity_copies_missing_and_corrupt_records": {
        "purpose": "Validar a nova aplicação de backup incremental baseada no relatório estruturado de fixidez.",
        "preconditions": "Um relatório TSV contém registros CORRUPT, MISSING, ERROR, EXTRA e OK; a origem contém os arquivos a repor.",
        "postconditions": "A rotina copia apenas CORRUPT, MISSING e ERROR, preserva EXTRA e gera relatório de aplicação.",
    },
    "test_preservation_backup_scripts.PreservationBackupScriptTests.test_incremental_backup_from_fixity_dry_run_does_not_copy": {
        "purpose": "Validar o modo de simulação da aplicação incremental por fixidez.",
        "preconditions": "Um relatório TSV indica um arquivo MISSING existente na origem.",
        "postconditions": "A rotina retorna sucesso, registra modo simulação e não cria o arquivo no destino.",
    },
    "test_jobstore.JobStoreTests.test_multiple_instances_can_append_logs_to_same_file_concurrently": {
        "purpose": "Validar que o JobStore suporta gravações concorrentes no mesmo arquivo JSON sem conflito no arquivo temporário.",
        "preconditions": "Várias instâncias de JobStore apontam para o mesmo arquivo temporário e registram logs em threads paralelas.",
        "postconditions": "Todos os logs esperados são gravados e o arquivo JSON permanece legível.",
    },
    "test_jobstore.JobStoreTests.test_bulk_logs_are_limited_per_job": {
        "purpose": "Validar gravação de logs em lote e contenção do tamanho do histórico por job.",
        "preconditions": "Um JobStore temporário recebe mais registros do que o limite configurado.",
        "postconditions": "Apenas os registros mais recentes até o limite configurado permanecem no JSON.",
    },
}
