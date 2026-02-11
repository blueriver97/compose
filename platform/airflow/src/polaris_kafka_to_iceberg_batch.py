import os
import json
from textwrap import dedent

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark import StorageLevel
from pyspark.sql import SparkSession, DataFrame, Column, Window
from pyspark.sql.avro.functions import from_avro
from confluent_kafka.schema_registry import SchemaRegistryClient

# --- Import common modules ---
from utils.logging import setup_console_logging
from utils.settings import Settings


def extract_debezium_schema(schema: dict) -> dict:
    """
    Debezium 메시지 스키마에서 컬럼 이름과 Debezium 커넥터 타입을 추출합니다.

    Args:
        schema: 파싱할 Debezium JSON 스키마 딕셔너리.

    Returns:
        {column_name: dbz_connector_type} 형태의 딕셔너리.
    """
    debezium_type = {}

    # 1. Envelope 스키마의 'fields' 목록에서 'before' 또는 'after' 필드를 찾습니다.
    envelope_fields = schema.get("fields", [])
    value_schema = None
    for field in envelope_fields:
        if field.get("name") in ("before", "after"):
            # 타입 정보는 ['null', {실제 스키마}] 형태일 수 있습니다.
            type_definitions = field.get("type", [])
            for type_def in type_definitions:
                if isinstance(type_def, dict) and "fields" in type_def:
                    value_schema = type_def
                    break
            if value_schema:
                break

    if not value_schema:
        print("Error: 'before' 또는 'after' 필드에서 유효한 스키마를 찾을 수 없습니다.")
        return {}

    # 2. 찾은 스키마 내부의 'fields' (컬럼 목록)를 순회합니다.
    column_fields = value_schema.get("fields", [])
    for col_field in column_fields:
        col_name = col_field.get("name")
        if not col_name:
            continue

        type_info = col_field.get("type")

        # 3. 컬럼 타입을 처리합니다. (Nullable 여부 고려)
        actual_type_def = None
        if isinstance(type_info, list):
            # Nullable 타입: ['null', type] 형태에서 실제 타입 정보를 찾습니다.
            for item in type_info:
                if item != "null":
                    actual_type_def = item
                    break
        else:
            # Non-nullable 타입
            actual_type_def = type_info

        if not actual_type_def:
            continue

        # 4. 최종 커넥터 타입을 추출합니다.
        # 복합 타입(dict)인 경우 'connect.name'을 우선적으로 사용하고,
        # 없는 경우 'type'을 사용합니다.
        # 단순 타입(str)인 경우 해당 문자열을 그대로 사용합니다.
        dbz_connector_type = None
        if isinstance(actual_type_def, dict):
            dbz_connector_type = actual_type_def.get("connect.name")
            if not dbz_connector_type:
                dbz_connector_type = actual_type_def.get("type")
        elif isinstance(actual_type_def, str):
            dbz_connector_type = actual_type_def

        if dbz_connector_type:
            debezium_type[col_name] = dbz_connector_type

    return debezium_type


def cast_dataframe(df: DataFrame, catalog_schema: T.StructType, debezium_dtypes: dict) -> DataFrame:
    def cast_column_type(field: T.StructField, debezium_dtype: str) -> Column:
        """
        "date1": {
            "int": 18641
        },
        "time1": {
            "long": 18291000000
        },
        "datetime1": {
            "long": 1758712669000
        },
        "create_datetime": {
            "long": 1758712669557813
        },
        "update_timestamp": {
            "string": "2025-09-24T02:17:49.557813Z"
        }
        """
        if debezium_dtype == "io.debezium.time.Date":
            return F.date_add(F.lit("1970-01-01"), F.col(field.name).cast("int")).alias(field.name)
        elif debezium_dtype == "io.debezium.time.MicroTime":
            return F.to_utc_timestamp(F.timestamp_seconds(F.col(field.name) / 1_000_000), "UTC").alias(field.name)
        elif debezium_dtype == "io.debezium.time.Timestamp":
            return F.to_utc_timestamp(F.timestamp_millis(F.col(field.name)), "Asia/Seoul").alias(field.name)
        elif debezium_dtype == "io.debezium.time.MicroTimestamp":
            return F.to_utc_timestamp(F.timestamp_micros(F.col(field.name)), "Asia/Seoul").alias(field.name)
        elif debezium_dtype == "io.debezium.time.ZonedTimestamp":
            pass
        return F.col(field.name).cast(field.dataType).alias(field.name)

    return df.select(
        *[cast_column_type(field, debezium_dtypes.get(field.name, "")) for field in catalog_schema.fields],
        "__op",
        "__offset",
    )


