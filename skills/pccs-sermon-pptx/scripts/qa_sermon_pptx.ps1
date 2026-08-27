param(
    [Parameter(Mandatory = $true)][string]$SourceDeck,
    [Parameter(Mandatory = $true)][string]$CandidateDeck,
    [string]$LayoutSpecPath = '',
    [string]$ExpectedFont = 'STKaiti',
    [switch]$RequireShadow
)

$ErrorActionPreference = 'Stop'
$script:Failures = [System.Collections.Generic.List[string]]::new()
$tolerance = 0.35

function Release-ComObject($Object) {
    if ($null -ne $Object) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Object) }
}

function Add-Failure([string]$Message) {
    $script:Failures.Add($Message)
}

function Near([double]$Actual, [double]$Expected, [double]$Tolerance = $script:tolerance) {
    return [Math]::Abs($Actual - $Expected) -le $Tolerance
}

function Safe-Value([scriptblock]$Expression, $Fallback = $null) {
    try { return (& $Expression) } catch { return $Fallback }
}

function Get-ShapeById($Slide, [int]$Id) {
    foreach ($shape in @($Slide.Shapes)) {
        if ($shape.Id -eq $Id) { return $shape }
    }
    return $null
}

function Get-Text($Shape) {
    try {
        if ($Shape.HasTextFrame -eq -1 -and $Shape.TextFrame.HasText -eq -1) {
            return [string]$Shape.TextFrame2.TextRange.Text
        }
    } catch {}
    return $null
}

function Is-Blank([string]$Text) {
    return (($Text -replace "[\r\n\v]", '').Trim().Length -eq 0)
}

function Sequence-Signature($Sequence, [string]$Prefix) {
    $parts = [System.Collections.Generic.List[string]]::new()
    $parts.Add("$Prefix-count=$($Sequence.Count)")
    for ($i = 1; $i -le $Sequence.Count; $i++) {
        $effect = $Sequence.Item($i)
        $shapeId = Safe-Value { $effect.Shape.Id } -1
        $duration = Safe-Value { [double]$effect.Timing.Duration } 0
        $delay = Safe-Value { [double]$effect.Timing.TriggerDelayTime } 0
        $parts.Add(("{0}:{1}:{2}:{3}:{4:F4}:{5:F4}" -f $Prefix, $shapeId, $effect.EffectType, $effect.Timing.TriggerType, $duration, $delay))
    }
    return @($parts)
}

function Animation-Signature($Slide) {
    $parts = [System.Collections.Generic.List[string]]::new()
    foreach ($part in (Sequence-Signature $Slide.TimeLine.MainSequence 'main')) { $parts.Add($part) }
    $interactive = $Slide.TimeLine.InteractiveSequences
    $parts.Add("interactive-count=$($interactive.Count)")
    for ($i = 1; $i -le $interactive.Count; $i++) {
        foreach ($part in (Sequence-Signature $interactive.Item($i) "interactive-$i")) { $parts.Add($part) }
    }
    return ($parts -join '|')
}

function Transition-Signature($Slide) {
    $transition = $Slide.SlideShowTransition
    return ("{0}:{1}:{2}:{3:F4}:{4}" -f $transition.EntryEffect, $transition.AdvanceOnClick, $transition.AdvanceOnTime, $transition.AdvanceTime, $transition.Speed)
}

