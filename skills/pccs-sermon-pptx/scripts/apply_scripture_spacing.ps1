param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [Parameter(Mandatory = $true)][string]$LayoutSpecPath
)

$ErrorActionPreference = 'Stop'

function Release-ComObject($Object) {
    if ($null -ne $Object) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Object) } catch {}
    }
}

function Get-ShapeById($Slide, [int]$ShapeId) {
    foreach ($shape in @($Slide.Shapes)) {
        if ($shape.Id -eq $ShapeId) { return $shape }
        Release-ComObject $shape
    }
    throw "Slide $($Slide.SlideIndex) shape ID $ShapeId not found."
}

function Has-Property($Object, [string]$Name) {
    return $null -ne $Object.PSObject.Properties[$Name]
}

if (-not (Test-Path -LiteralPath $Deck -PathType Leaf)) { throw "Deck not found: $Deck" }
if (-not (Test-Path -LiteralPath $LayoutSpecPath -PathType Leaf)) { throw "Layout spec not found: $LayoutSpecPath" }

$resolvedDeck = (Resolve-Path -LiteralPath $Deck).Path
$spec = Get-Content -LiteralPath $LayoutSpecPath -Raw | ConvertFrom-Json
$groups = @($spec.groups | Where-Object { Has-Property $_ 'verseStartSpaceBefore' })
if ($groups.Count -eq 0) { throw 'The layout spec has no groups with verseStartSpaceBefore.' }

$ppt = $null
$presentation = $null
$updatedSlides = [System.Collections.Generic.HashSet[int]]::new()
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $ppt.DisplayAlerts = 0
    $presentation = $ppt.Presentations.Open($resolvedDeck, $false, $false, $false)

    foreach ($group in $groups) {
        $verseGap = [double]$group.verseStartSpaceBefore
        $firstVerseGap = if (Has-Property $group 'firstVerseSpaceBefore') { [double]$group.firstVerseSpaceBefore } else { 0.0 }
        $continuationGap = if (Has-Property $group 'continuationSpaceBefore') { [double]$group.continuationSpaceBefore } else { 0.0 }
        $bodyAfter = [double]$group.bodySpaceAfter
        $blankAfter = [double]$group.blankSpaceAfter

        foreach ($slideNumber in @($group.slides)) {
            $slide = $presentation.Slides.Item([int]$slideNumber)
            $shape = Get-ShapeById $slide ([int]$group.shapeId)
            $range = $shape.TextFrame2.TextRange
            $seenVerse = $false

            for ($index = 2; $index -le $range.Paragraphs().Count; $index++) {
                $paragraph = $range.Paragraphs($index, 1)
                $clean = ([string]$paragraph.Text -replace "[\r\n\v]", '').Trim()
                $paragraph.ParagraphFormat.LineRuleBefore = 0
                $paragraph.ParagraphFormat.LineRuleAfter = 0

                if ([string]::IsNullOrWhiteSpace($clean)) {
                    $paragraph.ParagraphFormat.SpaceBefore = 0
                    $paragraph.ParagraphFormat.SpaceAfter = $blankAfter
                    continue
                }

                if ($clean -match '^\d+') {
                    $paragraph.ParagraphFormat.SpaceBefore = if ($seenVerse) { $verseGap } else { $firstVerseGap }
                    $seenVerse = $true
                }
                else {
                    $paragraph.ParagraphFormat.SpaceBefore = $continuationGap
                }
                $paragraph.ParagraphFormat.SpaceAfter = $bodyAfter
            }
            [void]$updatedSlides.Add([int]$slideNumber)
            Release-ComObject $shape
            Release-ComObject $slide
        }
    }
    $presentation.Save()
}
finally {
    if ($null -ne $presentation) { try { $presentation.Close() } catch {}; Release-ComObject $presentation }
    if ($null -ne $ppt) { try { $ppt.Quit() } catch {}; Release-ComObject $ppt }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

[pscustomobject]@{
    Deck = $resolvedDeck
    Groups = $groups.Count
    Slides = @($updatedSlides | Sort-Object)
    SpacingUnit = 'points'
}
