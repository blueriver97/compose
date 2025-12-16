from pyspark.sql import functions as F  # noqa
from pyspark.sql import types as T  # noqa
from pyspark.sql import SparkSession

CATALOG = "local"
spark = (
    SparkSession.builder.appName("test_iceberg_hadoop_catalog")
    .config("spark.sql.defaultCatalog", CATALOG)
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.type", "rest")
    .config(f"spark.sql.catalog.{CATALOG}.uri", "http://iceberg-rest:8181")
    # iceberg-rest는 Credential vending 기능이 없어서 Spark에서 MinIO에 접근할 때 필요한 정보를 직접 추가함.
    .config(f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config(f"spark.sql.catalog.{CATALOG}.s3.endpoint", "http://minio-server:9000")
    .config(f"spark.sql.catalog.{CATALOG}.s3.path-style-access", "true")
    .config(f"spark.sql.catalog.{CATALOG}.client.region", "us-east-1")
    .config(f"spark.sql.catalog.{CATALOG}.s3.access-key-id", "minioadmin")
    .config(f"spark.sql.catalog.{CATALOG}.s3.secret-access-key", "minioadmin")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.caseSensitive", "true")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
    .getOrCreate()
)

spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {CATALOG}.default")

# 문법: <catalog_name>.<schema_name>.<table_name>
df = spark.createDataFrame([[1, '2'], [3, '4'], [5, '6']], schema=T.StructType([
    T.StructField("id", T.IntegerType()),
    T.StructField("data", T.StringType())
]))
df.write.format("iceberg").mode("append").saveAsTable(f"{CATALOG}.default.sample")

spark.read.format("iceberg").load(f"{CATALOG}.default.sample").show()
