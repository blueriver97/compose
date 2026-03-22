#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$SCRIPT_DIR/backup/$BACKUP_DATE"
mkdir -p "$BACKUP_DIR/workflows" "$BACKUP_DIR/credentials"

echo "Starting n8n backup..."

# 1. 워크플로우 export
echo "Exporting workflows..."
docker exec n8n n8n export:workflow --all --output=/home/node/.n8n/backups/workflows/ --separate 2>/dev/null
if [ $? -eq 0 ]; then
    cp "$SCRIPT_DIR/data/n8n/backups/workflows/"*.json "$BACKUP_DIR/workflows/" 2>/dev/null
    echo "Workflows exported: $(ls "$BACKUP_DIR/workflows/" | wc -l | tr -d ' ') files"
else
    echo "Error: Failed to export workflows."
fi

# 2. Credential export (암호화 상태 유지)
echo "Exporting credentials..."
docker exec n8n n8n export:credentials --all --output=/home/node/.n8n/backups/credentials/ --separate 2>/dev/null
if [ $? -eq 0 ]; then
    cp "$SCRIPT_DIR/data/n8n/backups/credentials/"*.json "$BACKUP_DIR/credentials/" 2>/dev/null
    echo "Credentials exported: $(ls "$BACKUP_DIR/credentials/" | wc -l | tr -d ' ') files"
else
    echo "Error: Failed to export credentials."
fi

# 3. PostgreSQL 덤프
echo "Dumping PostgreSQL database..."
docker exec n8n_db pg_dump -U n8n n8n > "$BACKUP_DIR/n8n_db.sql" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Database dump completed."
else
    echo "Error: Failed to dump database."
fi

# 4. 컨테이너 내 임시 디렉토리 정리
docker exec n8n rm -rf /home/node/.n8n/backups 2>/dev/null

echo "------------------------------------------"
echo "Backup completed: $BACKUP_DIR"
echo "------------------------------------------"
