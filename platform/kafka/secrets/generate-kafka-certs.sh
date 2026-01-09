#!/bin/bash

# 설정 변수
PASS="changeit"
VALIDITY=3650
CA_NAME="RootCA"

echo "Starting certificate generation..."

# 1. Root CA 생성 (모든 인증서의 신뢰 기점)
openssl req -new -x509 -keyout ca-key.pem -out ca-cert.pem -days $VALIDITY -nodes -subj "/CN=$CA_NAME"

# 2. 공통 Truststore 생성 (CA 인증서 포함)
keytool -keystore truststore.jks -alias CARoot -import -file ca-cert.pem -storepass $PASS -noprompt

echo "Common truststore.jks created."

# 3. 노드별 Keystore 생성 함수 정의
generate_node_cert() {
    local NODE_NAME=$1
    local KEYSTORE="$NODE_NAME.keystore.jks"

    echo "Generating keystore for $NODE_NAME..."

    # Keystore 생성 및 개인키/인증서 생성
    keytool -genkey -keystore $KEYSTORE -alias $NODE_NAME -validity $VALIDITY -keyalg RSA -storepass $PASS -keypass $PASS \
        -dname "CN=$NODE_NAME" -ext "SAN=dns:$NODE_NAME,dns:localhost"

    # CSR (인증서 서명 요청) 생성
    keytool -keystore $KEYSTORE -certreq -file $NODE_NAME.csr -alias $NODE_NAME -storepass $PASS

    # CA를 사용하여 CSR 서명
    openssl x509 -req -CA ca-cert.pem -CAkey ca-key.pem -in $NODE_NAME.csr \
        -out $NODE_NAME-ca-signed.crt -days $VALIDITY -CAcreateserial

    # CA 인증서를 Keystore에 가져오기 (인증 체인 구성)
    keytool -keystore $KEYSTORE -alias CARoot -import -file ca-cert.pem -storepass $PASS -noprompt

    # 서명된 노드 인증서를 Keystore에 가져오기
    keytool -keystore $KEYSTORE -alias $NODE_NAME -import -file $NODE_NAME-ca-signed.crt -storepass $PASS -noprompt

    # 임시 CSR 파일 삭제
    rm $NODE_NAME.csr $NODE_NAME-ca-signed.crt
}

# 4. 각 노드별 인증서 생성 (Controller, Broker)
generate_node_cert "controller"
generate_node_cert "broker"
generate_node_cert "client"

# 5. 클라이언트용 Truststore 복사 (구분 편의성)
# cp truststore.jks client.truststore.jks

echo "All certificates generated"
