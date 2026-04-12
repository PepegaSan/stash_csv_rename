<#
.SYNOPSIS
  Renames files on disk using a CSV from export_stash_files.ps1.
  Either set column new_leaf (full new file name only, not a path) per row, or use -SuffixBeforeExt / -Prefix for all matching rows.

.PARAMETER OnlyUnderFolder
  Only process rows whose file_path is under this folder (case-insensitive). Example: -OnlyUnderFolder "D:\Videos\Batch1"

.PARAMETER SuffixBeforeExt
  Inserted before the extension: clip.mp4 -> clip_SUFFIX.mp4

.PARAMETER Prefix
  Prepended to the file name: clip.mp4 -> PREFIXclip.mp4

.PARAMETER UseNewLeafColumn
  If set (default), any non-empty new_leaf in CSV overrides automatic prefix/suffix for that row.

.EXAMPLE
  .\apply_stash_file_renames.ps1 -CsvPath ".\stash_files_export.csv" -WhatIf
.EXAMPLE
  .\apply_stash_file_renames.ps1 -CsvPath ".\files.csv" -OnlyUnderFolder "D:\Media\X" -SuffixBeforeExt "_renamed"
.EXAMPLE
  # After filling new_leaf in Excel for manual names:
  .\apply_stash_file_renames.ps1 -CsvPath ".\files.csv" -UseNewLeafColumn
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string] $CsvPath,
    [string] $Delimiter = ';',
    [string] $OnlyUnderFolder = '',
    [string] $SuffixBeforeExt = '',
    [string] $Prefix = '',
    [switch] $UseNewLeafColumn = $true
)

$ErrorActionPreference = "Stop"

if ($Delimiter -ne ';' -and $Delimiter -ne ',') {
    Write-Error "Delimiter must be ';' or ','."
}
if (-not (Test-Path -LiteralPath $CsvPath -PathType Leaf)) {
    Write-Error "CSV not found: $CsvPath"
}

if ($SuffixBeforeExt -match '[\\/]' -or $Prefix -match '[\\/]') {
    Write-Error 'Prefix and SuffixBeforeExt must not contain \ or /.'
}

