# AgriPredict backup for Windows (PowerShell)
# Dumps data + tables + stored procedures, functions, triggers and events,
# compresses it to .zip, verifies it, and keeps the newest N backups.
#
# Usage (PowerShell):
#   $env:DB_PASSWORD = 'yourpass'
#   .\backup_agripredict.ps1
# Optional parameters:
#   .\backup_agripredict.ps1 -DbUser root -DbName agripredict -BackupDir .\backups -Keep 7
#
# If mysqldump is not found, add MySQL's bin folder to PATH, e.g.
#   $env:Path += ';C:\Program Files\MySQL\MySQL Server 8.0\bin'
# If PowerShell blocks the script:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

param(
  [string]$DbName    = 'agripredict',
  [string]$DbHost    = 'localhost',
  [string]$DbUser    = 'root',
  [string]$BackupDir = '.\backups',
  [int]   $Keep      = 7
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command mysqldump -ErrorAction SilentlyContinue)) {
  throw "mysqldump not found. Add MySQL's bin folder to PATH (see the comments at the top of this script)."
}

# Password via environment so it does not show in the process list
if ($env:DB_PASSWORD) { $env:MYSQL_PWD = $env:DB_PASSWORD }

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$stamp   = Get-Date -Format 'yyyyMMdd_HHmmss'
$sqlFile = Join-Path $BackupDir "${DbName}_$stamp.sql"
$zipFile = Join-Path $BackupDir "${DbName}_$stamp.zip"

# --result-file writes the dump as UTF-8 bytes (avoids PowerShell's UTF-16 redirection problem,
# which would corrupt the Marathi/Hindi text)
& mysqldump -h $DbHost -u $DbUser `
  --single-transaction --routines --triggers --events `
  --default-character-set=utf8mb4 `
  --result-file=$sqlFile $DbName
if ($LASTEXITCODE -ne 0) { throw "mysqldump failed (exit code $LASTEXITCODE)" }

# Verify the dump finished
$tail = Get-Content -Path $sqlFile -Tail 5 -Encoding UTF8
if (-not ($tail -match 'Dump completed')) {
  Remove-Item $sqlFile -Force
  throw 'Backup verification FAILED: dump is incomplete.'
}

Compress-Archive -Path $sqlFile -DestinationPath $zipFile -Force
Remove-Item $sqlFile -Force
$sizeKb = [math]::Round((Get-Item $zipFile).Length / 1KB, 1)
Write-Host "Backup OK: $zipFile ($sizeKb KB)"

# Retention: keep only the newest $Keep backups
Get-ChildItem -Path $BackupDir -Filter "${DbName}_*.zip" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip $Keep |
  ForEach-Object { Remove-Item $_.FullName -Force; Write-Host "Removed old backup: $($_.Name)" }

# ---- Restore ----
#   Expand-Archive .\backups\agripredict_YYYYMMDD_HHMMSS.zip -DestinationPath .\restore
#   mysql -u root -p -e "CREATE DATABASE agripredict_restore CHARACTER SET utf8mb4;"
#   Get-Content .\restore\agripredict_YYYYMMDD_HHMMSS.sql -Raw -Encoding UTF8 | mysql -u root -p agripredict_restore
#   (If that is slow or garbles text, use:  mysql -u root -p agripredict_restore < .\restore\file.sql  from cmd.exe)
#
# ---- Schedule daily at 2 AM (Task Scheduler) ----
#   schtasks /Create /SC DAILY /ST 02:00 /TN "AgriPredict Backup" /TR "powershell -ExecutionPolicy Bypass -File C:\path\to\backup_agripredict.ps1"
