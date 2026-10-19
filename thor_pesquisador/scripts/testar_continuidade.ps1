[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$compose = Join-Path $PSScriptRoot '../docker-compose.test.yml'

function Invoke-TestDocker {
    param([string[]]$Arguments)
    $output = & docker compose -f $compose @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falha no comando Docker de continuidade." }
    return $output
}

$source = Invoke-TestDocker -Arguments @('exec','-T','backend','python','-c',
    "import json; from app.core.config import settings; assert settings.app_env == 'test'; assert settings.database_url.rsplit('/',1)[-1].endswith('_test'); assert settings.mongodb_database.endswith('_test'); print(json.dumps(dict(sql=settings.database_url.rsplit('/',1)[-1],mongo=settings.mongodb_database)))")
$databases = ($source -join '') | ConvertFrom-Json
$restore = 'fase6_restore_' + [Guid]::NewGuid().ToString('N') + '_test'
if ($restore -notmatch '^fase6_restore_[a-f0-9]{32}_test$' -or $restore -eq $databases.sql -or $restore -eq $databases.mongo) {
    throw 'Destino de restauracao inseguro.'
}
$dump = '/tmp/' + $restore + '.dump'
$archive = '/tmp/' + $restore + '.archive'
$sqlCreated = $false
$mongoCreated = $false
$watch = [System.Diagnostics.Stopwatch]::StartNew()
try {
    Invoke-TestDocker -Arguments @('exec','-T','postgres','pg_dump','-U','thor','-Fc','-f',$dump,$databases.sql) | Out-Null
    Invoke-TestDocker -Arguments @('exec','-T','postgres','createdb','-U','thor',$restore) | Out-Null
    $sqlCreated = $true
    Invoke-TestDocker -Arguments @('exec','-T','postgres','pg_restore','-U','thor','--exit-on-error','--no-owner','-d',$restore,$dump) | Out-Null
    $query = "SELECT json_build_object('usuarios',(SELECT count(*) FROM usuarios),'sessoes',(SELECT count(*) FROM sessoes),'eventos',(SELECT count(*) FROM auditoria_geral),'configuracao',(SELECT md5(row_to_json(t)::text) FROM configuracao_portal t),'migration',(SELECT version_num FROM alembic_version));"
    $before = Invoke-TestDocker -Arguments @('exec','-T','postgres','psql','-U','thor','-d',$databases.sql,'-t','-A','-c',$query)
    $after = Invoke-TestDocker -Arguments @('exec','-T','postgres','psql','-U','thor','-d',$restore,'-t','-A','-c',$query)
    if (($before -join '').Trim() -ne ($after -join '').Trim()) { throw 'Divergencia apos restaurar PostgreSQL.' }
    Invoke-TestDocker -Arguments @('exec','-T','mongo','mongodump','--db',$databases.mongo,('--archive='+$archive),'--gzip') | Out-Null
    $mongoCreated = $true
    Invoke-TestDocker -Arguments @('exec','-T','mongo','mongorestore',('--archive='+$archive),'--gzip',
        '--nsFrom',($databases.mongo+'.*'),'--nsTo',($restore+'.*')) | Out-Null
    $mongoQuery = ".getCollectionNames().sort().map(n=>n+':'+d.getCollection(n).countDocuments({})).join('|')"
    $beforeMongo = Invoke-TestDocker -Arguments @('exec','-T','mongo','mongosh','--quiet','--eval',
        ("const d=db.getSiblingDB('"+$databases.mongo+"');d"+$mongoQuery))
    $afterMongo = Invoke-TestDocker -Arguments @('exec','-T','mongo','mongosh','--quiet','--eval',
        ("const d=db.getSiblingDB('"+$restore+"');d"+$mongoQuery))
    if (($beforeMongo -join '').Trim() -ne ($afterMongo -join '').Trim()) { throw 'Divergencia apos restaurar MongoDB.' }
    $sha = Invoke-TestDocker -Arguments @('exec','-T','postgres','sha256sum',$dump)
    [PSCustomObject]@{resultado='PASS';postgres=(($after -join '').Trim() | ConvertFrom-Json);
        mongo=($afterMongo -join '').Trim();dump_sha256=($sha -join '').Split(' ')[0];segundos=[Math]::Round($watch.Elapsed.TotalSeconds,2)} | ConvertTo-Json -Depth 4
}
finally {
    # Only the generated destinations are removed; source databases are never modified.
    if ($restore -notmatch '^fase6_restore_[a-f0-9]{32}_test$') { throw 'Destino alterado; limpeza bloqueada.' }
    if ($sqlCreated) { Invoke-TestDocker -Arguments @('exec','-T','postgres','dropdb','-U','thor',$restore) | Out-Null }
    if ($mongoCreated) { Invoke-TestDocker -Arguments @('exec','-T','mongo','mongosh','--quiet','--eval',("db.getSiblingDB('"+$restore+"').dropDatabase()")) | Out-Null }
    Invoke-TestDocker -Arguments @('exec','-T','postgres','rm','-f','--',$dump) | Out-Null
    Invoke-TestDocker -Arguments @('exec','-T','mongo','rm','-f','--',$archive) | Out-Null
}
