param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [string]$QaCopy = '',
    [string]$RenderDir = '',
    [string]$BackgroundNamePattern = 'PCCS service background 48x23*'
)

$ErrorActionPreference = 'Stop'

function Release-ComObject {
    param($Object)
    if ($null -ne $Object) {
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Object)
    }
}

function Assert-Near {
    param(
        [double]$Actual,
        [double]$Expected,
        [string]$Label,
        [double]$Tolerance = 0.05
    )
    if ([Math]::Abs($Actual - $Expected) -gt $Tolerance) {
        throw "$Label expected $Expected, found $Actual"
    }
}

if (-not (Test-Path -LiteralPath $Deck)) {
    throw "Deck not found: $Deck"
}

$deckItem = Get-Item -LiteralPath $Deck
if ([string]::IsNullOrWhiteSpace($QaCopy)) {
    $QaCopy = Join-Path $deckItem.DirectoryName ($deckItem.BaseName + '_qa-duplicate.pptx')
}
if ([string]::IsNullOrWhiteSpace($RenderDir)) {
    $RenderDir = Join-Path $deckItem.DirectoryName ($deckItem.BaseName + '_qa-render')
}

$app = $null
$presentation = $null

try {
    $app = New-Object -ComObject PowerPoint.Application
    $presentation = $app.Presentations.Open($Deck, $true, $false, $false)

    Assert-Near $presentation.PageSetup.SlideWidth 720 'Slide width'
    Assert-Near $presentation.PageSetup.SlideHeight 405 'Slide height'

    $layoutNames = New-Object 'System.Collections.Generic.HashSet[string]'
    $matchingNames = New-Object 'System.Collections.Generic.HashSet[string]'
    $layoutFirstSlides = @{}
    $emptySlidePlaceholders = 0
    $boundsProblems = @()

    foreach ($slide in $presentation.Slides) {
        $layout = $slide.CustomLayout
        [void]$layoutNames.Add($layout.Name)
        [void]$matchingNames.Add($layout.MatchingName)
        if (-not $layoutFirstSlides.ContainsKey($layout.Name)) {
            $layoutFirstSlides[$layout.Name] = $slide.SlideIndex
        }

        foreach ($shape in $slide.Shapes) {
            if ($shape.Type -eq 14) {
                $text = ''
                try { $text = $shape.TextFrame.TextRange.Text.Trim() } catch {}
                if ($text.Length -eq 0) { $emptySlidePlaceholders++ }
            }

            if ($shape.Left -lt -0.1 -or $shape.Top -lt -0.1 -or
                ($shape.Left + $shape.Width) -gt 720.1 -or
                ($shape.Top + $shape.Height) -gt 405.1) {
                $boundsProblems += "Slide $($slide.SlideIndex): $($shape.Name)"
            }
        }
    }

    if ($layoutNames.Count -ne $matchingNames.Count) {
        throw "Layout Name/MatchingName identities are not unique."
    }
    if ($emptySlidePlaceholders -ne 0) {
        throw "Found $emptySlidePlaceholders empty slide placeholders."
    }
    if ($boundsProblems.Count -gt 0) {
        throw ($boundsProblems -join '; ')
    }

    foreach ($layoutName in $layoutNames) {
        $layout = $null
        foreach ($candidate in $presentation.Designs.Item(1).SlideMaster.CustomLayouts) {
            if ($candidate.Name -eq $layoutName) {
                $layout = $candidate
                break
            }
        }
        if ($null -eq $layout) { throw "Missing used layout: $layoutName" }

        $backgrounds = @()
        $tips = @()
        $placeholderCount = 0
        foreach ($shape in $layout.Shapes) {
            if ($shape.Name -like $BackgroundNamePattern) { $backgrounds += $shape }
            if ($shape.Name -eq 'PCCS logo tip overlay') { $tips += $shape }
            if ($shape.Type -eq 14) { $placeholderCount++ }
        }

        if ($backgrounds.Count -ne 1) {
            throw "Layout '$layoutName' has $($backgrounds.Count) service backgrounds."
        }
        if ($tips.Count -ne 1) {
            throw "Layout '$layoutName' has $($tips.Count) PCCS logo tip overlays."
        }
        if ($placeholderCount -ne 0) {
            throw "Layout '$layoutName' has $placeholderCount unused placeholders."
        }

        $background = $backgrounds[0]
        Assert-Near $background.Left 0 "Layout '$layoutName' background left"
        Assert-Near $background.Top 0 "Layout '$layoutName' background top"
        Assert-Near $background.Width 720 "Layout '$layoutName' background width"
        Assert-Near $background.Height 345 "Layout '$layoutName' background height"
        if ($tips[0].ZOrderPosition -ne $layout.Shapes.Count) {
            throw "Layout '$layoutName' logo-tip overlay is not topmost."
        }
    }

    New-Item -ItemType Directory -Path $RenderDir -Force | Out-Null
    $finalRenderDir = Join-Path $RenderDir 'final'
    New-Item -ItemType Directory -Path $finalRenderDir -Force | Out-Null
    foreach ($slide in $presentation.Slides) {
        $slide.Export((Join-Path $finalRenderDir ("Slide-{0}.png" -f $slide.SlideIndex)), 'PNG', 1600, 900)
    }

    $slideCount = $presentation.Slides.Count
    $presentation.Close()
    Release-ComObject $presentation
    $presentation = $null

    Copy-Item -LiteralPath $Deck -Destination $QaCopy -Force
    $presentation = $app.Presentations.Open($QaCopy, $false, $false, $false)
    $targets = @($layoutFirstSlides.Values | Sort-Object -Descending)
    foreach ($target in $targets) {
        $duplicate = $presentation.Slides.Item([int]$target).Duplicate().Item(1)
        $duplicate.Name = "QA duplicate source $target"

        $edited = $false
        foreach ($shape in $duplicate.Shapes) {
            try {
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                    $shape.TextFrame.TextRange.Text += ' '
                    $edited = $true
                    break
                }
            }
            catch {}
        }
        if (-not $edited) {
            $marker = $duplicate.Shapes.AddTextbox(1, 0, 0, 1, 1)
            $marker.Name = 'QA edit marker'
            $marker.TextFrame.TextRange.Text = 'QA'
            $marker.Visible = 0
        }
        Release-ComObject $duplicate
    }

    $presentation.Save()
    $presentation.Close()
    Release-ComObject $presentation
    $presentation = $null

    $presentation = $app.Presentations.Open($QaCopy, $true, $false, $false)
    $duplicatesFound = 0
    $duplicateRenderDir = Join-Path $RenderDir 'duplicates'
    New-Item -ItemType Directory -Path $duplicateRenderDir -Force | Out-Null
    foreach ($slide in $presentation.Slides) {
        if ($slide.Name -notlike 'QA duplicate source *') { continue }
        $duplicatesFound++

        $backgroundCount = 0
        $tipCount = 0
        foreach ($shape in $slide.CustomLayout.Shapes) {
            if ($shape.Name -like $BackgroundNamePattern) { $backgroundCount++ }
            if ($shape.Name -eq 'PCCS logo tip overlay') { $tipCount++ }
        }
        if ($backgroundCount -ne 1 -or $tipCount -ne 1) {
            throw "Duplicate '$($slide.Name)' lost its background or PCCS logo tip overlay."
        }

        $slide.Export((Join-Path $duplicateRenderDir ($slide.Name + '.png')), 'PNG', 1600, 900)
    }

    if ($duplicatesFound -ne $layoutNames.Count) {
        throw "Expected $($layoutNames.Count) duplicate layouts, found $duplicatesFound."
    }

    [pscustomobject]@{
        Slides = $slideCount
        UniqueLayouts = $layoutNames.Count
        UniqueMatchingNames = $matchingNames.Count
        BackgroundGeometry = 'PASS (0,0,720,345)'
        EmptySlidePlaceholders = $emptySlidePlaceholders
        ShapeBounds = 'PASS'
        FinalRenders = $slideCount
        DuplicateEditSaveReopen = "PASS ($duplicatesFound layouts)"
        DuplicateRenders = $duplicatesFound
    }
}
finally {
    if ($presentation) { try { $presentation.Close() } catch {} }
    if ($app) { try { $app.Quit() } catch {} }
    Release-ComObject $presentation
    Release-ComObject $app
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
