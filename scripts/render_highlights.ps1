param([string]$ProgId = 'KWPS.Application')
$ErrorActionPreference = 'Stop'
$paperRoot = Split-Path $PSScriptRoot -Parent
$qaRoot = Join-Path $paperRoot 'qa\highlights'
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null
$inputFile = Join-Path $paperRoot 'highlights.docx'
$pdfFile = Join-Path $qaRoot 'highlights.pdf'
$wordApp = $null
$highlightDoc = $null
try {
    Write-Output "Creating $ProgId"
    $wordApp = New-Object -ComObject $ProgId
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    Write-Output 'Opening Highlights read-only'
    $highlightDoc = $wordApp.Documents.Open($inputFile, $false, $true)
    Write-Output 'Exporting PDF'
    $highlightDoc.ExportAsFixedFormat($pdfFile, 17)
}
finally {
    if ($highlightDoc) { $highlightDoc.Close(0) }
    if ($wordApp) { $wordApp.Quit() }
}
& pdftoppm -r 120 -png $pdfFile (Join-Path $qaRoot 'page')
if ($LASTEXITCODE -ne 0) { throw 'Highlights PDF rendering failed.' }
Write-Output $pdfFile
