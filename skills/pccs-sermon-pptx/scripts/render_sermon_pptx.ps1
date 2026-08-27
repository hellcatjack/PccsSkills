param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [Parameter(Mandatory = $true)][string]$RenderDir,
    [int]$Width = 1600,
    [int]$Height = 900
)

$ErrorActionPreference = 'Stop'

function Release-ComObject($Object) {
    if ($null -ne $Object) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Object) }
}

if (-not (Test-Path -LiteralPath $Deck -PathType Leaf)) { throw "Deck not found: $Deck" }
if (-not (Test-Path -LiteralPath $RenderDir -PathType Container)) {
    New-Item -ItemType Directory -Path $RenderDir | Out-Null
}
if ((Get-ChildItem -LiteralPath $RenderDir -Filter '*.png' -File).Count -gt 0) {
    throw "Render directory already contains PNG files; use a new empty directory: $RenderDir"
}

$ppt = $null
$presentation = $null
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $presentation = $ppt.Presentations.Open($Deck, $true, $false, $false)
    foreach ($slide in @($presentation.Slides)) {
        $path = Join-Path $RenderDir ('Slide-{0:D3}.png' -f $slide.SlideIndex)
        $slide.Export($path, 'PNG', $Width, $Height)
    }
    [pscustomobject]@{
        Deck = (Get-Item -LiteralPath $Deck).FullName
        Slides = $presentation.Slides.Count
        RenderDir = (Get-Item -LiteralPath $RenderDir).FullName
        Width = $Width
        Height = $Height
    }
}
finally {
    if ($null -ne $presentation) { try { $presentation.Close() } catch {}; Release-ComObject $presentation }
    if ($null -ne $ppt) { try { $ppt.Quit() } catch {}; Release-ComObject $ppt }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
