from pyspark.sql import functions as F  # noqa
from pyspark.sql import types as T  # noqa
from pyspark.sql import SparkSession

CATALOG = "local"
spark = (
    SparkSession.builder.appName("test_iceberg_hadoop_catalog")
    .config("spark.sql.defaultCatalog", CATALOG)
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.type", "hadoop")
    .config(f"spark.sql.catalog.{CATALOG}.warehouse", "s3a://datalake/iceberg-warehouse")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.caseSensitive", True)
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
    .getOrCreate()
)

spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {CATALOG}.default")

# 문법: <catalog_name>.<schema_name>.<table_name>
df = spark.createDataFrame([[1, '2'], [3, '4']], schema=T.StructType([
    T.StructField("id", T.IntegerType()),
    T.StructField("data", T.StringType())
]))
df.write.format("iceberg").mode("append").saveAsTable(f"{CATALOG}.default.sample")

spark.read.format("iceberg").load(f"{CATALOG}.default.sample").show()
