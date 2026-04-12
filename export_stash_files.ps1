<#
.SYNOPSIS
  Lists scene video files from Stash (GraphQL) and writes a UTF-8 BOM CSV for batch rename workflows.
  Filter by path / file name (optional). One row per unique file path. Does not rename anything.

.PARAMETER PathPrefix
  Only include files whose full path (after normalization) starts with this string (case-insensitive).
  Example: -PathPrefix "D:\Videos\ProjectA"

.PARAMETER PathContains
  Only include files whose full path contains this substring (case-insensitive).

.PARAMETER FileNameContains
  Only include files whose file name (leaf) contains this substring (case-insensitive).

.PARAMETER FileNameRegex
  Only include files whose file name matches this PowerShell regex (case-insensitive by default).

.EXAMPLE
  .\export_stash_files.ps1 -OutFile "files_to_rename.csv"
.EXAMPLE
  .\export_stash_files.ps1 -PathPrefix "D:\Media\FolderX" -OutFile "folder_x_files.csv"
#>
[CmdletBinding()]
param(
    [string] $StashUrl = "http://127.0.0.1:9999",
    [string] $ApiKey = $env:STASH_API_KEY,
    [string] $OutFile = "stash_files_export.csv",
    [int] $PerPage = 500,
    [string] $Delimiter = ';',
    [string] $PathPrefix = '',
    [string] $PathContains = '',
    [string] $FileNameContains = '',
    [string] $FileNameRegex = ''
)

$ErrorActionPreference = "Stop"

if ($Delimiter -ne ';' -and $Delimiter -ne ',') {
    Write-Error "Delimiter must be ';' or ','."
}

