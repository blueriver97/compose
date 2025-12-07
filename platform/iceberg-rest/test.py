import os
from pyspark.sql import SparkSession
from pyspark.sql import types as T

# 환경 변수 체크 (카탈로그 생성까지는 iceberg-rest가 처리하지만, 실제 데이터를 읽고, 쓰는 작업 시 MinIO 인증키 필요)
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""

CATALOG = "my_catalog"
spark = (
    SparkSession.builder.appName("Iceberg Rest Catalog")
    # .config("spark.jars.packages",
    #         "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
    #         "org.apache.hadoop:hadoop-aws:3.3.4,"
    #         "")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.defaultCatalog", "my_catalog")
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.type", "rest")
    .config(f"spark.sql.catalog.{CATALOG}.uri", "http://localhost:8181")
    .config(f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config(f"spark.sql.catalog.{CATALOG}.s3.endpoint", "http://localhost:9000")
    .config(f"spark.sql.catalog.{CATALOG}.s3.path-style-access", True)
    .getOrCreate()
)

# 테이블 생성 테스트
spark.sql("CREATE NAMESPACE IF NOT EXISTS my_catalog.default")
spark.sql("CREATE TABLE IF NOT EXISTS my_catalog.default.sample (id bigint, DATA string) USING iceberg")

# 데이터 쓰기 테스트
df = spark.createDataFrame([[1, "20"], [2, "40"]], schema=T.StructType([
    T.StructField("id", T.IntegerType()),
    T.StructField("DATA", T.StringType())
]))
df.write.format("iceberg").mode("append").saveAsTable(f"{CATALOG}.default.sample")

# 데이터 읽기 테스트
spark.read.format("iceberg").load(f"{CATALOG}.default.sample").show()