function Normalize-StashFilePathForWindows {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string] $PathStr)
    if ([string]::IsNullOrWhiteSpace($PathStr)) { return '' }
    $s = $PathStr.Trim().Trim([char]0x22).Trim([char]0x27)
    if ($s.Length -ge 3 -and $s[1] -eq ':' -and [char]::IsLetter($s[0]) -and $s[2] -notin @('\', '/')) {
        $s = $s.Substring(0, 2) + '\' + $s.Substring(2)
    }
    return ($s -replace '/', '\')
}

function Normalize-StashCommercialAtString {
    param([Parameter(Mandatory = $true)][string]$s)
    return $s.Replace([char]0xFF20, '@').Replace([char]0xFE6B, '@')
}

function Resolve-StashPathViaParentNfc {
    param([Parameter(Mandatory = $true)][string] $LogicalPath)
    $norm = Normalize-StashFilePathForWindows $LogicalPath
    if ([string]::IsNullOrWhiteSpace($norm)) { return $null }
    if (-not [System.IO.Path]::IsPathRooted($norm)) { return $null }
    $parent = [System.IO.Path]::GetDirectoryName($norm)
    $leaf = [System.IO.Path]::GetFileName($norm)
    if ([string]::IsNullOrWhiteSpace($parent) -or [string]::IsNullOrWhiteSpace($leaf)) { return $null }
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { return $null }
    $targetNfc = $leaf.Normalize([System.Text.NormalizationForm]::FormC)
    foreach ($f in Get-ChildItem -LiteralPath $parent -File -ErrorAction SilentlyContinue) {
        if ($f.Name -eq $leaf) { return $f.FullName }
        if ($f.Name.Normalize([System.Text.NormalizationForm]::FormC) -eq $targetNfc) { return $f.FullName }
    }
    return $null
}

function Expand-StashLeafVariants {
    param([Parameter(Mandatory = $true)][string]$leaf)
    $t = Normalize-StashCommercialAtString $leaf.Trim()
    $set = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    [void]$set.Add($t)
    try {
        $d = [System.Uri]::UnescapeDataString($t)
        if ($d -cne $t) { [void]$set.Add($d) }
    } catch { }
    for ($round = 0; $round -lt 6; $round++) {
        $added = $false
        foreach ($item in @($set)) {
            foreach ($encCode in @(1252, 28591)) {
                try {
                    $enc = [System.Text.Encoding]::GetEncoding($encCode)
                    $fix = [System.Text.Encoding]::UTF8.GetString($enc.GetBytes($item))
                    if ($fix -cne $item -and $set.Add($fix)) { $added = $true }
                } catch { continue }
            }
        }
        if (-not $added) { break }
    }
    $snap = @($set)
    foreach ($item in $snap) {
        try { [void]$set.Add($item.Normalize([System.Text.NormalizationForm]::FormC)) } catch { }
        try { [void]$set.Add($item.Normalize([System.Text.NormalizationForm]::FormD)) } catch { }
        try { [void]$set.Add($item.ToLowerInvariant()) } catch { }
    }
    return $set
}

function Resolve-StashPathViaParentLeafVariants {
    param([Parameter(Mandatory = $true)][string] $LogicalPath)
    $norm = Normalize-StashFilePathForWindows $LogicalPath
    if ([string]::IsNullOrWhiteSpace($norm)) { return $null }
    if (-not [System.IO.Path]::IsPathRooted($norm)) { return $null }
    $parent = [System.IO.Path]::GetDirectoryName($norm)
    $leaf = [System.IO.Path]::GetFileName($norm)
    if ([string]::IsNullOrWhiteSpace($parent) -or [string]::IsNullOrWhiteSpace($leaf)) { return $null }
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { return $null }
    $want = Expand-StashLeafVariants $leaf
    foreach ($f in Get-ChildItem -LiteralPath $parent -File -ErrorAction SilentlyContinue) {
        $have = Expand-StashLeafVariants $f.Name
        foreach ($w in $want) {
            if ($have.Contains($w)) { return $f.FullName }
        }
    }
    return $null
}

function Resolve-StashExistingFilePath {
    param([Parameter(Mandatory = $true)][string] $PathStr)
    $candidates = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    function Add-Cand([string] $x) {
        if ([string]::IsNullOrWhiteSpace($x)) { return }
        $t = $x.Trim()
        [void]$candidates.Add($t)
        $at = Normalize-StashCommercialAtString $t
        if ($at -cne $t) { [void]$candidates.Add($at) }
        $norm = Normalize-StashFilePathForWindows $x
        if (-not [string]::IsNullOrWhiteSpace($norm)) {
            [void]$candidates.Add($norm)
            $na = Normalize-StashCommercialAtString $norm
            if ($na -cne $norm) { [void]$candidates.Add($na) }
        }
    }
    Add-Cand $PathStr
    try {
        $decoded = [System.Uri]::UnescapeDataString($PathStr)
        Add-Cand $decoded
    } catch { }
    $firstRound = @($candidates)
    foreach ($item in $firstRound) {
        if ([string]::IsNullOrWhiteSpace($item)) { continue }
        foreach ($encCode in @(1252, 28591)) {
            try {
                $enc = [System.Text.Encoding]::GetEncoding($encCode)
                $bytes = $enc.GetBytes($item)
                $fixed = [System.Text.Encoding]::UTF8.GetString($bytes)
                Add-Cand $fixed
            } catch { continue }
        }
    }
    foreach ($p in $candidates) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        try {
            if (Test-Path -LiteralPath $p -PathType Leaf) {
                return (Get-Item -LiteralPath $p -ErrorAction Stop).FullName
            }
        } catch { continue }
        $viaNfc = Resolve-StashPathViaParentNfc $p
        if ($viaNfc) { return $viaNfc }
        $viaLeaf = Resolve-StashPathViaParentLeafVariants $p
        if ($viaLeaf) { return $viaLeaf }
    }
    return $null
}

function Get-StashUniqueLeafInDir {
    param(
        [Parameter(Mandatory = $true)][string] $Directory,
        [Parameter(Mandatory = $true)][string] $DesiredLeaf
    )
    if (-not (Test-Path -LiteralPath $Directory)) { return $DesiredLeaf }
    $base = [System.IO.Path]::GetFileNameWithoutExtension($DesiredLeaf)
    $ext = [System.IO.Path]::GetExtension($DesiredLeaf)
    $candidate = $DesiredLeaf
    $n = 0
    while (Test-Path -LiteralPath (Join-Path $Directory $candidate)) {
        $n++
        $candidate = "${base}_${n}${ext}"
    }
    return $candidate
}