function Check-FontAndShadow($Slide) {
    foreach ($shape in @($Slide.Shapes)) {
        $text = Get-Text $shape
        if ($null -eq $text -or $text.Length -eq 0) { continue }

        if (-not [string]::IsNullOrWhiteSpace($ExpectedFont)) {
            $fontNames = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
            $runs = $shape.TextFrame2.TextRange.Runs()
            for ($r = 1; $r -le $runs.Count; $r++) {
                $run = $shape.TextFrame2.TextRange.Runs($r, 1)
                if (-not (Is-Blank ([string]$run.Text))) { [void]$fontNames.Add([string]$run.Font.Name) }
            }
            foreach ($font in $fontNames) {
                if ($font -ne $ExpectedFont) {
                    Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) font '$font'; expected '$ExpectedFont'"
                }
            }
        }

        if ($RequireShadow) {
            $shadow = $shape.TextFrame2.TextRange.Font.Shadow
            if ($shadow.Visible -ne -1) {
                Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) text shadow is not visible"
            } else {
                if ($shadow.ForeColor.RGB -ne 0) { Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) shadow is not black" }
                if (-not (Near ([double]$shadow.Transparency) 0.28 0.02)) { Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) shadow transparency differs" }
                if (-not (Near ([double]$shadow.Blur) 4 0.2)) { Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) shadow blur differs" }
                if (-not (Near ([double]$shadow.OffsetX) 1.5 0.2) -or -not (Near ([double]$shadow.OffsetY) 1.5 0.2)) {
                    Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) shadow offset differs"
                }
            }
        }
    }
}

function Check-TextBounds($Slide, [double]$SlideWidth, [double]$SlideHeight) {
    foreach ($shape in @($Slide.Shapes)) {
        $text = Get-Text $shape
        if ($null -eq $text -or $text.Length -eq 0) { continue }
        $range = $shape.TextFrame2.TextRange
        $boundHeight = [double]$range.BoundHeight
        $boundTop = Safe-Value { [double]$range.BoundTop } ([double]$shape.Top)
        $maxVisibleWidth = 0.0
        $maxRight = 0.0
        $lines = $range.Lines()
        for ($i = 1; $i -le $lines.Count; $i++) {
            $line = $range.Lines($i, 1)
            $raw = [string]$line.Text
            $visible = $raw.TrimEnd([char[]]@(' ', "`r", "`n", [char]11))
            $visibleWidth = if ($visible.Length -gt 0) { [double]$line.Characters(1, $visible.Length).BoundWidth } else { 0.0 }
            $lineLeft = Safe-Value { [double]$line.BoundLeft } ([double]$shape.Left)
            if ($visibleWidth -gt $maxVisibleWidth) { $maxVisibleWidth = $visibleWidth }
            if (($lineLeft + $visibleWidth) -gt $maxRight) { $maxRight = $lineLeft + $visibleWidth }
        }
        if ($boundHeight -gt ([double]$shape.Height + 2)) {
            Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) text height exceeds its box"
        }
        if ($maxVisibleWidth -gt ([double]$shape.Width + 2)) {
            Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) visible line width exceeds its box"
        }
        if ($maxRight -gt ($SlideWidth - 2)) {
            Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) visible text exceeds the right canvas edge"
        }
        if (($boundTop + $boundHeight) -gt ($SlideHeight - 2)) {
            Add-Failure "Slide $($Slide.SlideIndex) shape $($shape.Id) visible text exceeds the bottom canvas edge"
        }
    }
}

