# MinIO Object Storage

이 디렉토리는 S3 호환 객체 스토리지인 MinIO를 구축하고 관리하기 위한 설정입니다.

S3를 대체하여 데이터 레이크, 로그 아카이빙, 또는 애플리케이션의 파일 저장소로 활용할 수 있습니다.

## 1. 아키텍처 및 구성 요소 (Components)

---

`docker compose`를 통해 다음 두 가지 서비스가 실행됩니다.

| 서비스명 | 역할            | 설명                                                                                               |
| :------- | :-------------- | :------------------------------------------------------------------------------------------------- |
| minio    | 스토리지 서버   | S3 API 호환 스토리지 엔진 및 Web Console 제공                                                      |
| minio-mc | 초기화 유틸리티 | 컨테이너 실행 시 `.env`에 정의된 버킷을 자동으로 생성하고 종료되는 일회성 컨테이너 (`mc` CLI 사용) |

## 2. 설정 (Configuration)

---

환경 설정은 `.env` 파일에서 관리합니다.

### 주요 환경 변수

| 변수명                       | 설명                                         | 기본값                                |
| :--------------------------- | :------------------------------------------- | :------------------------------------ |
| `MINIO_ROOT_USER`            | 관리자 ID (AWS Access Key 역할)              | (사용자 지정)                         |
| `MINIO_ROOT_PASSWORD`        | 관리자 비밀번호 (AWS Secret Key 역할)        | (사용자 지정)                         |
| `MINIO_API_PORT`             | S3 API 호환 포트 (코드 연동용)               | `9000`                                |
| `MINIO_CONSOLE_PORT`         | Web Console 포트 (브라우저 접속용)           | `9001`                                |
| `MINIO_DEFAULT_BUCKETS`      | 자동 생성할 버킷 목록 (쉼표로 구분)          | `datalake`                            |
| `MINIO_ALIAS`                | mc 명령어에서 사용할 MinIO 서버 별칭         | `myminio`                             |
| `MINIO_BROWSER_REDIRECT_URL` | 리버스 프록시 사용 시, MinIO 리다이렉션 주소 | `https://blueriver.ddns.net/minio/ui` |

### 데이터 저장 (Persisting Data)

- 데이터는 Docker Volume minio_data에 저장됩니다.
- 컨테이너를 재시작해도 데이터는 유지되지만, 볼륨을 삭제(docker compose down -v)하면 데이터가 초기화됩니다.

## 3. 실행 및 접속 (Usage)

---

### 실행 방법

```bash
cd platform/minio
docker compose up -d
```

## 4. 사용 예시 (Examples)

---

### 테스트

- [test.py](test.py) 스크립트는 PySpark를 사용하여 MinIO에 Apache Iceberg 포맷으로 데이터를 쓰고 읽는 예제입니다.
- 아래 의존성 설치가 필요합니다.

  ```bash
  pip install pyspark pydantic pydantic-settings
  ```

- MinIO 컨테이너가 실행 중인 상태에서 아래 명령어를 수행합니다.

  ```bash
  python test.py
  ```

### 주요 설정

- MinIO를 로컬 S3로 사용하기 위해 Spark 설정 시 다음 옵션이 중요합니다. (test.py 참고)

- Path Style Access: true로 설정해야 DNS 해결 오류 없이 localhost 도메인을 사용할 수 있습니다.

  ```python
  .config("spark.hadoop.fs.s3a.path.style.access", "true")
  ```

- Endpoint: MinIO의 API 포트(9000)를 바라봐야 합니다.

  ```python
  .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
  ```

- Warehouse Path: `s3a://` 프로토콜을 사용합니다.

  ```python
  .config("spark.sql.catalog.local.warehouse", "s3a://datalake/iceberg-warehouse")
  ```

### 사용자 생성

```bash
# 예시: mc admin user add <alias> <ACCESS_KEY> <SECRET_KEY>
docker exec minio_mc mc admin user add myminio newuser newpassword123
docker exec minio_mc mc admin policy attach myminio readwrite --user newuser
docker exec minio_mc mc admin user list myminio
```

- Admin 계정을 사용하기 보다 일반 사용자 계정 사용을 권장합니다.

### 버킷 생성 / 삭제

```bash
docker exec minio_mc mc mb myminio/datalake
docker exec minio_mc mc rb myminio/datalake

# 객체 잠금(Object Locking) 기능을 활성화
docker exec minio_mc mc mb --region us-east-1 --with-lock myminio/datalake

# 버킷 강제 삭제
docker exec minio_mc mc rb --force myminio/datalake
```

#### 객체 잠금 (Object Locking)이란?

- 객체 잠금 활성화: 이 옵션을 사용하여 버킷을 생성하면, 이후 해당 버킷에 저장되는 객체들에 대해 "일정 기간 동안 수정하거나 삭제할 수 없는" 정책을 적용할 수 있음.
- 버저닝(Versioning) 강제: 객체 잠금 기능은 객체의 버전 관리에 의존
- 비가역적 설정: 일반적으로 버킷 생성 시에만 설정할 수 있으며, 한 번 활성화된 버킷의 객체 잠금 기능은 비활성화하기 어려움.

#### 잠금 모드 (Retention Modes)란?