function Test-PathUnderFolder {
    param([string] $FilePath, [string] $Folder)
    if ([string]::IsNullOrWhiteSpace($Folder)) { return $true }
    try {
        $f = (Get-Item -LiteralPath (Normalize-StashFilePathForWindows $Folder) -ErrorAction Stop).FullName.TrimEnd('\')
        $p = (Get-Item -LiteralPath $FilePath -ErrorAction Stop).FullName
        return $p.StartsWith($f + '\', [StringComparison]::OrdinalIgnoreCase) -or ($p -ieq $f)
    } catch {
        return $false
    }
}

$raw = [System.IO.File]::ReadAllText($CsvPath, [System.Text.UTF8Encoding]::new($true))
$head = $raw.Substring(0, [Math]::Min($raw.Length, 4096))
$detectDelim = if ($head.Split(';').Length -ge $head.Split(',').Length) { ';' } else { ',' }
if ($Delimiter -ne $detectDelim) {
    Write-Warning "Delimiter parameter is '$Delimiter' but file seems to use '$detectDelim'. Trying parameter first."
}

$rows = Import-Csv -LiteralPath $CsvPath -Delimiter $Delimiter
if ($rows.Count -eq 0) {
    Write-Warning "No data rows in CSV."
    exit 0
}

$propNames = $rows[0].PSObject.Properties.Name
if ($propNames -notcontains 'file_path') {
    Write-Error "CSV must contain a file_path column."
}

$normRoot = ''
if (-not [string]::IsNullOrWhiteSpace($OnlyUnderFolder)) {
    $normRoot = (Normalize-StashFilePathForWindows $OnlyUnderFolder).TrimEnd('\')
    if (-not (Test-Path -LiteralPath $normRoot)) {
        Write-Error "OnlyUnderFolder does not exist: $OnlyUnderFolder"
    }
}

if (-not $UseNewLeafColumn -and [string]::IsNullOrWhiteSpace($SuffixBeforeExt) -and [string]::IsNullOrWhiteSpace($Prefix)) {
    Write-Error "Provide -SuffixBeforeExt and/or -Prefix, or use -UseNewLeafColumn with non-empty new_leaf values in the CSV."
}

Write-Warning (
    "Files will be renamed on disk. Then run Stash Tasks -> Scan. " +
    "Stash matches by oshash/MD5. Do not run Clean before Scan. " +
    "Perceptual fingerprint does not update paths."
)

$done = 0
$skipped = 0

foreach ($row in $rows) {
    $oldFull = [string]$row.file_path
    if ([string]::IsNullOrWhiteSpace($oldFull)) { $skipped++; continue }
    $resolved = Resolve-StashExistingFilePath $oldFull
    if ($resolved) {
        $oldFull = $resolved
    } else {
        $oldFull = Normalize-StashFilePathForWindows $oldFull
    }

    if (-not (Test-Path -LiteralPath $oldFull -PathType Leaf)) {
        Write-Warning "Not found (skip): $oldFull"
        $skipped++
        continue
    }

    if (-not (Test-PathUnderFolder -FilePath $oldFull -Folder $normRoot)) {
        $skipped++
        continue
    }

    $item = Get-Item -LiteralPath $oldFull -ErrorAction Stop
    $dir = $item.DirectoryName
    $leaf = $item.Name

    $newLeaf = ''
    if ($UseNewLeafColumn -and ($propNames -contains 'new_leaf')) {
        $newLeaf = [string]$row.new_leaf
    }
    $newLeaf = $newLeaf.Trim()
    if ([string]::IsNullOrWhiteSpace($newLeaf)) {
        $base = [System.IO.Path]::GetFileNameWithoutExtension($leaf)
        $ext = [System.IO.Path]::GetExtension($leaf)
        $newLeaf = $Prefix + $base + $SuffixBeforeExt + $ext
    }

    if ($newLeaf -match '[\\/]' -or $newLeaf -eq '..' -or $newLeaf -eq '.') {
        Write-Warning "Invalid new_leaf (skip): $newLeaf"
        $skipped++
        continue
    }
    if ($newLeaf -eq $leaf) {
        $skipped++
        continue
    }

    $newLeaf = Get-StashUniqueLeafInDir -Directory $dir -DesiredLeaf $newLeaf
    if ($newLeaf -eq $leaf) {
        $skipped++
        continue
    }

    $targetFull = Join-Path $dir $newLeaf
    if ($PSCmdlet.ShouldProcess($oldFull, "Rename to: $newLeaf")) {
        try {
            Rename-Item -LiteralPath $oldFull -NewName $newLeaf -ErrorAction Stop
            $done++
        } catch {
            Write-Warning "Rename failed: $oldFull -> $newLeaf : $_"
            $skipped++
        }
    }
}

Write-Host "Renamed: $done  Skipped: $skipped"
if ($done -gt 0) {
    Write-Host "Run Stash -> Tasks -> Scan to refresh library paths."
}
