#!/bin/bash

echo "Replace env in core-site.xml ..."
sed -i "s#\$S3_BUCKET#$S3_BUCKET#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#\$AWS_ENDPOINT_URL_S3#$AWS_ENDPOINT_URL_S3#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#\$AWS_ACCESS_KEY_ID#$AWS_ACCESS_KEY_ID#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#\$AWS_SECRET_ACCESS_KEY#$AWS_SECRET_ACCESS_KEY#g" /opt/hadoop/etc/hadoop/core-site.xml

echo "Replace env in yarn-site.xml ..."
sed -i "s#\$YARN_RM1_WEBAPP_ADDR#$YARN_RM1_WEBAPP_ADDR#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#\$YARN_RM2_WEBAPP_ADDR#$YARN_RM2_WEBAPP_ADDR#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#\$YARN_NM_WEBAPP_ADDR#$YARN_NM_WEBAPP_ADDR#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#\$YARN_NM_USER_HOME_DIR#$YARN_NM_USER_HOME_DIR#g" /opt/hadoop/etc/hadoop/yarn-site.xml

echo "Replace env in spark-defaults.conf ..."
sed -i "s#\$S3_BUCKET#$S3_BUCKET#g" /opt/spark/conf/spark-defaults.conf

echo "Prepare dir in $S3_BUCKET"
hadoop fs -mkdir -p $S3_BUCKET/spark/logs
hadoop fs -mkdir -p $S3_BUCKET/spark/staging
hadoop fs -mkdir -p $S3_BUCKET/spark/venv
hadoop fs -mkdir -p $S3_BUCKET/spark/jars
