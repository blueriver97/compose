import datetime
from airflow.models import DAG, Variable
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# DAG 설정
DAG_ID = "kafka_to_iceberg_batch"
# 처리할 테이블 리스트 (빈 튜플로 초기화)
TABLES = (
    "store.tb_lower,"
    "store.TB_UPPER,"
    "store.TB_COMPOSITE_KEY"
)

# Spark 설정
SPARK_CONF = {
    "spark.yarn.maxAppAttempts": "1",
    "spark.driver.cores": "1",
    "spark.driver.memory": "1G",
    "spark.executor.cores": "1",
    "spark.executor.memory": "1G",
    "spark.executor.instances": "1",
}

# 환경 변수
AWS_PROFILE = "dev"
S3_BUCKET = Variable.get("S3_BUCKET")
BOOTSTRAP_SERVERS = Variable.get("BOOTSTRAP_SERVERS")
SCHEMA_REGISTRY = Variable.get("SCHEMA_REGISTRY")
VAULT_URL = Variable.get("VAULT_URL")
VAULT_USERNAME = Variable.get("VAULT_USERNAME")
VAULT_PASSWORD = Variable.get("VAULT_PASSWORD")
VAULT_SECRET_PATH = "secret/data/user/database/local-mysql"
HADOOP_CONF_DIR = Variable.get("HADOOP_CONF_DIR")
SPARK_HOME = Variable.get("SPARK_HOME")
PYSPARK_PYTHON = Variable.get("PYSPARK_PYTHON")
TOPIC_PREFIX = "local"

ENV_VARS = {
    "AWS_PROFILE": AWS_PROFILE,
    "S3_BUCKET": S3_BUCKET,
    "BOOTSTRAP_SERVERS": BOOTSTRAP_SERVERS,
    "SCHEMA_REGISTRY": SCHEMA_REGISTRY,
    "CATALOG": "glue_catalog",
    "TOPIC_PREFIX": TOPIC_PREFIX,
    "METRIC_NAMESPACE": DAG_ID,
    "TABLES": TABLES,
    "ICEBERG_S3_ROOT_PATH": f"s3a://{S3_BUCKET}/iceberg/biz/core",
    "CHECKPOINT_LOCATION": f"s3a://{S3_BUCKET}/iceberg/checkpoint/{DAG_ID}",
    "VAULT_URL": VAULT_URL,
    "VAULT_USERNAME": VAULT_USERNAME,
    "VAULT_PASSWORD": VAULT_PASSWORD,
    "VAULT_SECRET_PATH": VAULT_SECRET_PATH,
    "HADOOP_CONF_DIR": HADOOP_CONF_DIR,
    "SPARK_HOME": SPARK_HOME,
    "PYSPARK_PYTHON": PYSPARK_PYTHON,
}

# DAG 정의
with DAG(
        dag_id=DAG_ID,
        description="Batch job to process Kafka topics and write to Iceberg using Spark",
        start_date=datetime.datetime(2025, 9, 21),
        schedule=None,
        catchup=False,
        max_active_runs=1,
        tags=[],
) as dag:
    submit_spark_job = SparkSubmitOperator(
        conn_id="spark_default",
        task_id="submit_spark_job",
        spark_binary="/opt/spark/bin/spark-submit",
        name=DAG_ID,
        deploy_mode="cluster",
        application="/opt/airflow/src/polaris_kafka_to_iceberg_batch.py",
        py_files="/opt/airflow/src/utils.zip",
        conf=SPARK_CONF,
        env_vars=ENV_VARS
    )
