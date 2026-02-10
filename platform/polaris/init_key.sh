#!/usr/bin/env bash

# secret 디렉토리가 없으면 생성, 있으면 무시
mkdir -p secret

# Polaris Token-broker key files
openssl genrsa -out secret/private-key.pem 2048
openssl rsa -in secret/private-key.pem -pubout -out secret/public-key.pem
chmod -R 0644 secret/*.pem

# Trino Login User/Password
# touch secret/password.db
# htpasswd -b -B -C 10 secret/password.db trino trinoadmin

# Trino SSL key files
# openssl genrsa -out secret/server.key 2048
# openssl req -new -key secret/server.key -out secret/server.csr -config trino-config/san.cnf
# openssl x509 -req -days 3650 -in secret/server.csr -signkey secret/server.key -out secret/server.crt
# openssl pkcs12 -export -out secret/keystore.p12 -inkey secret/server.key -in secret/server.crt -passout pass:password1! -name "localhost"
