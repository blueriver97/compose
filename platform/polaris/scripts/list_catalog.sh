curl -X GET http://localhost:8181/api/management/v1/catalogs \
  -H "Authorization: Bearer $POLARIS_TOKEN" \
  -H "Polaris-Realm: default" \
  | jq
