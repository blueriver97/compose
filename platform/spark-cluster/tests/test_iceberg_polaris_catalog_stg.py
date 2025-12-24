from pyspark.sql import functions as F  # noqa
from pyspark.sql import types as T  # noqa
from pyspark.sql import SparkSession

CATALOG = "polaris"
spark = (
    SparkSession.builder.appName("test_iceberg_polaris_catalog")
    .config("spark.sql.defaultCatalog", CATALOG)
    .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
    .config(f"spark.sql.catalog.{CATALOG}.type", "rest")
    .config(f"spark.sql.catalog.{CATALOG}.warehouse", "polaris") # polaris catalog name
    .config(f"spark.sql.catalog.{CATALOG}.uri", "https://polaris.blueriver.ddns.net/api/catalog")
    .config(f"spark.sql.catalog.{CATALOG}.oauth2-server-uri", "https://polaris.blueriver.ddns.net/api/catalog/v1/oauth/tokens")
    .config(f"spark.sql.catalog.{CATALOG}.header.Polaris-Realm", "default")
    .config(f"spark.sql.catalog.{CATALOG}.header.X-Iceberg-Access-Delegation", "vended-credentials")
    .config(f"spark.sql.catalog.{CATALOG}.credential", "root:polarisadmin")
    .config(f"spark.sql.catalog.{CATALOG}.scope", "PRINCIPAL_ROLE:ALL")
    .config(f"spark.sql.catalog.{CATALOG}.token-refresh-enabled", "true")
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
