# MinIO Object Storage

이 디렉토리는 S3 호환 객체 스토리지인 MinIO를 구축하고 관리하기 위한 설정입니다.

S3를 대체하여 데이터 레이크, 로그 아카이빙, 또는 애플리케이션의 파일 저장소로 활용할 수 있습니다.

---

## 1. 아키텍처 및 구성 요소 (Components)

`docker compose`를 통해 다음 두 가지 서비스가 실행됩니다.

| 서비스명      | 역할            | 설명                                                                                               |
| :------------ | :-------------- | :------------------------------------------------------------------------------------------------- |
| minio         | 스토리지 서버   | S3 API 호환 스토리지 엔진 및 Web Console 제공                                                      |
| createbuckets | 초기화 유틸리티 | 컨테이너 실행 시 `.env`에 정의된 버킷을 자동으로 생성하고 종료되는 일회성 컨테이너 (`mc` CLI 사용) |

---

## 2. 설정 (Configuration)

환경 설정은 `.env` 파일에서 관리합니다.

### 주요 환경 변수

| 변수명                  | 설명                                  | 기본값           |
| :---------------------- | :------------------------------------ | :--------------- |
| `MINIO_ROOT_USER`       | 관리자 ID (AWS Access Key 역할)       | (사용자 지정)    |
| `MINIO_ROOT_PASSWORD`   | 관리자 비밀번호 (AWS Secret Key 역할) | (사용자 지정)    |
| `MINIO_API_PORT`        | S3 API 호환 포트 (코드 연동용)        | `9000`           |
| `MINIO_CONSOLE_PORT`    | Web Console 포트 (브라우저 접속용)    | `9001`           |
| `MINIO_DEFAULT_BUCKETS` | 자동 생성할 버킷 목록 (쉼표로 구분)   | `iceberg-bucket` |

---

## 3. 실행 및 접속 (Usage)

### 실행 방법

```bash
cd platform/minio
docker compose up -d
```

## 4. 데이터 저장 (Persisting Data)

- 데이터는 Docker Volume minio_data에 저장됩니다.
- 컨테이너를 재시작해도 데이터는 유지되지만, 볼륨을 삭제(docker compose down -v)하면 데이터가 초기화됩니다.

## 5. 사용 예시 (Examples)

### 테스트

- write_table.py 스크립트는 PySpark를 사용하여 MinIO에 Apache Iceberg 포맷으로 데이터를 쓰고 읽는 예제입니다.
- 아래 의존성 설치가 필요합니다.

```bash
pip install pyspark pydantic pydantic-settings
```

- MinIO 컨테이너가 실행 중인 상태에서 아래 명령어를 수행합니다.

```bash
python write_table.py
```

### 주요 설정

- MinIO를 로컬 S3로 사용하기 위해 Spark 설정 시 다음 옵션이 중요합니다. (write_table.py 참고)

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
.config("spark.sql.catalog.local.warehouse", "s3a://iceberg-bucket/iceberg_warehouse")
```

### 사용자 생성

- Admin 계정을 사용하기 보다 일반 사용자 계정 사용을 권장합니다.

```bash
# 예시: mc admin user add <alias> <ACCESS_KEY> <SECRET_KEY>
docker exec minio_mc mc admin user add myminio newuser newpassword123
docker exec minio_mc mc admin policy attach myminio readwrite --user newuser
docker exec minio_mc mc admin user list myminio
```
