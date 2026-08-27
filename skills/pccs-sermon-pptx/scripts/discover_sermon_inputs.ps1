param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string]$Deck = ''
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "Project root not found: $Root"
}

$rootItem = Get-Item -LiteralPath $Root
$files = @(Get-ChildItem -LiteralPath $rootItem.FullName -Recurse -File -ErrorAction SilentlyContinue)
$pptxFiles = @($files | Where-Object { $_.Extension -ieq '.pptx' })
$videoExtensions = @('.mp4', '.mov', '.m4v', '.avi', '.wmv', '.mkv')
$videoFiles = @($files | Where-Object { $videoExtensions -contains $_.Extension.ToLowerInvariant() })

if ([string]::IsNullOrWhiteSpace($Deck)) {
    $rankedDecks = @(
        foreach ($file in $pptxFiles) {
            $score = 0
            if ($file.BaseName -notmatch '(?i)(_qa|qa-|render|duplicate|统一排版|美化版)') { $score += 100 }
            if ($file.BaseName -match '(?i)_v(?<version>\d+)') { $score += [int]$Matches.version }
            [pscustomobject]@{
                Path = $file.FullName
                Score = $score
                LastWriteTime = $file.LastWriteTime
                Bytes = $file.Length
            }
        }
    ) | Sort-Object Score, LastWriteTime -Descending
    if ($rankedDecks.Count -eq 0) { throw "No PPTX files found under: $Root" }
    $selectedDeck = Get-Item -LiteralPath $rankedDecks[0].Path
} else {
    if (-not (Test-Path -LiteralPath $Deck -PathType Leaf)) { throw "Requested deck not found: $Deck" }
    $selectedDeck = Get-Item -LiteralPath $Deck
    $rankedDecks = @([pscustomobject]@{
        Path = $selectedDeck.FullName
        Score = 1000
        LastWriteTime = $selectedDeck.LastWriteTime
        Bytes = $selectedDeck.Length
    })
}

$dateTokens = [System.Collections.Generic.HashSet[string]]::new()
foreach ($match in [regex]::Matches($selectedDeck.FullName, '(?<!\d)20\d{6}(?!\d)')) {
    [void]$dateTokens.Add($match.Value)
}

$rankedVideos = @(
    foreach ($video in $videoFiles) {
        $score = 0
        $reasons = [System.Collections.Generic.List[string]]::new()
        if ($video.DirectoryName -ieq $selectedDeck.DirectoryName) {
            $score += 200
            $reasons.Add('same-directory')
        }
        foreach ($token in $dateTokens) {
            if ($video.FullName -like "*$token*") {
                $score += 80
                $reasons.Add("date-$token")
            }
        }
        if ($video.LastWriteTime.Date -eq $selectedDeck.LastWriteTime.Date) {
            $score += 20
            $reasons.Add('same-modified-date')
        }
        if ($video.Length -ge 500MB) {
            $score += 20
            $reasons.Add('large-video')
        } elseif ($video.Length -ge 100MB) {
            $score += 10
            $reasons.Add('substantial-video')
        }
        [pscustomobject]@{
            Path = $video.FullName
            Score = $score
            Reasons = @($reasons)
            LastWriteTime = $video.LastWriteTime
            Bytes = $video.Length
        }
    }
) | Sort-Object Score, LastWriteTime, Bytes -Descending

[pscustomobject]@{
    Root = $rootItem.FullName
    SelectedDeck = $selectedDeck.FullName
    LikelyVideo = if ($rankedVideos.Count -gt 0) { $rankedVideos[0].Path } else { $null }
    DeckCandidates = @($rankedDecks)
    VideoCandidates = @($rankedVideos)
} | ConvertTo-Json -Depth 6
