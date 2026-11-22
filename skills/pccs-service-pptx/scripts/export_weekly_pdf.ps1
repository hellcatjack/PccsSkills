param(
    [Parameter(Mandatory=$true)][string]$Pptx,
    [Parameter(Mandatory=$true)][string]$Pdf
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $Pptx).Path
$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Pdf)
if ([IO.Path]::GetExtension($output) -ine '.pdf' -or (Test-Path -LiteralPath $output)) {
    throw 'Choose a new path ending in .pdf.'
}
$app = New-Object -ComObject PowerPoint.Application
$deck = $null
try {
    $deck = $app.Presentations.Open($source,-1,0,0)
    $deck.SaveCopyAs($output,32)
    if ((Get-Item -LiteralPath $output).Length -le 0) { throw 'PowerPoint produced an empty PDF.' }
    Get-Item -LiteralPath $output | Select-Object FullName,Length
} finally {
    if ($deck) { $deck.Close() }
    if ($app.Presentations.Count -eq 0) { $app.Quit() }
}
