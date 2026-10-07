#!/usr/bin/env bash
# AgriPredict backup (Linux / macOS / Git Bash)
# Dumps data + tables + stored procedures, functions, triggers and events,
# compresses it, and keeps the newest N backups.
#
# Usage:   DB_USER=root DB_PASSWORD='yourpass' ./backup_agripredict.sh
# Options (environment variables):
#   DB_NAME      database name            (default: agripredict)
#   DB_HOST      host                     (default: localhost)
#   BACKUP_DIR   where to store backups   (default: ./backups)
#   KEEP         how many backups to keep (default: 7)
set -euo pipefail

DB_NAME="${DB_NAME:-agripredict}"
DB_HOST="${DB_HOST:-localhost}"
DB_USER="${DB_USER:-root}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP="${KEEP:-7}"

# Pass the password through the environment so it does not appear in `ps` output
if [ -n "${DB_PASSWORD:-}" ]; then export MYSQL_PWD="$DB_PASSWORD"; fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/${DB_NAME}_${STAMP}.sql.gz"

# --single-transaction : consistent snapshot without locking tables (InnoDB)
# --routines/--triggers/--events : include procedures, functions, triggers, scheduler events
DUMP="mysqldump"
command -v mysqldump >/dev/null 2>&1 || DUMP="mariadb-dump"

"$DUMP" -h "$DB_HOST" -u "$DB_USER" \
  --single-transaction --routines --triggers --events \
  --default-character-set=utf8mb4 "$DB_NAME" | gzip > "$OUT"

# Verify the file is a non-empty, complete dump
if ! gzip -t "$OUT" || ! gunzip -c "$OUT" | tail -n 5 | grep -q "Dump completed"; then
  echo "Backup verification FAILED: $OUT" >&2
  exit 1
fi
echo "Backup OK: $OUT ($(du -h "$OUT" | cut -f1))"

# Retention: delete everything except the newest $KEEP backups
ls -1t "$BACKUP_DIR"/${DB_NAME}_*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r old; do
  rm -f "$old"
  echo "Removed old backup: $old"
done

# ---- Restore (into the same or a new database) ----
#   mysql -u root -p -e "CREATE DATABASE agripredict_restore CHARACTER SET utf8mb4;"
#   gunzip -c backups/agripredict_YYYYMMDD_HHMMSS.sql.gz | mysql -u root -p agripredict_restore
# ---- Schedule daily at 2 AM (Linux/macOS crontab -e) ----
#   0 2 * * * DB_USER=root DB_PASSWORD='yourpass' /path/to/backup_agripredict.sh >> /path/to/backup.log 2>&1
