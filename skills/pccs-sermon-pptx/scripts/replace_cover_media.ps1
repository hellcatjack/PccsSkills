param(
    [Parameter(Mandatory = $true)][string]$Deck,
    [Parameter(Mandatory = $true)][string]$Redraw,
    [int]$SlideNumber = 1,
    [Parameter(Mandatory = $true)][int]$ShapeId
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Deck -PathType Leaf)) { throw "Deck not found: $Deck" }
if (-not (Test-Path -LiteralPath $Redraw -PathType Leaf)) { throw "Redraw not found: $Redraw" }
if ($SlideNumber -lt 1) { throw 'SlideNumber must be at least 1.' }
if ($ShapeId -lt 1) { throw 'ShapeId must be at least 1.' }

$resolvedDeck = (Resolve-Path -LiteralPath $Deck).Path
$resolvedRedraw = (Resolve-Path -LiteralPath $Redraw).Path
$slideEntryName = "ppt/slides/slide$SlideNumber.xml"
$relationshipEntryName = "ppt/slides/_rels/slide$SlideNumber.xml.rels"

Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Drawing

function Read-ZipEntryText($Entry) {
    $reader = [System.IO.StreamReader]::new($Entry.Open())
    try { return $reader.ReadToEnd() }
    finally { $reader.Dispose() }
}

$readZip = [System.IO.Compression.ZipFile]::OpenRead($resolvedDeck)
try {
    $slideEntry = $readZip.GetEntry($slideEntryName)
    $relationshipEntry = $readZip.GetEntry($relationshipEntryName)
    if (-not $slideEntry) { throw "Slide entry not found: $slideEntryName" }
    if (-not $relationshipEntry) { throw "Slide relationship entry not found: $relationshipEntryName" }

    [xml]$slideXml = Read-ZipEntryText $slideEntry
    [xml]$relationshipXml = Read-ZipEntryText $relationshipEntry
    $namespaces = [System.Xml.XmlNamespaceManager]::new($slideXml.NameTable)
    $namespaces.AddNamespace('p', 'http://schemas.openxmlformats.org/presentationml/2006/main')
    $namespaces.AddNamespace('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
    $namespaces.AddNamespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')

    $picture = $slideXml.SelectSingleNode("//p:pic[p:nvPicPr/p:cNvPr[@id='$ShapeId']]", $namespaces)
    if (-not $picture) { throw "Slide $SlideNumber picture shape ID $ShapeId was not found." }
    $blip = $picture.SelectSingleNode('.//a:blip', $namespaces)
    if (-not $blip) { throw "Slide $SlideNumber picture shape ID $ShapeId has no embedded image relationship." }
    $relationshipId = $blip.GetAttribute('embed', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    $relationship = @($relationshipXml.Relationships.Relationship) | Where-Object { $_.Id -eq $relationshipId } | Select-Object -First 1
    if (-not $relationship -or $relationship.Type -notlike '*/image') {
        throw "Image relationship $relationshipId was not found for slide $SlideNumber shape ID $ShapeId."
    }

    $target = [string]$relationship.Target
    $mediaFileName = [System.IO.Path]::GetFileName($target)
    $mediaEntryName = "ppt/media/$mediaFileName"
    if (-not $readZip.GetEntry($mediaEntryName)) { throw "Embedded cover media not found: $mediaEntryName" }

    $references = @()
    foreach ($entry in $readZip.Entries | Where-Object { $_.FullName -like 'ppt/slides/_rels/*.rels' }) {
        [xml]$rels = Read-ZipEntryText $entry
        foreach ($item in @($rels.Relationships.Relationship)) {
            if ([System.IO.Path]::GetFileName([string]$item.Target) -eq $mediaFileName -and $item.Type -like '*/image') {
                $references += "$($entry.FullName):$($item.Id)"
            }
        }
    }
    if ($references.Count -ne 1) {
        throw "Cover media is shared by $($references.Count) relationships. Stop instead of changing other slides: $($references -join ', ')"
    }
}
finally {
    $readZip.Dispose()
}

$extension = [System.IO.Path]::GetExtension($mediaFileName).ToLowerInvariant()
$imageFormat = switch ($extension) {
    '.tif' { [System.Drawing.Imaging.ImageFormat]::Tiff }
    '.tiff' { [System.Drawing.Imaging.ImageFormat]::Tiff }
    '.png' { [System.Drawing.Imaging.ImageFormat]::Png }
    '.jpg' { [System.Drawing.Imaging.ImageFormat]::Jpeg }
    '.jpeg' { [System.Drawing.Imaging.ImageFormat]::Jpeg }
    '.bmp' { [System.Drawing.Imaging.ImageFormat]::Bmp }
    '.gif' { [System.Drawing.Imaging.ImageFormat]::Gif }
    default { throw "Unsupported embedded cover format '$extension'. Use an in-place PowerPoint picture replacement and rerun QA." }
}

$convertedImage = Join-Path ([System.IO.Path]::GetTempPath()) ("pccs-cover-{0}{1}" -f ([guid]::NewGuid().ToString('N')), $extension)
$sourceImage = [System.Drawing.Image]::FromFile($resolvedRedraw)
try {
    $pixelWidth = $sourceImage.Width
    $pixelHeight = $sourceImage.Height
    $sourceImage.Save($convertedImage, $imageFormat)
}
finally {
    $sourceImage.Dispose()
}

try {
    $zip = [System.IO.Compression.ZipFile]::Open($resolvedDeck, [System.IO.Compression.ZipArchiveMode]::Update)
    try {
        $oldEntry = $zip.GetEntry($mediaEntryName)
        if (-not $oldEntry) { throw "Embedded cover media disappeared before replacement: $mediaEntryName" }
        $oldEntry.Delete()
        $newEntry = $zip.CreateEntry($mediaEntryName, [System.IO.Compression.CompressionLevel]::Optimal)
        $source = [System.IO.File]::OpenRead($convertedImage)
        $destination = $newEntry.Open()
        try { $source.CopyTo($destination) }
        finally {
            $source.Dispose()
            $destination.Dispose()
        }
    }
    finally {
        $zip.Dispose()
    }
}
finally {
    Remove-Item -LiteralPath $convertedImage -Force -ErrorAction SilentlyContinue
}

[pscustomobject]@{
    Deck = $resolvedDeck
    Slide = $SlideNumber
    ShapeId = $ShapeId
    RelationshipId = $relationshipId
    MediaEntry = $mediaEntryName
    PixelWidth = $pixelWidth
    PixelHeight = $pixelHeight
}