이 옵션으로 생성된 버킷은 추후 객체별 또는 기본 정책으로 두 가지 유형의 잠금을 설정할 수 있습니다.

- GOVERNANCE 모드 (거버넌스 모드)
  - 실수로 인한 삭제 방지, 내부 보안 정책 준수용.
  - 대부분의 사용자는 객체를 삭제/수정할 수 없지만, 특수 권한(s3:BypassGovernanceRetention)을 가진 관리자(root 등)는 잠금을 우회하여 삭제하거나 잠금 기간을 단축할 수 있습니다.

- COMPLIANCE 모드 (컴플라이언스 모드)
  - 법적 감사 데이터, 금융 거래 로그, 의료 기록 등 법적 규제(SEC 17a-4 등) 준수가 필수적인 데이터.
  - 그 누구도(Root 계정 포함) 지정된 보존 기간(Retention Period)이 만료되기 전까지는 객체를 덮어쓰거나 삭제할 수 없습니다. 보존 기간을 단축하는 것도 불가능합니다.

### 파일 추가 / 삭제

```bash
# 단일 파일 추가
docker exec minio_mc mc cp /tmp/config.json myminio/datalake/config.json

# 단일 파일 삭제
docker exec minio_mc mc rm myminio/datalake/config.json

# 디렉토리 재귀적 삭제
docker exec minio_mc mc rm --recursive --force myminio/datalake/rawdata/2025

# 특정 기간 이전 파일 삭제
docker exec minio_mc mc rm --recursive --force --older-than 30d myminio/datalake/tmp/
```

## AWS CLI 호환

---

### 환경 변수 설정 (간편)

AWS CLI(aws)를 사용하여 MinIO를 제어할 때 가장 중요한 점은 --endpoint-url 옵션을 통해 요청을 AWS가 아닌 MinIO 서버로 돌리는 것입니다.
환경 변수로 설정하는 방법과 .aws/config 파일에 설정하는 방법이 있습니다.

```bash
export AWS_ENDPOINT_URL=http://minio-server:9000
export AWS_ACCESS_KEY_ID=minioadmin      # MinIO 아이디
export AWS_SECRET_ACCESS_KEY=minioadmin  # MinIO 비밀번호
export AWS_DEFAULT_REGION=us-east-1      # MinIO는 리전 구분은 없지만, 클라이언트 호환성을 위해 설정 권장
```

### AWS CLI 설정 파일 수정 (표준, AWS CLI v2+)

```bash
# 1. 디렉토리 생성 (없을 경우 대비)
mkdir -p ~/.aws

# 2. config 파일 작성 (S3 요청을 MinIO로 납치하는 설정 포함)
cat > ~/.aws/config <<EOF
[default]
region = us-east-1
output = json
services = minio-endpoint

[services minio-endpoint]
s3 =
  endpoint_url = http://minio-server:9000
EOF

# 3. credentials 파일 작성 (자격 증명)
cat > ~/.aws/credentials <<EOF
[default]
aws_access_key_id = minioadmin
aws_secret_access_key = minioadmin
EOF
```

### 버킷(Bucket) 관리

```bash
# 버킷 생성
aws s3 mb s3://datalake --endpoint-url http://minio-server:9000

# 버킷 목록 조회
aws s3 ls --endpoint-url http://minio-server:9000

# 버킷 삭제 (내용이 비어있어야 함)
aws s3 rb s3://datalake --endpoint-url http://minio-server:9000
```

### 파일 업로드 및 다운로드 (Copy)

```bash
# 단일 파일 업로드
aws s3 cp ./data.csv s3://datalake/raw/data.csv --endpoint-url http://minio-server:9000

# 파일 다운로드
aws s3 cp s3://datalake/raw/data.csv ./downloaded_data.csv --endpoint-url http://minio-server:9000

# 서버 내부 복사 (MinIO 내부 이동, 네트워크 효율적)
aws s3 cp s3://datalake/raw/data.csv s3://datalake/processed/data.csv --endpoint-url http://minio-server:9000
```

### 파일 목록 조회 및 삭제

```bash
# 파일 목록 조회 (특정 폴더)
aws s3 ls s3://datalake/raw/ --endpoint-url http://minio-server:9000

# 전체 파일 재귀적 조회 (하위 폴더 포함)
aws s3 ls s3://datalake/ --recursive --endpoint-url http://minio-server:9000

# 특정 파일 삭제
aws s3 rm s3://datalake/raw/data.csv --endpoint-url http://minio-server:9000

# 폴더 하위 모든 파일 삭제 (주의!)
aws s3 rm s3://datalake/raw/ --recursive --endpoint-url http://minio-server:9000
```

### 대용량 동기화 (Sync)

```bash
# 로컬 폴더 -> MinIO 동기화 (업로드)
aws s3 sync ./local_logs s3://datalake/logs/ --endpoint-url http://minio-server:9000

# MinIO -> 로컬 폴더 동기화 (다운로드)
aws s3 sync s3://datalake/logs/ ./local_backup_logs --endpoint-url http://minio-server:9000

# 완전 동기화 (소스에서 삭제된 파일은 타겟에서도 삭제)
aws s3 sync ./local_logs s3://datalake/logs/ --delete --endpoint-url http://minio-server:9000
```
