from pyspark.sql import SparkSession
from pyspark.sql import types as T
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MINIO_ACCESS_KEY: str = Field(alias="MINIO_ROOT_USER")
    MINIO_SECRET_KEY: str = Field(alias="MINIO_ROOT_PASSWORD")
    MINIO_API_PORT: str = Field(alias="MINIO_API_PORT", default="9000")
    BUCKET_NAME: str = Field(default="iceberg-bucket")
    CATALOG_NAME: str = Field(default="local")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # .env에 모르는 변수가 있어도 에러 안 냄
    )

    @computed_field
    def MINIO_ENDPOINT(self) -> str:
        """
        MINIO_ENDPOINT가 .env에 명시되어 있으면 그걸 쓰고,
        없으면 MINIO_API_PORT를 기반으로 localhost 주소를 자동 생성합니다.
        """
        return f"http://localhost:{self.MINIO_API_PORT}"


config = Settings(_env_file=".env", _env_file_encoding="utf-8")

# MinIO 접속 정보 (docker-compose.yml 기준)
spark = (
    SparkSession.builder
    .appName("IcebergWithMinIO")
    # -------------------------------------------------------------------------
    # 1. 필수 라이브러리 (Spark 버전에 맞춰 수정 필요)
    # Spark 3.5 기준: Iceberg 1.5.0, Hadoop-AWS 3.3.4 (Spark 내장 하둡 버전과 호환 필요)
    # -------------------------------------------------------------------------
    .config("spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "")

    # -------------------------------------------------------------------------
    # 2. Iceberg Catalog 설정
    # 여기서는 'local'이라는 이름의 카탈로그를 정의합니다.
    # -------------------------------------------------------------------------
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config(f"spark.sql.catalog.{config.CATALOG_NAME}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{config.CATALOG_NAME}.type", "hadoop")  # 파일시스템 기반 카탈로그 (가장 간단)
    # S3A 프로토콜 사용
    .config(f"spark.sql.catalog.{config.CATALOG_NAME}.warehouse", f"s3a://{config.BUCKET_NAME}/iceberg_warehouse")

    # -------------------------------------------------------------------------
    # 3. MinIO (S3) 연결 설정 (Hadoop AWS)
    # -------------------------------------------------------------------------
    .config("spark.hadoop.fs.s3a.endpoint", config.MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", config.MINIO_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", config.MINIO_SECRET_KEY)

    # [핵심] Path Style Access: true 필수
    # 설명: false(기본값)면 bucket-name.localhost:9000 처럼 DNS 스타일로 찾아서 에러 발생
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")  # 로컬 HTTP 사용 시
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    # (선택) 성능 튜닝: 로컬 테스트 시 빠른 커밋을 위해
    .config("spark.hadoop.fs.s3a.committer.magic.enabled", "true")
    .getOrCreate()
)

print("Creating Namespace...")
spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {config.CATALOG_NAME}.db")

# 3. 테이블 저장
print("Saving Table...")
# 문법: <catalog_name>.<namespace_name>.<table_name>
df = spark.createDataFrame([[1, 2, "3", 4]], schema=T.StructType([
    T.StructField("id", T.IntegerType()),
    T.StructField("value", T.IntegerType()),
    T.StructField("name", T.StringType()),
    T.StructField("age", T.IntegerType()),
]))
df.write.format("iceberg").mode("append").saveAsTable(f"{config.CATALOG_NAME}.db.test_table")
print("Success! Data saved to MinIO.")

# 4. 확인 (데이터 읽기)
spark.read.format("iceberg").load(f"{config.CATALOG_NAME}.db.test_table").show()
