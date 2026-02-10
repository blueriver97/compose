# Apache Polaris (Iceberg REST Catalog)

이 프로젝트는 Apache Polaris를 사용하여 Iceberg REST Catalog를 구축하고, 메타데이터 저장을 위한 PostgreSQL 및 데이터 스토리지를 위한 MinIO(S3)를
연동하는 Docker Compose 환경을 제공합니다. 또한 데이터 분석을 위한 Trino 및 Spark 연동 설정을 포함합니다.

## 시스템 구성 (Architecture)

---

postgresql: Polaris의 엔티티 및 권한 메타데이터를 저장하는 영속성 계층(Relational JDBC)입니다.
polaris: Apache Iceberg용 오픈 소스 REST 카탈로그 서버입니다.
polaris-bootstrap: relational-jdbc 모드 사용 시 필요한 초기 DB 스키마와 루트 관리자(Realm) 정보를 생성합니다.
polaris-setup: 컨테이너 실행 시 자동으로 카탈로그 생성, Principal 생성, 권한 부여를 수행하는 초기화합니다.
trino: polaris 카탈로그를 거쳐 데이터 조회를 수행하는 쿼리 엔진입니다.

#### 해당 환경에서는 Polaris의 Credential vending을 사용합니다.

보안 강화를 위해 클라이언트가 스토리지(MinIO)의 인증을 직접 관리하지 않고, Polaris로부터 일시적으로 위임 받아 처리합니다.
이 방법은 클라이언트에게 S3 키를 공개하지 않아도 된다는 장점이 있습니다.

#### Credential vending 및 보안 워크플로우는 다음과 같은 순서로 진행됩니다.

1. OAuth2 기반 인증: 클라이언트는 Principal 자격 증명을 통해 Polaris 토큰 엔드포인트에서 JWT를 발급받습니다.
2. 접근 위임 (Access Delegation):
   - Spark 설정에서 `X-Iceberg-Access-Delegation=vended-credentials` 옵션을 활성화하면 Polaris가 MinIO와 통신하여 해당 테이블 작업에 필요한 임시 자격
     증명을
     생성합니다.
   - 클라이언트는 Polaris가 제공한 임시 권한을 사용해 Minio에 접근합니다.
3. RBAC 기반 권한 제어: admin_role 및 catalog_role을 통해 테이블 수준의 읽기/쓰기 권한을 정밀하게 제어합니다.

#### 데이터 분석 계층 (Query Engine)은 다음과 같이 연동됩니다.

1. Trino 연동: HTTPS(8443 포트) 통신과 PASSWORD 인증을 적용하여 보안 채널을 형성합니다.
   - iceberg.rest-catalog.vend-credentials-enabled=true 설정을 통해 Polaris로부터 권한을 위임받아 쿼리를 수행합니다.
2. Spark 연동: Spark 전용 iceberg Catalog 확장을 통해 Polaris REST 인터페이스와 직접 통신하며, OAuth2를 통한 토큰 갱신 기능을 지원합니다.

## 사전 준비 (Prerequisites)

---

1. 스토리지 용도로 사용되는 MinIO는 별도로 구성해야 합니다. [minio](../minio)
2. Polaris 인증 및 토큰 브로커 기능을 위해 RSA 키 쌍이 필요합니다. 아래 스크립트를 사용하여 키를 생성하세요.

```bash
./init_key.sh
```

- 생성되는 파일:
  - (Polaris용) private-key.pem, public-key.pem
  - (Trino용) keystore.p12, password.db
- Trino 기본 계정: trino / trinoadmin

## 환경 설정 (.env)

---

`.env` 파일을 통해 데이터베이스 정보, Polaris 관리자 계정, S3 연결 정보를 관리합니다.

```env
# Postgres 설정
POSTGRES_DB=catalog
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin

# Polaris 설정
POLARIS_REALM=default
ROOT_CLIENT_ID=root
ROOT_CLIENT_SECRET=polarisadmin

# MinIO/S3 연결 정보
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_ENDPOINT_URL_S3=http://minio-server:9000
AWS_ENDPOINT_URL_STS=http://minio-server:9000

# Iceberg Catalog 설정
CATALOG_NAME=polaris
CATALOG_WAREHOUSE=s3://datalake/iceberg
```

#### 주의 사항

1. 현재 Trino의 커스텀 헤더 추가가 지원되지 않아 `polaris.realm-context.require-header`가 false로 설정되어 있습니다.
   이는 운영 환경에서 멀티 테넌시(Multi-tenancy)를 적용할 경우 보안 홀이 될 수 있습니다.

## 실행 방법

---

Docker Compose를 사용하여 전체 스택을 실행합니다.

```bash
docker compose up -d

# 초기화 로그 확인 (setup 완료 여부)
docker logs -f polaris-setup
```

## 사용 가이드

---

### Spark SQL 연동

`polaris-setup` 로그에서 출력된 `USER_CLIENT_ID`와 `USER_CLIENT_SECRET`을 사용하여 접속합니다.

```bash
spark-sql \
    --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
    --conf spark.sql.defaultCatalog=polaris \
    --conf spark.sql.catalog.polaris=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.polaris.type=rest \
    --conf spark.sql.catalog.polaris.warehouse=polaris \
    --conf spark.sql.catalog.polaris.uri=http://polaris:8181/api/catalog \
    --conf spark.sql.catalog.polaris.oauth2-server-uri=http://polaris:8181/api/catalog/v1/oauth/tokens \
    --conf spark.sql.catalog.polaris.header.Polaris-Realm=default \
    --conf spark.sql.catalog.polaris.header.X-Iceberg-Access-Delegation=vended-credentials \
    --conf spark.sql.catalog.polaris.credential=0ad89a1802bc76fd:0faf3da66f732c8c3b6acb4f675c2f53 \
    --conf spark.sql.catalog.polaris.scope=PRINCIPAL_ROLE:ALL \
    --conf spark.sql.catalog.polaris.token-refresh-enabled=true
```

### Trino 연동 (HTTP)

- 단순하게 HTTP 기반으로 통신하려는 경우, 8080 포트를 사용해야 하며 별도의 인증 없이 사용합니다.
- 이 경우 JDBC 설정에 `user` property를 통해 유저명을 입력해야 합니다.
  (PyCharm 연결 시, `No Auth` 선택 후 `Advanced` 탭에서 `user` 속성 추가 필요)

### Trino 연동 (HTTPS)

- Trino는 Password 기반의 인증을 활성화하는 경우 SSL(HTTPS) 활성화가 강제됩니다.
- HTTPS 사용 시, keystore.p12을 사용하며 Client Key Password는 \*.p12 파일 생성에 사용된 비밀 값을 의미합니다.

```yaml
Endpoint: https://localhost:8443
User: trino
Password: trinoadmin
CA File: server.crt
Client Certificate File: server.crt
Client Key File: server.key
Client Key Password: password1!
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
