# backup.ps1 - Heimnetz backup script

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "./backup/$timestamp"
$backupSql = "$backupDir/heimnetz.sql"
$backupZip = "./backup/heimnetz_backup_$timestamp.zip"
$logFile = "./backup/backup.log"

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Dump MariaDB database
& mysqldump.exe -u user -ppassword heimnetz > $backupSql

# Copy config files
Copy-Item -Path "./config/*" -Destination $backupDir -Recurse -Force

# Compress backup
Compress-Archive -Path $backupDir/* -DestinationPath $backupZip

# Log result
Add-Content -Path $logFile -Value "$(Get-Date): Backup completed - $backupZip"
Write-Host "Backup completed: $backupZip"
