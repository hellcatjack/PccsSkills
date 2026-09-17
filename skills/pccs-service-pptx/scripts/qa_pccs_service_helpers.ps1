# Pure guards and small COM inspection helpers, shared with tests.
function Get-PccsServiceSlideMap {
    param($Plan, [int]$SlideCount)
    $map = @{}
    $records = @($Plan.slides)
    if ($records.Count -eq 0) { throw 'Project JSON must declare at least one service slide.' }
    $localIndex = 0
    foreach ($record in $records) {
        $localIndex++
        if (($record.index -isnot [int] -and $record.index -isnot [long]) -or $record.index -ne $localIndex) {
            throw 'Service record index must remain locally consecutive, beginning at 1.'
        }
        $finalIndex = if ($null -ne $record.PSObject.Properties['final_slide_index']) { $record.final_slide_index } else { $record.index }
        if (($finalIndex -isnot [int] -and $finalIndex -isnot [long]) -or $finalIndex -lt 1 -or $finalIndex -gt $SlideCount) {
            throw "Service record $localIndex final_slide_index must be an integer within the deck's 1..$SlideCount range."
        }
        $key = [int]$finalIndex
        if ($map.ContainsKey($key)) { throw "More than one service record maps to final_slide_index $key." }
        $map[$key] = $record
    }
    return $map
}

function Assert-PccsConsumedServiceSlides {
    param([hashtable]$Map, $Consumed)
    foreach ($index in $Map.Keys) {
        if (-not $Consumed.Contains([int]$index)) { throw "Declared service final_slide_index $index was not checked." }
    }
}

