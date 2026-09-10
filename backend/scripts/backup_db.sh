#!/bin/bash
# Cartify Automated PostgreSQL Backup Script
# Retention: 7 days
# Format: Custom directory-friendly compressed SQL dump

set -e

BACKUP_DIR="${BACKUP_DIR:-/backups/cartify}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/cartify_db_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-cartify}"
PGDATABASE="${PGDATABASE:-cartify_db}"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting backup for database: ${PGDATABASE}..."

pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" --no-owner --clean | gzip -9 > "${BACKUP_FILE}"

if [ $? -eq 0 ] && [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup completed successfully: ${BACKUP_FILE} (${SIZE})"
else
    echo "[$(date)] ERROR: Backup failed!" >&2
    exit 1
fi

echo "[$(date)] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "cartify_db_*.sql.gz" -mtime +${RETENTION_DAYS} -exec rm -f {} \;

echo "[$(date)] Backup maintenance routine complete."
