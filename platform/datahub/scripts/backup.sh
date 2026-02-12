#!/bin/bash

# 백업 경로 및 파일명 설정
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./datahub_backup_$BACKUP_DATE"
mkdir -p "$BACKUP_DIR"

echo "Starting DataHub backup..."

# 1. GMS 컨테이너에서 FERNET_KEY 추출
# Secret 복호화에 필수적인 키입니다.
echo "Extracting Fernet Key..."
docker exec datahub-gms env | grep DATAHUB_SECRET_STATE_MANAGER_FERNET_KEY > "$BACKUP_DIR/fernet_key.txt"

if [ $? -eq 0 ]; then
    echo "Successfully backed up Fernet Key."
else
    echo "Error: Failed to extract Fernet Key."
fi

# 2. MySQL 데이터베이스 덤프
# metadata_aspect_v2 테이블에 Secret이 암호화되어 저장됩니다.
echo "Dumping MySQL database..."
# 환경에 따라 컨테이너명(mysql)과 DB명(datahub)을 수정하십시오.
docker exec mysql /usr/bin/mysqldump -u datahub -pdatahub datahub > "$BACKUP_DIR/datahub_db_dump.sql"

if [ $? -eq 0 ]; then
    echo "Successfully backed up Database."
else
    echo "Error: Failed to dump Database."
fi

# 3. 백업 파일 압축
tar -czvf "datahub_backup_$BACKUP_DATE.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "------------------------------------------"
echo "Backup Completed: datahub_backup_$BACKUP_DATE.tar.gz"
echo "IMPORTANT: Keep the Fernet Key secure. Without it, secrets cannot be recovered."
echo "------------------------------------------"
