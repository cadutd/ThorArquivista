$ErrorActionPreference = "Stop"

function Format-XmlReport {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    $xml = New-Object System.Xml.XmlDocument
    $xml.PreserveWhitespace = $false
    $xml.Load($Path)

    $settings = New-Object System.Xml.XmlWriterSettings
    $settings.Indent = $true
    $settings.IndentChars = "  "
    $settings.Encoding = New-Object System.Text.UTF8Encoding($false)

    $writer = [System.Xml.XmlWriter]::Create($Path, $settings)
    try {
        $xml.Save($writer)
    }
    finally {
        $writer.Close()
    }
}

function Get-TestStatus {
    param(
        [Parameter(Mandatory = $true)]
        [System.Xml.XmlElement] $TestCase
    )

    if ($TestCase.SelectSingleNode("failure")) {
        return "FALHOU"
    }
    if ($TestCase.SelectSingleNode("error")) {
        return "ERRO"
    }
    if ($TestCase.SelectSingleNode("skipped")) {
        return "IGNORADO"
    }
    return "PASSOU"
}

function Get-JUnitCases {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,
        [Parameter(Mandatory = $true)]
        [string] $Layer
    )

    $xml = New-Object System.Xml.XmlDocument
    $xml.Load($Path)

    $cases = @()
    foreach ($case in $xml.SelectNodes("//testcase")) {
        $status = Get-TestStatus $case
        $messageNode = $case.SelectSingleNode("failure|error|skipped")
        $cases += [PSCustomObject]@{
            Layer = $Layer
            Status = $status
            ClassName = $case.GetAttribute("classname")
            Name = $case.GetAttribute("name")
            Time = $case.GetAttribute("time")
            Message = if ($messageNode) { $messageNode.GetAttribute("message") } else { "" }
        }
    }
    return $cases
}

function Write-HumanReports {
    param(
        [Parameter(Mandatory = $true)]
        [string] $BackendPath,
        [Parameter(Mandatory = $true)]
        [string] $FrontendPath,
        [Parameter(Mandatory = $true)]
        [string] $OutputRoot
    )

    $allCases = @()
    $allCases += Get-JUnitCases -Path $BackendPath -Layer "Backend"
    $allCases += Get-JUnitCases -Path $FrontendPath -Layer "Frontend"

    $total = $allCases.Count
    $passed = ($allCases | Where-Object Status -eq "PASSOU").Count
    $failed = ($allCases | Where-Object Status -eq "FALHOU").Count
    $errors = ($allCases | Where-Object Status -eq "ERRO").Count
    $skipped = ($allCases | Where-Object Status -eq "IGNORADO").Count

    $summaryPath = Join-Path $OutputRoot "summary.md"
    $htmlPath = Join-Path $OutputRoot "summary.html"

    $markdown = @()
    $markdown += "# Relatorio de Testes"
    $markdown += ""
    $markdown += "| Total | Passaram | Falharam | Erros | Ignorados |"
    $markdown += "| ---: | ---: | ---: | ---: | ---: |"
    $markdown += "| $total | $passed | $failed | $errors | $skipped |"
    $markdown += ""

    foreach ($layer in @("Backend", "Frontend")) {
        $layerCases = $allCases | Where-Object Layer -eq $layer
        $markdown += "## $layer"
        $markdown += ""
        $markdown += "| Status | Teste | Classe/Arquivo | Tempo | Mensagem |"
        $markdown += "| --- | --- | --- | ---: | --- |"
        foreach ($case in $layerCases) {
            $message = ($case.Message -replace "\|", "\|" -replace "`r?`n", " ")
            $markdown += "| $($case.Status) | $($case.Name) | $($case.ClassName) | $($case.Time)s | $message |"
        }
        $markdown += ""
    }

    $markdown | Set-Content -Path $summaryPath -Encoding UTF8

    $rows = foreach ($case in $allCases) {
        $statusClass = $case.Status.ToLowerInvariant()
        "<tr class='$statusClass'><td>$($case.Layer)</td><td>$($case.Status)</td><td>$([System.Net.WebUtility]::HtmlEncode($case.Name))</td><td>$([System.Net.WebUtility]::HtmlEncode($case.ClassName))</td><td>$($case.Time)s</td><td>$([System.Net.WebUtility]::HtmlEncode($case.Message))</td></tr>"
    }
    $html = @"
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Relatorio de Testes</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; color: #172033; }
    h1 { margin-bottom: 8px; }
    .summary { display: flex; gap: 12px; margin: 16px 0 24px; flex-wrap: wrap; }
    .metric { border: 1px solid #d7dce5; border-radius: 6px; padding: 10px 14px; min-width: 110px; }
    .metric strong { display: block; font-size: 24px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d7dce5; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f3f5f8; }
    tr.passou td:nth-child(2) { color: #116329; font-weight: 700; }
    tr.falhou td:nth-child(2), tr.erro td:nth-child(2) { color: #b42318; font-weight: 700; }
    tr.ignorado td:nth-child(2) { color: #8a5a00; font-weight: 700; }
  </style>
</head>
<body>
  <h1>Relatorio de Testes</h1>
  <div class="summary">
    <div class="metric"><span>Total</span><strong>$total</strong></div>
    <div class="metric"><span>Passaram</span><strong>$passed</strong></div>
    <div class="metric"><span>Falharam</span><strong>$failed</strong></div>
    <div class="metric"><span>Erros</span><strong>$errors</strong></div>
    <div class="metric"><span>Ignorados</span><strong>$skipped</strong></div>
  </div>
  <table>
    <thead>
      <tr><th>Camada</th><th>Status</th><th>Teste</th><th>Classe/Arquivo</th><th>Tempo</th><th>Mensagem</th></tr>
    </thead>
    <tbody>
      $($rows -join "`n      ")
    </tbody>
  </table>
</body>
</html>
"@
    $html | Set-Content -Path $htmlPath -Encoding UTF8
}

$root = Split-Path -Parent $PSScriptRoot
$reportsRoot = Join-Path $root "test-reports"
$backendReports = Join-Path $reportsRoot "backend"
$frontendReports = Join-Path $reportsRoot "frontend"
$backendReportPath = Join-Path $backendReports "junit.xml"
$frontendReportPath = Join-Path $frontendReports "junit.xml"

New-Item -ItemType Directory -Force -Path $backendReports | Out-Null
New-Item -ItemType Directory -Force -Path $frontendReports | Out-Null

Push-Location $root
try {
    docker compose exec backend sh -c "mkdir -p /tmp/thor-test-reports && pytest -q --junitxml=/tmp/thor-test-reports/junit.xml"
    docker cp thor-backend:/tmp/thor-test-reports/junit.xml $backendReportPath
    Format-XmlReport $backendReportPath
}
finally {
    Pop-Location
}

Push-Location (Join-Path $root "frontend")
try {
    npm.cmd run test:functional:report
    Format-XmlReport $frontendReportPath
}
finally {
    Pop-Location
}

Write-HumanReports -BackendPath $backendReportPath -FrontendPath $frontendReportPath -OutputRoot $reportsRoot

Write-Host "Relatorios gerados em:"
Write-Host " - $backendReportPath"
Write-Host " - $frontendReportPath"
Write-Host " - $(Join-Path $reportsRoot 'summary.md')"
Write-Host " - $(Join-Path $reportsRoot 'summary.html')"
