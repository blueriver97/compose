from pyspark.sql import functions as F  # noqa
from pyspark.sql import types as T  # noqa
from pyspark.sql import SparkSession

CATALOG = "glue"
spark = (
    SparkSession.builder.appName("test_iceberg_glue_catalog")
    .config("spark.sql.defaultCatalog", CATALOG)
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config(f"spark.sql.catalog.{CATALOG}.warehouse", "s3a://datalake/iceberg-warehouse")
    .config(f"spark.sql.catalog.{CATALOG}.s3.path-style-access", "true")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider")
    .config("spark.sql.caseSensitive", "true")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
    .getOrCreate()
)

spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {CATALOG}.default")

# 문법: <catalog_name>.<schema_name>.<table_name>
df = spark.createDataFrame([[1, '2'], [3, '4'], [5, '6'], [7, '8']], schema=T.StructType([
    T.StructField("id", T.IntegerType()),
    T.StructField("data", T.StringType())
]))
df.write.format("iceberg").mode("append").saveAsTable(f"{CATALOG}.default.sample")

spark.read.format("iceberg").load(f"{CATALOG}.default.sample").show()
