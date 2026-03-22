#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 인자로 백업 디렉토리 지정
BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    # 인자 없으면 가장 최근 백업 사용
    BACKUP_DIR=$(ls -td "$SCRIPT_DIR/backup/"*/ 2>/dev/null | head -1)
    if [ -z "$BACKUP_DIR" ]; then
        echo "Error: No backup found. Usage: $0 [backup_dir]"
        exit 1
    fi
fi

echo "Restoring from: $BACKUP_DIR"

# 1. PostgreSQL 복원
if [ -f "$BACKUP_DIR/n8n_db.sql" ]; then
    echo "Restoring database..."
    docker exec -i n8n_db psql -U n8n -d n8n < "$BACKUP_DIR/n8n_db.sql" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Database restored."
    else
        echo "Error: Failed to restore database."
    fi
fi

# 2. 워크플로우 import
if [ -d "$BACKUP_DIR/workflows" ] && [ "$(ls "$BACKUP_DIR/workflows/"*.json 2>/dev/null)" ]; then
    echo "Importing workflows..."
    docker cp "$BACKUP_DIR/workflows" n8n:/home/node/.n8n/restore_workflows
    docker exec n8n n8n import:workflow --input=/home/node/.n8n/restore_workflows/ --separate 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Workflows imported."
    else
        echo "Error: Failed to import workflows."
    fi
    docker exec n8n rm -rf /home/node/.n8n/restore_workflows 2>/dev/null
fi

# 3. Credential import
if [ -d "$BACKUP_DIR/credentials" ] && [ "$(ls "$BACKUP_DIR/credentials/"*.json 2>/dev/null)" ]; then
    echo "Importing credentials..."
    docker cp "$BACKUP_DIR/credentials" n8n:/home/node/.n8n/restore_credentials
    docker exec n8n n8n import:credentials --input=/home/node/.n8n/restore_credentials/ --separate 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Credentials imported."
    else
        echo "Error: Failed to import credentials."
    fi
    docker exec n8n rm -rf /home/node/.n8n/restore_credentials 2>/dev/null
fi

echo "------------------------------------------"
echo "Restore completed. Restart n8n to apply:"
echo "  docker compose restart n8n"
echo "------------------------------------------"
