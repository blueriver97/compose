# src/04.mysql_to_iceberg.py
import os
from typing import Dict, List

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import SparkSession, DataFrame, Column

# --- Import common modules ---
from utils.logging import setup_console_logging
from utils.settings import Settings
from utils.database import get_jdbc_options, get_primary_keys, get_partition_key_info


def cast_dataframe(df: DataFrame) -> DataFrame:
    """Timestamp 타입은 UTC 시간으로 변경하고 Boolean 타입은 Int로 변경함"""

    def cast_column_type(field: T.StructField) -> Column:
        return F.col(field.name).alias(field.name)

    return df.select([cast_column_type(field) for field in df.schema.fields])


def main(spark: SparkSession, config: Settings) -> None:
    """
    Reads data from a MySQL database and saves it as Iceberg tables.
    """
    logger = setup_console_logging(spark)
    logger.info("Starting Iceberg table creation from MySQL.")
    logger.info(f"Target tables: {config.TABLE_STR}")

    # Note. Retrieve primary key and partition key information from the database.
    primary_keys: Dict[str, List[str]] = get_primary_keys(spark, config)
    partition_keys: Dict[str, str] = get_partition_key_info(spark, config)
    jdbc_options = get_jdbc_options(config)

    success_count = 0
    for table_name in config.TABLE_LIST:
        try:
            schema, table = table_name.split(".")
            bronze_schema = f"{schema.lower()}_bronze"
            target_table = table.lower()
            full_table_name = f"{config.CATALOG}.{bronze_schema}.{target_table}"

            pk_cols = primary_keys.get(table_name, [])
            partition_column = partition_keys.get(table_name)

            jdbc_df: DataFrame

            if partition_column:
                logger.info(f"Reading '{table_name}' with partitioning on column '{partition_column}'.")
                bound_query = (
                    f"SELECT min({partition_column}) as `lower`, max({partition_column}) as `upper` FROM {table_name}"
                )
                bound_df = spark.read.format("jdbc").options(**jdbc_options).option("query", bound_query).load()
                bounds = bound_df.first()

                if not bounds or bounds["lower"] is None:
                    logger.warning(
                        f"Partition column '{partition_column}' has no data for table '{table_name}'. Reading without partitioning."
                    )
                    jdbc_df = spark.read.format("jdbc").options(**jdbc_options).option("dbtable", table_name).load()
                else:
                    jdbc_df = (
                        spark.read.format("jdbc")
                        .options(**jdbc_options)
                        .option("dbtable", table_name)
                        .option("partitionColumn", partition_column)
                        .option("lowerBound", bounds["lower"])
                        .option("upperBound", bounds["upper"])
                        .option("numPartitions", config.NUM_PARTITIONS)
                        .load()
                    )
            else:
                logger.info(f"Reading '{table_name}' without partitioning.")
                jdbc_df = spark.read.format("jdbc").options(**jdbc_options).option("dbtable", table_name).load()

            jdbc_df = cast_dataframe(jdbc_df)
            jdbc_df = jdbc_df.withColumn("last_applied_date", F.current_timestamp())

            # Note. Create the database if it does not exist.
            spark.sql(f"CREATE DATABASE IF NOT EXISTS {config.CATALOG}.{bronze_schema}")

            logger.info(f"Creating or replacing {full_table_name}")
            # Issue. Merge On Read / Accept-Schema 활성화 시 아래 옵션 추가 필요.
            # Issue. write.spark.accept-any-schema 활성화 시 Merge Into ... UNRESOLVED_COLUMN.WITH_SUGGESTION 오류 발생됨.
            """
                'write.spark.accept-any-schema'='true',
                'write.delete.mode'='merge-on-read',
                'write.update.mode'='merge-on-read',
                'write.merge.mode'='merge-on-read',
            """
            if pk_cols:
                jdbc_df = jdbc_df.withColumn("id_iceberg", F.md5(F.concat_ws("|", *[F.col(pk) for pk in pk_cols])))
                (
                    jdbc_df.limit(1)
                    .writeTo(f"{full_table_name}")
                    .using("iceberg")
                    .tableProperty("location", f"{config.ICEBERG_S3_ROOT_PATH}/{bronze_schema}/{target_table}")
                    .tableProperty("format-version", "2")
                    .tableProperty("write.metadata.delete-after-commit.enabled", "true")
                    .tableProperty("write.metadata.previous-versions-max", "5")
                    .tableProperty("history.expire.max-snapshot-age-ms", "86400000")
                    # .partitionedBy(F.bucket(num_partition, "id_iceberg"))
                    .createOrReplace()
                )

                (
                    jdbc_df.writeTo(f"{full_table_name}")
                    # .partitionedBy(F.bucket(num_partition, "id_iceberg"))
                    .overwritePartitions()
                )
            else:
                (
                    jdbc_df.writeTo(f"{full_table_name}")
                    .using("iceberg")
                    .tableProperty("location", f"{config.ICEBERG_S3_ROOT_PATH}/{bronze_schema}/{target_table}")
                    .tableProperty("format-version", "2")
                    .createOrReplace()
                )

            success_count += 1
            progress = (success_count / len(config.TABLE_LIST)) * 100
            logger.info(f"[{progress:3.1f}%] Successfully created or replaced {full_table_name}")

        except Exception as e:
            logger.error(f"[FAIL] Failed to process {table_name}: {e}")

    logger.info("Iceberg table creation process finished.")


if __name__ == "__main__":
    settings = Settings()
    settings.init_vault()

    os.environ["AWS_PROFILE"] = settings.AWS_PROFILE

    spark_session = (
        SparkSession.builder.appName("MySQLToIceberg")
        .config("spark.sql.defaultCatalog", settings.CATALOG)
        .config(f"spark.sql.catalog.{settings.CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
        .config(f"spark.sql.catalog.{settings.CATALOG}.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
        .config(f"spark.sql.catalog.{settings.CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config(f"spark.sql.catalog.{settings.CATALOG}.warehouse", settings.ICEBERG_S3_ROOT_PATH)
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    main(spark_session, settings)
    spark_session.stop()
