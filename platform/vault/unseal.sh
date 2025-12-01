#!/bin/bash

SECRET_FILE=".secret"

# Secret 파일이 없으면 Vault 초기화
if [ ! -f "$SECRET_FILE" ]; then
    echo "$SECRET_FILE does not exist. Initializing Vault now."
    docker exec vault vault operator init > $SECRET_FILE
    if [ $? -ne 0 ]; then
        echo "Failed to initialize Vault."
        exit 1
    fi
fi

# Secret 파일에서 키 읽기
ROOT_KEY=$(grep 'Initial Root Token:' $SECRET_FILE | awk '{print $4}')
UNSEAL_KEY1=$(grep 'Unseal Key 1:' $SECRET_FILE | awk '{print $4}')
UNSEAL_KEY2=$(grep 'Unseal Key 2:' $SECRET_FILE | awk '{print $4}')
UNSEAL_KEY3=$(grep 'Unseal Key 3:' $SECRET_FILE | awk '{print $4}')

# 키 추출 여부 확인
if [ -z "$ROOT_KEY" ] || [ -z "$UNSEAL_KEY1" ] || [ -z "$UNSEAL_KEY2" ] || [ -z "$UNSEAL_KEY3" ]; then
    echo "Failed to extract keys from $SECRET_FILE."
    exit 1
fi

# Vault 언실
echo "Unsealing Vault..."
docker exec vault vault operator unseal $UNSEAL_KEY1
if [ $? -ne 0 ]; then
    echo "Failed to unseal Vault with key 1."
    exit 1
fi

docker exec vault vault operator unseal $UNSEAL_KEY2
if [ $? -ne 0 ]; then
    echo "Failed to unseal Vault with key 2."
    exit 1
fi

docker exec vault vault operator unseal $UNSEAL_KEY3
if [ $? -ne 0 ]; then
    echo "Failed to unseal Vault with key 3."
    exit 1
fi

echo "Vault has been unsealed successfully."