def process_table(
    spark: SparkSession,
    config: Settings,
    schema: str,
    table: str,
    table_df: DataFrame,
    parsed_debezium_schema: dict,
    pk_cols: list,
) -> None:
    iceberg_schema, iceberg_table = f"{schema.lower()}_bronze", table.lower()
    full_table_name = f"{config.CATALOG}.{iceberg_schema}.{iceberg_table}"
    logger = setup_console_logging(spark)

    catalog_schema = spark.table(full_table_name).schema

    cdc_df = table_df.withColumn("last_applied_date", F.col("__ts_ms")).withColumn(
        "id_iceberg", F.md5(F.concat_ws("|", *[F.col(column) for column in pk_cols]))
    )
    cdc_df = cast_dataframe(cdc_df, catalog_schema, parsed_debezium_schema)

    window_spec = Window.partitionBy("id_iceberg").orderBy(F.desc("__offset"))
    cdc_df = (
        cdc_df.withColumn("__row", F.row_number().over(window_spec))
        .filter(F.col("__row") == 1)
        .drop("__row", "__offset")
    )
    upsert_df = cdc_df.filter(F.col("__op") != "d").drop("__op")
    delete_df = cdc_df.filter(F.col("__op") == "d").drop("__op")

    if not upsert_df.isEmpty():
        upsert_df.createOrReplaceGlobalTempView("upsert_view")
        columns = spark.table(full_table_name).columns
        update_expr = ", ".join([f"t.{c} = s.{c}" for c in columns])
        insert_cols = ", ".join(columns)
        insert_vals = ", ".join([f"s.{c}" for c in columns])

        query = dedent(f"""
            MERGE INTO {full_table_name} t
            USING (SELECT * FROM global_temp.upsert_view) s
            ON t.id_iceberg = s.id_iceberg
            WHEN MATCHED THEN UPDATE SET {update_expr}
            WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
        """)
        logger.info(f"statements > {query}")
        spark.sql(query)

    if not delete_df.isEmpty():
        delete_df.createOrReplaceGlobalTempView("delete_view")
        query = dedent(f"""
            DELETE FROM {full_table_name} t
            WHERE EXISTS (
                SELECT s.id_iceberg
                FROM global_temp.delete_view s
                WHERE s.id_iceberg = t.id_iceberg
            )
        """)
        logger.info(f"statements > {query}")
        spark.sql(query)


def process_batch(batch_df: DataFrame, batch_id: int, spark: SparkSession, config: Settings) -> None:
    spark.sparkContext.setLogLevel("INFO")
    logger = setup_console_logging(spark)

    logger.info(f"<batch-{batch_id}, {batch_df.count()}>")
    if batch_df.isEmpty():
        return

    batch_df.persist(StorageLevel.MEMORY_AND_DISK)
    for table_identifier in config.TABLE_LIST:
        schema, table = table_identifier.split(".")
        target_topic = config.TOPIC_DICT.get(table_identifier)
        filtered_df = batch_df.filter(F.col("topic") == target_topic)

        if filtered_df.isEmpty():
            continue

        # 메시지 내 Schema ids 추출 및 Schema registry 조회
        value_schema_ids = [row.value_schema_id for row in filtered_df.select("value_schema_id").distinct().collect()]
        value_schema_dict = {sid: schema_registry_client.get_schema(sid).schema_str for sid in value_schema_ids}

        logger.info(f"{value_schema_ids}, {value_schema_dict}")

        # Schema ID 별로 DataFrame 필터링 후 처리
        for schema_id, schema_str in value_schema_dict.items():
            schema_filtered_df = filtered_df.filter(F.col("value_schema_id") == schema_id)
            debezium_schema = json.loads(schema_str)
            parsed_debezium_schema = extract_debezium_schema(debezium_schema)

            # Schema 적용
            key_schema_id = schema_filtered_df.select("key_schema_id").distinct().collect()[0].key_schema_id
            key_schema_str = schema_registry_client.get_schema(key_schema_id).schema_str
            pk_cols = [field["name"] for field in json.loads(key_schema_str)["fields"]]

            transformed_df = schema_filtered_df.withColumn(
                "data",
                from_avro(F.col("value"), schema_str, {"mode": "FAILFAST"}),
            ).select(
                "data.after.*",
                F.col("data.ts_ms").alias("__ts_ms"),
                F.col("data.op").alias("__op"),
                F.col("offset").alias("__offset"),
            )

            process_table(spark, config, schema, table, transformed_df, parsed_debezium_schema, pk_cols)

    batch_df.unpersist()


