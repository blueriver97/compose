# Apache Iceberg REST Catalog

이 프로젝트는 Iceberg 생태계의 표준 인터페이스인 REST Catalog의 구성을 나타냅니다.

## 개요 (Overview)

---

REST Catalog는 모든 Iceberg 클라이언트와 카탈로그 서버 간의 통신을 단일 표준 API(OpenAPI Spec)로 통일하여 다음과 같은 이점을 제공합니다.

#### Universal Compatibility

- 언어(Java, Python, Rust 등)나 엔진에 상관없이 단일 클라이언트 구현만으로 모든 카탈로그와 통신이 가능합니다.

#### Server-Side Deconfliction

- 데이터 충돌(Conflict) 발생 시 클라이언트가 아닌 서버가 재시도(Retry) 및 병합을 제어하여 작업 신뢰성을 대폭 향상시킵니다. (Change-based
  commits)

#### Advanced Features

- Multi-table commits(다중 테이블 트랜잭션), Lazy snapshot loading 등 클라이언트 기반 카탈로그에서는 구현하기 어려운 기능을 지원합니다.
- Multi-table Commits: 여러 테이블에 대한 변경 사항을 단일 트랜잭션으로 묶어 원자적(Atomic)으로 커밋할 수 있습니다.
- Lazy Snapshot Loading: 테이블의 전체 히스토리를 로딩하는 대신 필요한 시점의 스냅샷만 지연 로딩하여, 대규모 테이블 조회 시 초기 기동 속도를 획기적으로 개선하고 메모리 사용량을
  최적화합니다.

## 환경 구성 (Configuration)

---

이 구성은 모던 데이터 레이크 표준인 Catalog-Centric 방식을 따르며 추가로 아래의 환경을 필요로 합니다.

- Compute (Spark): 데이터 처리 및 분석 엔진.
- Storage (MinIO): 실제 데이터 파일(Parquet, Avro 등)이 저장되는 S3 호환 Object Storage.

### 사전 준비

```bash
cd ../minio
docker-compose up -d
```

- Storage: [`../minio`](../minio) 디렉토리에서 MinIO 서비스를 먼저 실행해야 합니다.
- 기본 버킷 생성 여부를 확인하십시오.

### 실행

```bash
docker-compose up -d
```

## 사용 예시 (Example)

---

```python
from pyspark.sql import SparkSession

# 카탈로그 생성까지는 iceberg-rest에 입력한 키로 처리 가능, 실제 데이터를 읽고/쓰는 작업 시 MinIO 인증키 필요
CATALOG = "local"
MINIO_ACCESS_KEY = ""
MINIO_SECRET_KEY = ""
spark = (
    SparkSession.builder.appName("Iceberg Rest Catalog")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.defaultCatalog", CATALOG)
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.type", "rest")
    .config(f"spark.sql.catalog.{CATALOG}.uri", "http://localhost:8181")
    .config(f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config(f"spark.sql.catalog.{CATALOG}.s3.endpoint", "http://localhost:9000")
    .config(f"spark.sql.catalog.{CATALOG}.s3.path-style-access", "true")
    .config(f"spark.sql.catalog.{CATALOG}.client.region", "us-east-1")
    .config(f"spark.sql.catalog.{CATALOG}.s3.access-key-id", MINIO_ACCESS_KEY)
    .config(f"spark.sql.catalog.{CATALOG}.s3.secret-access-key", MINIO_SECRET_KEY)
    .getOrCreate()
)
```

## 트러블슈팅 (Troubleshooting)

---

> Caused by: software.amazon.awssdk.core.exception.SdkClientException: Unable to execute HTTP request:
> iceberg-bucket.localhost (SDK Attempt Count: 6)

- False 설정 시, 버킷 이름이 MinIO 주소 앞에 .(dot)으로 붙으므로 `spark.sql.catalog.{CATALOG}.s3.path-style-access` 값을 True로 설정 필수

> Caused by: java.io.IOException: software.amazon.awssdk.services.s3.model.S3Exception: The Access Key Id you provided
> does not exist in our records.

- MinIO 인증 정보가 없는 경우 발생되며, 환경변수 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY를 설정이 올바른지 확인 필요.
