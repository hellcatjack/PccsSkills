param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [string]$QaCopy = '',
    [string]$RenderDir = '',
    [string]$BackgroundNamePattern = 'PCCS service background 48x23*',
    [string]$ProjectJson = ''
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'qa_pccs_service_helpers.ps1')

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
$runId = [Guid]::NewGuid().ToString('N')
if ([string]::IsNullOrWhiteSpace($QaCopy)) {
    $QaCopy = Join-Path $deckItem.DirectoryName ($deckItem.BaseName + '_qa-' + $runId + '.pptx')
}
if ([string]::IsNullOrWhiteSpace($RenderDir)) {
    $RenderDir = Join-Path $deckItem.DirectoryName ($deckItem.BaseName + '_qa-render-' + $runId)
}
Assert-PccsNewOutputPath $deckItem.FullName $QaCopy
Assert-PccsNewOutputPath $deckItem.FullName $RenderDir
$QaCopy = [IO.Path]::GetFullPath($QaCopy)
$RenderDir = [IO.Path]::GetFullPath($RenderDir)
$projectPlan = if ($ProjectJson) { Get-Content -LiteralPath $ProjectJson -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
# Open only our own new copy. Even read-only opening the user's existing deck can
# attach to a window the user already has open.
[IO.File]::Copy($deckItem.FullName, $QaCopy, $false)

$app = $null
$presentation = $null

try {
    $app = New-Object -ComObject PowerPoint.Application
    $presentation = $app.Presentations.Open($QaCopy, $false, $false, $false)

    Assert-Near $presentation.PageSetup.SlideWidth 720 'Slide width'
    Assert-Near $presentation.PageSetup.SlideHeight 405 'Slide height'

    $layouts = @{}
    $serviceMap = if ($projectPlan) { Get-PccsServiceSlideMap $projectPlan $presentation.Slides.Count } else { @{} }
    $consumedServiceSlides = New-Object 'System.Collections.Generic.HashSet[int]'
    $scriptureBodyChecks = 0
    $emptySlidePlaceholders = 0
    $boundsProblems = @()

    foreach ($slide in $presentation.Slides) {
        Register-PccsLayout $layouts $slide

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
        if ($serviceMap.ContainsKey([int]$slide.SlideIndex)) {
            $planned = $serviceMap[[int]$slide.SlideIndex]
            if ($planned.type -eq 'scripture') {
                Assert-PccsScriptureBody $slide $planned
                $scriptureBodyChecks++
            }
            [void]$consumedServiceSlides.Add([int]$slide.SlideIndex)
        }
    }
    Assert-PccsConsumedServiceSlides $serviceMap $consumedServiceSlides

    if ($emptySlidePlaceholders -ne 0) {
        throw "Found $emptySlidePlaceholders empty slide placeholders."
    }
    if ($boundsProblems.Count -gt 0) {
        throw ($boundsProblems -join '; ')
    }

    foreach ($entry in $layouts.Values) {
        $layout = $entry.Layout
        $layoutName = $layout.Name

        $backgrounds = @()
        $tips = @()
        $placeholderCount = 0
        foreach ($shape in $layout.Shapes) {
            if ($shape.Name -like $BackgroundNamePattern) { $backgrounds += $shape }
            if ($shape.Name -eq 'PCCS logo tip overlay') { $tips += $shape }
            if ($shape.Type -eq 14) {
                $placeholderText = ''
                try { $placeholderText = $shape.TextFrame.TextRange.Text.Trim() } catch {}
                if ($placeholderText.Length -eq 0) { $placeholderCount++ }
            }
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
    $targets = @($layouts.Values | ForEach-Object { $_.SourceSlide } | Sort-Object -Descending)
    $expectedDuplicates = @{}
    foreach ($target in $targets) {
        $duplicate = $presentation.Slides.Item([int]$target).Duplicate().Item(1)
        $duplicate.Name = "QA duplicate source $target"

        $before = Get-PccsSlideTextState $duplicate
        Set-PccsVisibleQaEdit $duplicate
        $after = Get-PccsSlideTextState $duplicate
        if ($before -cne $after) { throw "QA visible edit changed typography or layout: source $target" }
        $expectedDuplicates[$duplicate.Name] = Get-PccsSlideTextState $duplicate -IncludeText
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
        $actualState = Get-PccsSlideTextState $slide -IncludeText
        if ($actualState -cne $expectedDuplicates[$slide.Name]) {
            throw "Duplicate '$($slide.Name)' changed visible text, fonts, geometry or layout after reopen."
        }

        $slide.Export((Join-Path $duplicateRenderDir ($slide.Name + '.png')), 'PNG', 1600, 900)
    }

    if ($duplicatesFound -ne $layouts.Count) {
        throw "Expected $($layouts.Count) duplicate layouts, found $duplicatesFound."
    }

    [pscustomobject]@{
        Slides = $slideCount
        UniqueLayouts = $layouts.Count
        UniqueMatchingNames = $layouts.Count
        BackgroundGeometry = 'PASS (0,0,720,345)'
        EmptySlidePlaceholders = $emptySlidePlaceholders
        ShapeBounds = 'PASS'
        FinalRenders = $slideCount
        DuplicateEditSaveReopen = "PASS ($duplicatesFound layouts)"
        DuplicateRenders = $duplicatesFound
        ScriptureBodyChecks = $(if ($projectPlan) { "PASS ($scriptureBodyChecks declared scripture bodies)" } else { 'Not requested: supply -ProjectJson' })
        ServiceMappedSlides = $consumedServiceSlides.Count
        QaCopy = $QaCopy
    }
}
finally {
    if ($presentation) {
        # On failure, discard unsaved edits in our QA copy without a save prompt.
        try { $presentation.Saved = -1; $presentation.Close() } catch {}
    }
    # PowerPoint may share one application across automation and user windows.
    # Close only the presentation opened above; never quit the application.
    Release-ComObject $presentation
    Release-ComObject $app
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
