#!/bin/bash

echo "INFO: Replace env in core-site.xml ..."
sed -i "s#\$S3_BUCKET#$S3_BUCKET#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#\$AWS_ENDPOINT_URL_S3#$AWS_ENDPOINT_URL_S3#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#\$AWS_ACCESS_KEY_ID#$AWS_ACCESS_KEY_ID#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#\$AWS_SECRET_ACCESS_KEY#$AWS_SECRET_ACCESS_KEY#g" /opt/hadoop/etc/hadoop/core-site.xml

echo "INFO: Replace env in yarn-site.xml ..."
sed -i "s#\$YARN_RM1_WEBAPP_ADDR#$YARN_RM1_WEBAPP_ADDR#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#\$YARN_RM2_WEBAPP_ADDR#$YARN_RM2_WEBAPP_ADDR#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#\$YARN_NM_WEBAPP_ADDR#$YARN_NM_WEBAPP_ADDR#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#\$YARN_NM_USER_HOME_DIR#$YARN_NM_USER_HOME_DIR#g" /opt/hadoop/etc/hadoop/yarn-site.xml

echo "INFO: Replace env in spark-defaults.conf ..."
sed -i "s#\$S3_BUCKET#$S3_BUCKET#g" /opt/spark/conf/spark-defaults.conf
sed -i "s#\$ARCH#$ARCH#g" /opt/spark/conf/spark-defaults.conf

#echo "INFO: Registering Staging SSL Certificate..."
#STAGING_CERT_PATH="/tmp/ssl/letsencrypt-stg-root-x1.pem" # 실제 경로에 맞춰 수정 필요
#TRUSTSTORE_PATH="$JAVA_HOME/lib/security/cacerts"
#CERT_ALIAS="letsencrypt-staging-root"
#if [ -f "$STAGING_CERT_PATH" ]; then
#    # 인증서가 이미 Java Truststore에 등록되어 있는지 확인
#    keytool -list -keystore "$TRUSTSTORE_PATH" -storepass changeit -alias "$CERT_ALIAS" > /dev/null 2>&1
#    if [ $? -eq 0 ]; then
#        echo "INFO: SSL Certificate '$CERT_ALIAS' already exists in truststore."
#    else
#        # 인증서 등록 수행 (관리자 권한 필요)
#        keytool -importcert -trustcacerts -keystore "$TRUSTSTORE_PATH" \
#                -storepass changeit -alias "$CERT_ALIAS" -file "$STAGING_CERT_PATH" -noprompt
#        echo "INFO: SSL Certificate '$CERT_ALIAS' has been successfully registered."
#    fi
#else
#    echo "WARN: Staging certificate file not found at $STAGING_CERT_PATH. Skipping registration."
#fi

# 생성할 디렉토리 리스트 정의
echo "INFO: Preparing directories in $S3_BUCKET"
TARGET_DIRS=(
    "$S3_BUCKET/spark/logs"
    "$S3_BUCKET/spark/staging"
    "$S3_BUCKET/spark/venv"
    "$S3_BUCKET/spark/jars"
)

for dir in "${TARGET_DIRS[@]}"; do
    # hadoop fs -test -d: 디렉토리가 존재하면 0 반환
    if hadoop fs -test -d "$dir" 2>/dev/null; then
        echo "INFO: Directory already exists: $dir"
    else
        # 디렉토리 생성 수행
        if hadoop fs -mkdir -p "$dir"; then
            echo "INFO: Directory created successfully: $dir"
        else
            echo "ERROR: Failed to create directory: $dir"
        fi
    fi
done

echo "INFO: All tasks completed successfully."
