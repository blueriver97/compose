# root 계정의 정보를 사용하여 토큰 발급
export POLARIS_TOKEN=$(curl -X POST http://localhost:8181/api/catalog/v1/oauth/tokens \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Polaris-Realm: default" \
  -d "grant_type=client_credentials&client_id=root&client_secret=polarisadmin&scope=PRINCIPAL_ROLE:ALL" \
  | jq -r '.access_token')
