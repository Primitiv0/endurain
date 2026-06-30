$WeblateUrl = "https://translate.codeberg.org"
$ProjectSlug = "endurain"                  # change if your project slug differs
$Token = "wlp_or_wlu_token_here"           # project/user API token
$Repo = "https://codeberg.org/endurain-project/endurain.git"
$Branch = "pre-release"
$PushBranch = "pre-release"
$DryRun = $true                            # set to $false to actually create
$DebugMode = $true                         # set to $false to reduce output
$PurgeJsonComponentsFirst = $true         # set to $true to delete existing git/json-nested components first
$License = "AGPL-3.0-only"
$LicenseUrl = "https://spdx.org/licenses/AGPL-3.0-only.html"

# Resolve paths relative to script location so this works from any cwd.
$RepoRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  try {
    $RepoRoot = (git rev-parse --show-toplevel).Trim()
  }
  catch {
    $RepoRoot = (Resolve-Path ".").Path
  }
}
$BaseDir = Join-Path $RepoRoot "frontend/src/i18n/us"

$Headers = @{
  Authorization = "Token $Token"
  "Content-Type" = "application/json"
}

function Get-ExistingComponentsMap {
  $map = @{}
  $nextPage = "$WeblateUrl/api/projects/$ProjectSlug/components/?page_size=1000"
  while ($nextPage) {
    $resp = Invoke-RestMethod -Method GET -Uri $nextPage -Headers @{ Authorization = "Token $Token" }
    foreach ($c in $resp.results) { $map[$c.slug] = $c }
    $nextPage = $resp.next
  }
  return $map
}

# Existing components keyed by slug for update/skip decisions.
$existing = Get-ExistingComponentsMap

if ($PurgeJsonComponentsFirst) {
  foreach ($component in $existing.Values) {
    if ($component.vcs -eq "git" -and $component.file_format -eq "json-nested") {
      if ($DryRun) {
        Write-Host "DRYRUN delete component: $($component.slug)"
        continue
      }

      try {
        $componentSlug = [uri]::EscapeDataString($component.slug)
        Invoke-RestMethod -Method DELETE -Uri "$WeblateUrl/api/components/$ProjectSlug/$componentSlug/" -Headers @{ Authorization = "Token $Token" }
        Write-Host "DELETED component: $($component.slug)"
      }
      catch {
        Write-Host "FAILED delete component: $($component.slug)"
        Write-Host $_.Exception.Message
      }
    }
  }

  # Refresh after purge, so create/update decisions are accurate.
  $existing = Get-ExistingComponentsMap
}

$files = Get-ChildItem -Path $BaseDir -Recurse -File -Filter "*.json"

$repoRootResolved = (Resolve-Path $RepoRoot).Path
$repoRootWithSep = $repoRootResolved.TrimEnd('\') + "\"

if ($DebugMode) {
  Write-Host "DEBUG repoRootResolved=$repoRootResolved"
  Write-Host "DEBUG baseDir=$BaseDir"
}

foreach ($f in $files) {
  $fullPath = (Resolve-Path $f.FullName).Path
  if (-not $fullPath.StartsWith($repoRootWithSep, [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "WARN source path is outside repo root. Skipping file."
    if ($DebugMode) {
      Write-Host "DEBUG fullPath=$fullPath"
      Write-Host "DEBUG repoRootWithSep=$repoRootWithSep"
    }
    continue
  }

  $rel = $fullPath.Substring($repoRootWithSep.Length) -replace "\\", "/"

  if ($rel -notmatch "^frontend/src/i18n/us/") {
    Write-Host "WARN unexpected relative path. Skipping file."
    if ($DebugMode) {
      Write-Host "DEBUG fullName=$fullPath"
      Write-Host "DEBUG rel=$rel"
    }
    continue
  }

  $mask = $rel -replace "/us/", "/*/"
  $name = [System.IO.Path]::GetFileNameWithoutExtension($rel)
  $slug = $name

  $desired = @{
    name        = $name
    slug        = $slug
    vcs         = "git"
    repo        = $Repo
    branch      = $Branch
    push_branch = $PushBranch
    file_format = "json-nested"
    filemask    = $mask
    template    = $rel
    new_base    = $rel
    license     = $License
    license_url = $LicenseUrl
  }

  if ($existing.ContainsKey($slug)) {
    $current = $existing[$slug]
    $needsUpdate = (
      $current.name -ne $desired.name -or
      $current.repo -ne $desired.repo -or
      $current.branch -ne $desired.branch -or
      $current.push_branch -ne $desired.push_branch -or
      $current.vcs -ne $desired.vcs -or
      $current.file_format -ne $desired.file_format -or
      $current.filemask -ne $desired.filemask -or
      $current.template -ne $desired.template -or
      $current.license -ne $desired.license -or
      $current.license_url -ne $desired.license_url
    )

    if (-not $needsUpdate) {
      Write-Host "SKIP existing (already aligned): $slug"
      continue
    }

    $patchBody = @{
      name        = $desired.name
      repo        = $desired.repo
      branch      = $desired.branch
      push_branch = $desired.push_branch
      vcs         = $desired.vcs
      file_format = $desired.file_format
      filemask    = $desired.filemask
      template    = $desired.template
      new_base    = $desired.new_base
      license     = $desired.license
      license_url = $desired.license_url
    } | ConvertTo-Json -Depth 10

    if ($DryRun) {
      Write-Host "DRYRUN update: $slug | template=$rel | mask=$mask"
      continue
    }

    try {
      $componentSlug = [uri]::EscapeDataString($slug)
      $updated = Invoke-RestMethod -Method PATCH -Uri "$WeblateUrl/api/components/$ProjectSlug/$componentSlug/" -Headers $Headers -Body $patchBody
      Write-Host "UPDATED: $($updated.slug)"
    }
    catch {
      Write-Host "FAILED update: $slug"
      Write-Host $_.Exception.Message
      if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
        Write-Host "DEBUG API response:"
        Write-Host $_.ErrorDetails.Message
      }
      if ($DebugMode) {
        Write-Host "DEBUG patch payload:"
        Write-Host $patchBody
      }
    }
    continue
  }

  $body = $desired | ConvertTo-Json -Depth 10

  if ($DryRun) {
    Write-Host "DRYRUN create: $slug | template=$rel | mask=$mask"
    continue
  }

  try {
    $created = Invoke-RestMethod -Method POST -Uri "$WeblateUrl/api/projects/$ProjectSlug/components/" -Headers $Headers -Body $body
    Write-Host "CREATED: $($created.slug)"
  }
  catch {
    Write-Host "FAILED: $slug"
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
      Write-Host "DEBUG API response:"
      Write-Host $_.ErrorDetails.Message
    }
    if ($DebugMode) {
      Write-Host "DEBUG create payload:"
      Write-Host $body
      Write-Host "DEBUG source file: $($f.FullName)"
      Write-Host "DEBUG rel=$rel"
      Write-Host "DEBUG mask=$mask"
    }
  }
}