function Assert-PccsNewOutputPath {
    param([string]$Source, [string]$Destination)
    $sourcePath = [IO.Path]::GetFullPath($Source)
    $destinationPath = [IO.Path]::GetFullPath($Destination)
    if ([string]::Equals($sourcePath, $destinationPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'QA output must not replace the source presentation.'
    }
    if (Test-Path -LiteralPath $destinationPath) {
        throw "QA output already exists; choose a new path: $destinationPath"
    }
}

function Register-PccsLayout {
    param([hashtable]$Registry, $Slide)
    # Names are not identities: two masters can each have CustomLayout.Index=1.
    $layout = $Slide.CustomLayout
    $key = '{0}:{1}' -f $Slide.Design.Index, $layout.Index
    if ($Registry.ContainsKey($key)) { return }
    foreach ($entry in $Registry.Values) {
        if ($entry.Layout.Name -eq $layout.Name -or $entry.Layout.MatchingName -eq $layout.MatchingName) {
            throw "Distinct layouts must have unique Name and MatchingName: '$($layout.Name)'."
        }
    }
    $Registry[$key] = @{ Layout = $layout; SourceSlide = $Slide.SlideIndex }
}

function Get-PccsSlideTextState {
    param($Slide, [switch]$IncludeText)
    $shapes = @()
    $layoutShapes = @()
    $foregroundShapes = @()
    foreach ($shape in $Slide.CustomLayout.Shapes) {
        $layoutShapes += [ordered]@{
            Name = $shape.Name; Type = $shape.Type; Left = $shape.Left; Top = $shape.Top
            Width = $shape.Width; Height = $shape.Height; ZOrder = $shape.ZOrderPosition
        }
    }
    foreach ($shape in $Slide.Shapes) {
        $foregroundShapes += [ordered]@{
            Name = $shape.Name; Type = $shape.Type; Left = $shape.Left; Top = $shape.Top
            Width = $shape.Width; Height = $shape.Height; ZOrder = $shape.ZOrderPosition; Visible = $shape.Visible
        }
        if (-not $shape.HasTextFrame -or -not $shape.TextFrame.HasText) { continue }
        $range = $shape.TextFrame2.TextRange
        $characters = @()
        for ($i = 1; $i -le $range.Length; $i++) {
            $character = $range.Characters($i, 1)
            $font = $character.Font
            $characters += [ordered]@{
                Name = $font.Name; NameFarEast = $font.NameFarEast; Size = $font.Size
                Bold = $font.Bold; Italic = $font.Italic; Fill = $font.Fill.ForeColor.RGB
                ShadowVisible = $font.Shadow.Visible; Alignment = $character.ParagraphFormat.Alignment
                SpaceWithin = $character.ParagraphFormat.SpaceWithin
                SpaceBefore = $character.ParagraphFormat.SpaceBefore
                SpaceAfter = $character.ParagraphFormat.SpaceAfter
            }
        }
        $state = [ordered]@{
            Name = $shape.Name; Left = $shape.Left; Top = $shape.Top
            Width = $shape.Width; Height = $shape.Height; Characters = $characters
            AutoSize = $shape.TextFrame2.AutoSize; WordWrap = $shape.TextFrame2.WordWrap
        }
        if ($IncludeText) { $state.Text = $range.Text }
        $shapes += $state
    }
    [ordered]@{
        LayoutName = $Slide.CustomLayout.Name
        MatchingName = $Slide.CustomLayout.MatchingName
        LayoutShapes = $layoutShapes
        ForegroundShapes = $foregroundShapes
        TextShapes = $shapes
    } | ConvertTo-Json -Depth 12 -Compress
}

function Set-PccsVisibleQaEdit {
    param($Slide)
    foreach ($shape in $Slide.Shapes) {
        if ($shape.Visible -eq 0 -or -not $shape.HasTextFrame -or -not $shape.TextFrame.HasText) { continue }
        $range = $shape.TextFrame2.TextRange
        for ($i = 1; $i -le $range.Length; $i++) {
            $character = $range.Characters($i, 1)
            if ([string]::IsNullOrWhiteSpace($character.Text)) { continue }
            # Replace one visible character, retaining the existing run and length.
            $character.Text = $(if ($character.Text -ceq 'Q') { 'R' } else { 'Q' })
            return
        }
    }
    throw "Layout '$($Slide.CustomLayout.Name)' has no visible text to edit; choose a text-bearing representative manually."
}

function Assert-PccsScriptureBody {
    param($Slide, $Plan)
    $bodies = @($Slide.Shapes | Where-Object { $_.Name -in @('PCCS scripture body', 'Scripture body') })
    if ($bodies.Count -ne 1) { throw "Slide $($Slide.SlideIndex): expected one named PCCS scripture body or Scripture body." }
    $body = $bodies[0]
    $expected = $Plan.source_lines -join "`r"
    $actual = $body.TextFrame2.TextRange.Text.Replace("`r`n", "`r").Replace("`n", "`r")
    if ($actual -cne $expected -and $actual -cne ($expected + "`r")) {
        throw "Slide $($Slide.SlideIndex): scripture characters or source line order changed."
    }
    $fontName = if ($Plan.body_font) { $Plan.body_font } else { 'SimSun' }
    $fontSize = if ($null -ne $Plan.body_font_pt) { [double]$Plan.body_font_pt } else { 36 }
    $alignment = if ($Plan.alignment) { $Plan.alignment } else { 'left' }
    $alignments = @{ left = 1; center = 2; right = 3; justify = 4 }
    $range = $body.TextFrame2.TextRange
    if ($body.TextFrame2.AutoSize -eq 2) { throw 'Scripture body uses automatic font shrinking.' }
    for ($i = 1; $i -le $range.Length; $i++) {
        $character = $range.Characters($i, 1)
        if ($character.Text -match '^[\r\n]$') { continue }
        $font = $character.Font
        if ($font.Name -ne $fontName -or $font.NameFarEast -ne $fontName -or
            [Math]::Abs($font.Size - $fontSize) -gt 0.05) {
            throw "Slide $($Slide.SlideIndex): scripture must resolve to $fontName $fontSize pt."
        }
        if ($character.ParagraphFormat.Alignment -ne $alignments[$alignment]) {
            throw "Slide $($Slide.SlideIndex): scripture alignment differs from $alignment."
        }
        if (-not $Plan.body_shadow -and $font.Shadow.Visible -ne 0) {
            throw "Slide $($Slide.SlideIndex): scripture body has a shadow."
        }
    }
}