function Check-LayoutSpec($Presentation, $Spec) {
    if (-not (Near ([double]$Presentation.PageSetup.SlideWidth) ([double]$Spec.slideWidth))) {
        Add-Failure "Slide width differs from layout spec"
    }
    if (-not (Near ([double]$Presentation.PageSetup.SlideHeight) ([double]$Spec.slideHeight))) {
        Add-Failure "Slide height differs from layout spec"
    }

    foreach ($group in @($Spec.groups)) {
        foreach ($slideNumber in @($group.slides)) {
            if ([int]$slideNumber -lt 1 -or [int]$slideNumber -gt $Presentation.Slides.Count) {
                Add-Failure "Layout group '$($group.name)' references missing slide $slideNumber"
                continue
            }
            $slide = $Presentation.Slides.Item([int]$slideNumber)
            $shape = Get-ShapeById $slide ([int]$group.shapeId)
            if ($null -eq $shape) {
                Add-Failure "Slide $slideNumber missing layout shape ID $($group.shapeId) for group '$($group.name)'"
                continue
            }
            foreach ($field in @('left','top','width','height')) {
                $actual = [double]$shape.($field.Substring(0,1).ToUpperInvariant() + $field.Substring(1))
                $expected = [double]$group.$field
                if (-not (Near $actual $expected)) {
                    Add-Failure "Slide $slideNumber shape $($shape.Id) $field=$([Math]::Round($actual,2)); expected $expected"
                }
            }
            if ($shape.TextFrame2.VerticalAnchor -ne [int]$group.verticalAnchor) {
                Add-Failure "Slide $slideNumber shape $($shape.Id) vertical anchor differs"
            }
            if ($shape.TextFrame2.WordWrap -ne [int]$group.wordWrap) {
                Add-Failure "Slide $slideNumber shape $($shape.Id) word wrap differs"
            }
            foreach ($margin in @('MarginLeft','MarginRight','MarginTop','MarginBottom')) {
                if (-not (Near ([double]$shape.TextFrame2.$margin) 0 0.1)) {
                    Add-Failure "Slide $slideNumber shape $($shape.Id) $margin is not zero"
                }
            }

            $range = $shape.TextFrame2.TextRange
            $hasVerseSpacing = $null -ne $group.PSObject.Properties['verseStartSpaceBefore']
            $seenVerse = $false
            for ($p = 1; $p -le $range.Paragraphs().Count; $p++) {
                $paragraph = $range.Paragraphs($p, 1)
                $blank = Is-Blank ([string]$paragraph.Text)
                $size = if ($p -eq 1) { [double]$group.titleSize } elseif ($blank) { [double]$group.blankSize } else { [double]$group.bodySize }
                $spaceAfter = if ($p -eq 1) { [double]$group.titleSpaceAfter } elseif ($blank) { [double]$group.blankSpaceAfter } else { [double]$group.bodySpaceAfter }
                if (-not (Near ([double]$paragraph.Font.Size) $size 0.2)) {
                    Add-Failure "Slide $slideNumber shape $($shape.Id) paragraph $p size differs"
                }
                if (-not (Near ([double]$paragraph.ParagraphFormat.SpaceAfter) $spaceAfter 0.2)) {
                    Add-Failure "Slide $slideNumber shape $($shape.Id) paragraph $p spacing differs"
                }
                if ($hasVerseSpacing -and $p -gt 1) {
                    $clean = ([string]$paragraph.Text -replace "[\r\n\v]", '').Trim()
                    $expectedBefore = 0.0
                    if (-not $blank) {
                        if ($clean -match '^\d+') {
                            $expectedBefore = if ($seenVerse) {
                                [double]$group.verseStartSpaceBefore
                            } elseif ($null -ne $group.PSObject.Properties['firstVerseSpaceBefore']) {
                                [double]$group.firstVerseSpaceBefore
                            } else {
                                0.0
                            }
                            $seenVerse = $true
                        } elseif ($null -ne $group.PSObject.Properties['continuationSpaceBefore']) {
                            $expectedBefore = [double]$group.continuationSpaceBefore
                        }
                    }
                    if (-not (Near ([double]$paragraph.ParagraphFormat.SpaceBefore) $expectedBefore 0.2)) {
                        Add-Failure "Slide $slideNumber shape $($shape.Id) paragraph $p verse spacing before differs"
                    }
                    if ($paragraph.ParagraphFormat.LineRuleBefore -ne 0 -or $paragraph.ParagraphFormat.LineRuleAfter -ne 0) {
                        Add-Failure "Slide $slideNumber shape $($shape.Id) paragraph $p verse spacing is not measured in points"
                    }
                }
            }
        }
    }
}

