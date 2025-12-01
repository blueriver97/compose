#!/bin/bash

SECRET_FILE=".secret"

if [[ -z $VAULT_USER || -z $VAULT_PASSWORD ]]; then
  echo "No set VAULT_USER or VAULT_PASSWORD"
  exit 1
fi

# Secret 파일이 없으면 Vault 초기화
if [ ! -f "$SECRET_FILE" ]; then
    echo "Vault is not initialized. Initializing now"
    docker exec vault vault operator init > $SECRET_FILE
fi

# Secret 파일에서 키 읽기
ROOT_KEY=$(grep 'Initial Root Token:' $SECRET_FILE | awk '{print $4}')
UNSEAL_KEY1=$(grep 'Unseal Key 1:' $SECRET_FILE | awk '{print $4}')
UNSEAL_KEY2=$(grep 'Unseal Key 2:' $SECRET_FILE | awk '{print $4}')
UNSEAL_KEY3=$(grep 'Unseal Key 3:' $SECRET_FILE | awk '{print $4}')

# Vault 언실
echo "Unseal Vault"
docker exec vault vault operator unseal $UNSEAL_KEY1
docker exec vault vault operator unseal $UNSEAL_KEY2
docker exec vault vault operator unseal $UNSEAL_KEY3

# Vault 로그인
echo "Root Login Vault"
docker exec vault vault login $ROOT_KEY

# Userpass 인증 방법 활성화
ENABLE_USERPASS=$(docker exec vault vault auth list | grep "^userpass")
if [ -z "$ENABLE_USERPASS" ]; then
    echo "> Enabling Userpass"
    docker exec vault vault auth enable userpass
else
    echo "> Userpass already activated."
fi

# KV Secret Engine 활성화
echo "Activating Secret Engine..."
SECRET_ENGINE="secret"
SECRET_ENGINE_EXISTS=$(docker exec vault vault secrets list | grep "^${SECRET_ENGINE}")
if [ -z "$SECRET_ENGINE_EXISTS" ]; then
    echo "> Secret engine does not exist. Creating engine..."
    docker exec vault vault secrets enable -path=secret kv-v2
    echo "> KV Secret Engine enabled at path 'secret'."
else
    echo "> Secret Engine already exists."
fi

# 정책 생성
echo "Applying policy..."
POLICY_NAME="base-policy"
POLICY_FILE="/vault/policy/policy.hcl"
POLICY_EXISTS=$(docker exec vault vault policy list | grep "^${POLICY_NAME}$")
if [ -z "$POLICY_EXISTS" ]; then
    echo "> Policy does not exist. Creating policy..."
    docker exec vault vault policy write ${POLICY_NAME} $POLICY_FILE
else
    echo "> Policy already exists."
fi

# 유저 확인 및 생성
echo "Creating user..."
USER_EXISTS=$(docker exec vault vault list auth/userpass/users | grep "^${VAULT_USER}$")
if [ -z "$USER_EXISTS" ]; then
    echo "> User does not exist. Creating user..."
    docker exec vault vault write auth/userpass/users/${VAULT_USER} password=${VAULT_PASSWORD} policies=${POLICY_NAME}
else
    echo "> User already exists."
fi

# 정책과 사용자 연결
echo "Attaching policy to user..."
docker exec vault vault write auth/userpass/users/${VAULT_USER} policies=${POLICY_NAME}

echo "Setup completed."
