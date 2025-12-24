/opt/spark/bin/spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --num-executors 1 \
  --executor-cores 1 \
  --executor-memory 2G \
  --driver-memory 2G \
  --conf spark.yarn.maxAppAttempts=1 \
  test_iceberg_polaris_catalog.py
