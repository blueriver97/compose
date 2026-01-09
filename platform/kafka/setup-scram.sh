#!/bin/bash

# 1. 컨테이너 내부에 임시 클라이언트 설정 파일 생성
# SSL 설정을 포함하여 kafka-configs가 브로커에 접속할 수 있게 함
bash -c "cat <<EOF > /tmp/admin-config.properties
security.protocol=SSL
ssl.truststore.location=/etc/kafka/secrets/truststore.jks
ssl.truststore.password=changeit
ssl.keystore.location=/etc/kafka/secrets/kafka.keystore.jks
ssl.keystore.password=changeit
ssl.key.password=changeit
EOF"

echo "Starting SCRAM user creation with SSL..."

# 2. --command-config 옵션을 사용하여 계정 생성
# 각 명령어는 동일한 설정 파일을 참조함
USERS=("broker" "schemaregistry" "client")
PASSWORDS=("broker" "schemaregistry" "client")

for i in "${!USERS[@]}"; do
  echo "Creating user: ${USERS[$i]}"
  kafka-configs \
    --bootstrap-server broker:19092 \
    --command-config /tmp/admin-config.properties \
    --alter \
    --add-config "SCRAM-SHA-256=[password=${PASSWORDS[$i]}]" \
    --entity-type users \
    --entity-name "${USERS[$i]}"
done

# 3. 보안을 위해 임시 파일 삭제
rm /tmp/admin-config.properties

echo "All SCRAM users created successfully."