if (-not (Test-Path -LiteralPath $SourceDeck -PathType Leaf)) { throw "Source deck not found: $SourceDeck" }
if (-not (Test-Path -LiteralPath $CandidateDeck -PathType Leaf)) { throw "Candidate deck not found: $CandidateDeck" }
if (-not [string]::IsNullOrWhiteSpace($LayoutSpecPath) -and -not (Test-Path -LiteralPath $LayoutSpecPath -PathType Leaf)) {
    throw "Layout spec not found: $LayoutSpecPath"
}

$layoutSpec = if ([string]::IsNullOrWhiteSpace($LayoutSpecPath)) { $null } else { Get-Content -LiteralPath $LayoutSpecPath -Raw | ConvertFrom-Json }
$ppt = $null
$source = $null
$candidate = $null
$validatedSlides = 0
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $source = $ppt.Presentations.Open($SourceDeck, $true, $false, $false)
    $candidate = $ppt.Presentations.Open($CandidateDeck, $true, $false, $false)
    $validatedSlides = $candidate.Slides.Count

    if ($source.Slides.Count -ne $candidate.Slides.Count) {
        Add-Failure "Slide count changed: source=$($source.Slides.Count), candidate=$($candidate.Slides.Count)"
    }
    if (-not (Near ([double]$source.PageSetup.SlideWidth) ([double]$candidate.PageSetup.SlideWidth)) -or
        -not (Near ([double]$source.PageSetup.SlideHeight) ([double]$candidate.PageSetup.SlideHeight))) {
        Add-Failure "Slide size changed"
    }

    $count = [Math]::Min($source.Slides.Count, $candidate.Slides.Count)
    for ($s = 1; $s -le $count; $s++) {
        $srcSlide = $source.Slides.Item($s)
        $dstSlide = $candidate.Slides.Item($s)
        if ($srcSlide.Shapes.Count -ne $dstSlide.Shapes.Count) {
            Add-Failure "Slide $s shape count changed"
        }
        foreach ($srcShape in @($srcSlide.Shapes)) {
            $dstShape = Get-ShapeById $dstSlide $srcShape.Id
            if ($null -eq $dstShape) {
                Add-Failure "Slide $s missing source shape ID $($srcShape.Id)"
                continue
            }
            if ($srcShape.Type -ne $dstShape.Type) { Add-Failure "Slide $s shape $($srcShape.Id) type changed" }
            if ((Get-Text $srcShape) -cne (Get-Text $dstShape)) {
                Add-Failure "Slide $s shape $($srcShape.Id) text or hard line breaks changed"
            }
        }
        if ((Animation-Signature $srcSlide) -cne (Animation-Signature $dstSlide)) {
            Add-Failure "Slide $s animations changed"
        }
        if ((Transition-Signature $srcSlide) -cne (Transition-Signature $dstSlide)) {
            Add-Failure "Slide $s transitions changed"
        }
        Check-FontAndShadow $dstSlide
        Check-TextBounds $dstSlide ([double]$candidate.PageSetup.SlideWidth) ([double]$candidate.PageSetup.SlideHeight)
    }

    if ($null -ne $layoutSpec) { Check-LayoutSpec $candidate $layoutSpec }
}
finally {
    if ($null -ne $candidate) { try { $candidate.Close() } catch {}; Release-ComObject $candidate }
    if ($null -ne $source) { try { $source.Close() } catch {}; Release-ComObject $source }
    if ($null -ne $ppt) { try { $ppt.Quit() } catch {}; Release-ComObject $ppt }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

if ($script:Failures.Count -gt 0) {
    Write-Host "VALIDATION FAILED ($($script:Failures.Count) issue(s))"
    $script:Failures | ForEach-Object { Write-Host " - $_" }
    exit 1
}

Write-Host 'VALIDATION PASSED'
[pscustomobject]@{
    Slides = $validatedSlides
    Font = $ExpectedFont
    ShadowRequired = [bool]$RequireShadow
    LayoutSpec = if ([string]::IsNullOrWhiteSpace($LayoutSpecPath)) { 'not supplied' } else { $LayoutSpecPath }
}
exit 0
