# Apache Polaris (Iceberg REST Catalog)

이 프로젝트는 Apache Polaris를 사용하여 Iceberg REST Catalog를 구축하고, 메타데이터 저장을 위한 PostgreSQL 및 데이터 스토리지를 위한 MinIO(S3)를
연동하는 Docker Compose 환경을 제공합니다.

## 시스템 구성 (Architecture)

---

Polaris: Apache Iceberg용 오픈 소스 REST 카탈로그 서버입니다.
PostgreSQL: Polaris의 엔티티 및 권한 메타데이터를 저장하는 영속성 계층(Relational JDBC)입니다.
MinIO: Iceberg 테이블의 실제 데이터가 저장되는 S3 호환 스토리지입니다.
polaris-setup: 컨테이너 실행 시 자동으로 카탈로그 생성, Principal 생성, 권한 부여를 수행하는 초기화 스크립트입니다.

## 사전 준비 (Prerequisites)

---

Polaris 인증 및 토큰 브로커 기능을 위해 RSA 키 쌍이 필요합니다. 아래 스크립트를 사용하여 키를 생성하세요.

```bash
# platform/polaris/rsa 디렉토리에서 실행
cd rsa
./generate_key.sh
```

## 환경 설정 (.env)

---

`.env` 파일을 통해 데이터베이스 정보, Polaris 관리자 계정, S3 연결 정보를 관리합니다.

```env
# Postgres 설정
POSTGRES_DB=catalog
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin

# Polaris 관리자 설정
POLARIS_REALM=default
ROOT_CLIENT_ID=root
ROOT_CLIENT_SECRET=polarisadmin

# MinIO (S3) 접속 정보
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# Catalog 설정
CATALOG_NAME=polaris
CATALOG_WAREHOUSE=s3://datalake/iceberg-warehouse
CATALOG_S3_ENDPOINT=http://minio-server:9000
```

## 실행 방법

---

Docker Compose를 사용하여 전체 스택을 실행합니다.

```bash
docker compose up -d
```

## 사용 가이드

---

### Spark SQL 연동

`polaris-setup` 로그에서 출력된 `USER_CLIENT_ID`와 `USER_CLIENT_SECRET`을 사용하여 접속합니다.

```bash
spark-sql \
 --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
 --conf spark.sql.catalog.polaris=org.apache.iceberg.spark.SparkCatalog \
 --conf spark.sql.defaultCatalog=polaris \
 --conf spark.sql.catalog.polaris.type=rest \
 --conf spark.sql.catalog.polaris.warehouse=$CATALOG_NAME \
 --conf spark.sql.catalog.polaris.uri=http://polaris:8181/api/catalog \
 --conf spark.sql.catalog.polaris.credential=$USER_CLIENT_ID:$USER_CLIENT_SECRET \
 --conf spark.sql.catalog.polaris.scope=PRINCIPAL_ROLE:ALL \
 --conf spark.sql.catalog.polaris.s3.endpoint=$CATALOG_S3_ENDPOINT \
 --conf spark.sql.catalog.polaris.s3.path-style-access=true \
 --conf spark.sql.catalog.polaris.s3.access-key-id=AWS_ACCESS_KEY_ID \
 --conf spark.sql.catalog.polaris.s3.secret-access-key=AWS_SECRET_ACCESS_KEY \
 --conf spark.sql.catalog.polaris.client.region=irrelevant
```

### REST API 테스트

토큰을 발급받아 네임스페이스를 생성하는 예시입니다.

```bash
# 1. 토큰 발급
export TOKEN=$(curl -s -X POST http://localhost:8181/api/catalog/v1/oauth/tokens \
  -H "Polaris-Realm: $REALM" \
  -d "grant_type=client_credentials" \
  -d "client_id=<USER_CLIENT_ID>" \
  -d "client_secret=<USER_CLIENT_SECRET>" \
  -d "scope=PRINCIPAL_ROLE:ALL" | jq -r '.access_token')

# 2. 네임스페이스 생성
curl -X POST http://localhost:8181/api/catalog/v1/polaris/namespaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Polaris-Realm: $REALM" \
  -H "Content-Type: application/json" \
  -d '{"namespace": ["namespace1"], "properties": {}}'
```

## 주요 엔드포인트

---

Iceberg REST API: `http://localhost:8181/api/catalog/v1`
Management API: `http://localhost:8181/api/management/v1`
Health Check: `http://localhost:8182/q/health`
Metrics: `http://localhost:8182/q/metrics`