function Escape-StashCsvField {
    param($Value, [string] $Delim)
    if ($null -eq $Value) { $Value = '' }
    else { $Value = [string]$Value }
    $mustQuote = $Value.Contains($Delim) -or $Value.Contains('"') -or $Value.Contains("`r") -or $Value.Contains("`n") `
        -or $Value.Contains('&') -or $Value.Contains('%') -or $Value.Contains('@') -or $Value.Contains("'") `
        -or $Value.Contains('#') -or $Value.Contains('^') -or $Value.Contains('`')
    $escaped = $Value.Replace('"', '""')
    if ($mustQuote) { return '"' + $escaped + '"' }
    return $escaped
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

function Test-StashFileRowFilter {
    param(
        [string] $FullPath,
        [string] $Leaf,
        [string] $PathPrefix,
        [string] $PathContains,
        [string] $FileNameContains,
        [string] $FileNameRegex
    )
    if ([string]::IsNullOrWhiteSpace($FullPath)) { return $false }
    $fp = $FullPath
    if (-not [string]::IsNullOrWhiteSpace($PathPrefix)) {
        if (-not $fp.StartsWith($PathPrefix, [StringComparison]::OrdinalIgnoreCase)) { return $false }
    }
    if (-not [string]::IsNullOrWhiteSpace($PathContains)) {
        if ($fp.IndexOf($PathContains, [StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
    }
    if (-not [string]::IsNullOrWhiteSpace($FileNameContains)) {
        if ($Leaf.IndexOf($FileNameContains, [StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
    }
    if (-not [string]::IsNullOrWhiteSpace($FileNameRegex)) {
        if ($Leaf -notmatch $FileNameRegex) { return $false }
    }
    return $true
}

$normPrefix = if ([string]::IsNullOrWhiteSpace($PathPrefix)) { '' } else { (Normalize-StashFilePathForWindows $PathPrefix).TrimEnd('\') + '\' }

$uri = ($StashUrl.TrimEnd("/")) + "/graphql"
$headers = @{ "Content-Type" = "application/json" }
if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
    $headers["ApiKey"] = $ApiKey
}

$gql = @'
query ExportSceneFiles($filter: FindFilterType) {
  findScenes(filter: $filter) {
    count
    scenes {
      id
      title
      files { path }
    }
  }
}
'@

$page = 1
$seenPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$rows = New-Object System.Collections.Generic.List[object]
$totalCount = $null

do {
    $body = [PSCustomObject]@{
        query     = $gql
        variables = [PSCustomObject]@{
            filter = [PSCustomObject]@{
                per_page = $PerPage
                page     = $page
            }
        }
    }
    $json = $body | ConvertTo-Json -Compress -Depth 12
    $resp = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $json -TimeoutSec 300

    if ($resp.errors) {
        $msg = ($resp.errors | ForEach-Object { $_.message }) -join "; "
        Write-Error "GraphQL: $msg"
    }

    $chunk = $resp.data.findScenes
    if ($null -eq $totalCount) { $totalCount = $chunk.count }
    $scenes = $chunk.scenes
    if ($null -eq $scenes) { $scenes = @() }
    else { $scenes = @($scenes) }

    foreach ($sc in $scenes) {
        $files = @($sc.files)
        if ($files.Count -eq 0) { continue }
        $rawPath = [string]$files[0].path
        if ([string]::IsNullOrWhiteSpace($rawPath)) { continue }
        $fp = Normalize-StashFilePathForWindows $rawPath
        $leaf = [System.IO.Path]::GetFileName($fp)
        $dir = [System.IO.Path]::GetDirectoryName($fp)
        if (-not (Test-StashFileRowFilter -FullPath $fp -Leaf $leaf -PathPrefix $normPrefix `
                -PathContains $PathContains -FileNameContains $FileNameContains -FileNameRegex $FileNameRegex)) {
            continue
        }
        $key = $fp.Trim()
        if ($seenPaths.Contains($key)) { continue }
        [void]$seenPaths.Add($key)

        $rows.Add([PSCustomObject][ordered]@{
            scene_id    = $sc.id
            scene_title = [string]$sc.title
            file_path   = $fp
            file_directory = if ($dir) { $dir } else { '' }
            file_name   = $leaf
            new_leaf    = ''
        })
    }

    Write-Host "Page $page : $($scenes.Count) scenes scanned, $($rows.Count) unique file path(s) matched so far (total scenes ~$totalCount)"
    $page++
} while ($scenes.Count -eq $PerPage)

# Fix paths to existing files on disk (mojibake), same idea as marker export
$cache = @{}
$fixed = 0
foreach ($r in $rows) {
    $orig = [string]$r.file_path
    if ([string]::IsNullOrWhiteSpace($orig)) { continue }
    $k = $orig.Trim()
    if (-not $cache.ContainsKey($k)) { $cache[$k] = Resolve-StashExistingFilePath $k }
    $hit = $cache[$k]
    if ($hit) {
        if ($hit -ine $k) { $fixed++ }
        $r.file_path = $hit
        $r.file_directory = [System.IO.Path]::GetDirectoryName($hit)
        $r.file_name = [System.IO.Path]::GetFileName($hit)
    }
}
if ($fixed -gt 0) {
    Write-Host "Updated file_path on $fixed row(s) to the resolved on-disk path (incl. UTF-8 mojibake fix where applicable)."
}

$dirOut = Split-Path -Parent $OutFile
if ($dirOut -and -not (Test-Path -LiteralPath $dirOut)) {
    New-Item -ItemType Directory -Path $dirOut -Force | Out-Null
}

$colNames = @('scene_id', 'scene_title', 'file_path', 'file_directory', 'file_name', 'new_leaf')
$outLines = New-Object System.Collections.Generic.List[string]
$outLines.Add(($colNames -join $Delimiter))
foreach ($r in $rows) {
    $cells = foreach ($name in $colNames) {
        $v = $r.$name
        if ($null -ne $v) { $v = [string]$v }
        Escape-StashCsvField -Value $v -Delim $Delimiter
    }
    $outLines.Add(($cells -join $Delimiter))
}

$utf8BOM = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines($OutFile, $outLines, $utf8BOM)

Write-Host "Done: $OutFile ($($rows.Count) rows). Edit new_leaf in Excel, run gui_file_tools.py (Tab 3), or use .\apply_stash_file_renames.ps1 with -SuffixBeforeExt / -Prefix. Then run Stash Tasks -> Scan."
