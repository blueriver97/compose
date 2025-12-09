import os
from pyspark.sql import SparkSession
from pyspark.sql import types as T
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MINIO_ACCESS_KEY: str = Field(alias="MINIO_ROOT_USER")
    MINIO_SECRET_KEY: str = Field(alias="MINIO_ROOT_PASSWORD")
    CATALOG_NAME: str = Field(alias="CATALOG_NAME")
    BUCKET_NAME: str = Field(default="BUCKET_NAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


config = Settings(_env_file=".env", _env_file_encoding="utf-8")

# 환경 변수 체크 (카탈로그 생성까지는 iceberg-rest에 입력한 키로 처리 가능, 실제 데이터를 읽고/쓰는 작업 시 MinIO 인증키 필요)
os.environ["AWS_ACCESS_KEY_ID"] = config.MINIO_ACCESS_KEY
os.environ["AWS_SECRET_ACCESS_KEY"] = config.MINIO_SECRET_KEY

CATALOG = config.CATALOG_NAME
spark = (
    SparkSession.builder.appName("Iceberg Rest Catalog")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.defaultCatalog", CATALOG)
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.type", "rest")
    .config(f"spark.sql.catalog.{CATALOG}.uri", "http://localhost:8181")
    .config(f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config(f"spark.sql.catalog.{CATALOG}.s3.endpoint", "http://localhost:9000")
    .config(f"spark.sql.catalog.{CATALOG}.s3.path-style-access", True)
    .getOrCreate()
)

# 테이블 생성 테스트
spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {CATALOG}.default")
spark.sql(f"CREATE TABLE IF NOT EXISTS {CATALOG}.default.sample (id bigint, data string) USING iceberg")

# 데이터 쓰기 테스트
df = spark.createDataFrame([[1, "1"], [2, "2"]], schema=T.StructType([
    T.StructField("id", T.IntegerType()),
    T.StructField("data", T.StringType())
]))
df.write.format("iceberg").mode("append").saveAsTable(f"{CATALOG}.default.sample")

# 데이터 읽기 테스트
spark.read.format("iceberg").load(f"{CATALOG}.default.sample").show()