if __name__ == "__main__":
    # 1. Load settings from .env file
    # dev.env 또는 prod.env 파일을 지정하여 환경을 선택할 수 있습니다.
    # settings = Settings(_env_file="src/dev.env", _env_file_encoding="utf-8")

    settings = Settings()
    spark = (
        SparkSession.builder.appName("")
        .config("spark.sql.defaultCatalog", settings.CATALOG)
        .config(f"spark.sql.catalog.{settings.CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
        .config(f"spark.sql.catalog.{settings.CATALOG}.type", "rest")
        .config(f"spark.sql.catalog.{settings.CATALOG}.warehouse", "polaris")  # polaris catalog name
        .config(f"spark.sql.catalog.{settings.CATALOG}.uri", "http://polaris.svc.internal:8181/api/catalog")
        .config(f"spark.sql.catalog.{settings.CATALOG}.oauth2-server-uri", "http://polaris.svc.internal:8181/api/catalog/v1/oauth/tokens")
        .config(f"spark.sql.catalog.{settings.CATALOG}.header.Polaris-Realm", "default")
        .config(f"spark.sql.catalog.{settings.CATALOG}.header.X-Iceberg-Access-Delegation", "vended-credentials")
        .config(f"spark.sql.catalog.{settings.CATALOG}.credential", "root:polarisadmin")
        .config(f"spark.sql.catalog.{settings.CATALOG}.scope", "PRINCIPAL_ROLE:ALL")
        .config(f"spark.sql.catalog.{settings.CATALOG}.token-refresh-enabled", "true")
        .config("spark.rdd.compress", True)
        .config("spark.sql.caseSensitive", True)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
        .config("spark.streaming.stopGracefulOnShutdown", True)
        .config("spark.shuffle.service.removeShuffle", True)
        .config("spark.metrics.namespace", settings.METRIC_NAMESPACE)
        .getOrCreate()
    )

    schema_registry_client = SchemaRegistryClient({"url": settings.SCHEMA_REGISTRY})
    udf_byte2int = spark.udf.register("byte_to_int", lambda x: int.from_bytes(x, byteorder="big", signed=False))

    """
    startingOffsets
    | earliest  | offset 맨 앞부터 가져 오기                 |
    | latest    | offset 마지막 offset 이후 메시지 가져 오기   |
    """
    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.BOOTSTRAP_SERVERS)
        .option("subscribe", ",".join(settings.TOPIC_LIST))
        .option("maxOffsetsPerTrigger", settings.MAX_OFFSETS_PER_TRIGGER)
        .option("startingOffsets", settings.STARTING_OFFSETS)
        .option("failOnDataLoss", False)
        .load()
    )

    """
    Key / Value 포맷
    | 1     | MAGIC BYTE, 항상 \x00 값 사용       |
    | 2~5   | SCHEMA ID, b'\x00\x00\x00\x08'   |
    | 6~    | 실제 메시지 내용                     |
    """
    query = (
        kafka_df.withColumn("key_schema_id", udf_byte2int(F.substring("key", 2, 4)))  # SCHEMA_ID = b'\x00\x00\x00\x08'
        .withColumn("key", F.expr("substring(key, 6, length(key)-5)"))
        .withColumn("value_schema_id", udf_byte2int(F.substring("value", 2, 4)))  # SCHEMA_ID = b'\x00\x00\x00\x08'
        .withColumn("value", F.expr("substring(value, 6, length(value)-5)"))
        .selectExpr("key_schema_id", "value_schema_id", "key", "value", "topic", "offset")
        .writeStream.foreachBatch(lambda batch_df, batch_id: process_batch(batch_df, batch_id, spark, settings))
        .option("checkpointLocation", settings.CHECKPOINT_LOCATION)
        .outputMode("append")
        .trigger(availableNow=True)
        # .trigger(processingTime="5 minutes")
        .start()
    )

    query.awaitTermination()
    spark.stop()
