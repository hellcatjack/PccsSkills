param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [string]$OutputJson = ''
)

$ErrorActionPreference = 'Stop'

function Release-ComObject($Object) {
    if ($null -ne $Object) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Object) }
}

function Safe-Value([scriptblock]$Expression, $Fallback = $null) {
    try { return (& $Expression) } catch { return $Fallback }
}

if (-not (Test-Path -LiteralPath $Deck -PathType Leaf)) { throw "Deck not found: $Deck" }

$ppt = $null
$presentation = $null
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $presentation = $ppt.Presentations.Open($Deck, $true, $false, $false)
    $slideInventory = [System.Collections.Generic.List[object]]::new()

    foreach ($slide in @($presentation.Slides)) {
        $shapeInventory = [System.Collections.Generic.List[object]]::new()
        foreach ($shape in @($slide.Shapes)) {
            $hasText = $false
            $text = $null
            $paragraphs = @()
            $fontName = $null
            $verticalAnchor = $null
            $wordWrap = $null
            $shadowVisible = $null
            try {
                $hasText = ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1)
                if ($hasText) {
                    $range = $shape.TextFrame2.TextRange
                    $text = [string]$range.Text
                    $fontName = [string]$range.Font.Name
                    $verticalAnchor = $shape.TextFrame2.VerticalAnchor
                    $wordWrap = $shape.TextFrame2.WordWrap
                    $shadowVisible = $range.Font.Shadow.Visible
                    $items = [System.Collections.Generic.List[object]]::new()
                    for ($p = 1; $p -le $range.Paragraphs().Count; $p++) {
                        $paragraph = $range.Paragraphs($p, 1)
                        $items.Add([pscustomobject]@{
                            Index = $p
                            Text = [string]$paragraph.Text
                            Font = [string]$paragraph.Font.Name
                            Size = Safe-Value { [double]$paragraph.Font.Size }
                            LineRuleBefore = Safe-Value { [int]$paragraph.ParagraphFormat.LineRuleBefore }
                            LineRuleAfter = Safe-Value { [int]$paragraph.ParagraphFormat.LineRuleAfter }
                            SpaceBefore = Safe-Value { [double]$paragraph.ParagraphFormat.SpaceBefore }
                            SpaceAfter = Safe-Value { [double]$paragraph.ParagraphFormat.SpaceAfter }
                        })
                    }
                    $paragraphs = @($items)
                }
            } catch {}

            $shapeInventory.Add([pscustomobject]@{
                Id = $shape.Id
                Name = $shape.Name
                Type = $shape.Type
                Left = [double]$shape.Left
                Top = [double]$shape.Top
                Width = [double]$shape.Width
                Height = [double]$shape.Height
                ZOrder = $shape.ZOrderPosition
                HasText = $hasText
                Text = $text
                Font = $fontName
                VerticalAnchor = $verticalAnchor
                WordWrap = $wordWrap
                ShadowVisible = $shadowVisible
                Paragraphs = $paragraphs
            })
        }

        $effects = [System.Collections.Generic.List[object]]::new()
        $sequence = $slide.TimeLine.MainSequence
        for ($e = 1; $e -le $sequence.Count; $e++) {
            $effect = $sequence.Item($e)
            $effects.Add([pscustomobject]@{
                Index = $e
                ShapeId = Safe-Value { $effect.Shape.Id } -1
                EffectType = $effect.EffectType
                TriggerType = $effect.Timing.TriggerType
                Duration = Safe-Value { [double]$effect.Timing.Duration } 0
                Delay = Safe-Value { [double]$effect.Timing.TriggerDelayTime } 0
            })
        }

        $transition = $slide.SlideShowTransition
        $slideInventory.Add([pscustomobject]@{
            Index = $slide.SlideIndex
            Name = $slide.Name
            Layout = Safe-Value { $slide.CustomLayout.Name }
            ShapeCount = $slide.Shapes.Count
            PictureCount = @($shapeInventory | Where-Object { $_.Type -in @(11, 13) }).Count
            Shapes = @($shapeInventory)
            Animations = @($effects)
            Transition = [pscustomobject]@{
                EntryEffect = $transition.EntryEffect
                AdvanceOnClick = $transition.AdvanceOnClick
                AdvanceOnTime = $transition.AdvanceOnTime
                AdvanceTime = [double]$transition.AdvanceTime
                Speed = $transition.Speed
            }
        })
    }

    $result = [pscustomobject]@{
        Deck = (Get-Item -LiteralPath $Deck).FullName
        SlideWidth = [double]$presentation.PageSetup.SlideWidth
        SlideHeight = [double]$presentation.PageSetup.SlideHeight
        SlideCount = $presentation.Slides.Count
        Slides = @($slideInventory)
    }
    $json = $result | ConvertTo-Json -Depth 12
    if ([string]::IsNullOrWhiteSpace($OutputJson)) {
        $json
    } else {
        $json | Set-Content -LiteralPath $OutputJson -Encoding utf8
        Write-Host "Inventory saved: $OutputJson"
    }
}
finally {
    if ($null -ne $presentation) { try { $presentation.Close() } catch {}; Release-ComObject $presentation }
    if ($null -ne $ppt) { try { $ppt.Quit() } catch {}; Release-ComObject $ppt }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
