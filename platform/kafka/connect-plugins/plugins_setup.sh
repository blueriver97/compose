#!/bin/bash

# .env 파일 읽기 (다운로드 스크립트와 동일한 변수 설정을 위해)
echo "Reading .env file to determine file names..."
while IFS='=' read -r key value; do
    if [[ $key == "DEBEZIUM_VERSION" ]]; then
        DEBEZIUM_VERSION=$value
    elif [[ $key == "GROOVY_VERSION" ]]; then
        GROOVY_VERSION=$value
    elif [[ $key == "ICEBERG_VERSION" ]]; then
        ICEBERG_VERSION=$value
    fi
done < ../.env

# 변수가 올바르게 로드되었는지 확인
if [ -z "$DEBEZIUM_VERSION" ] || [ -z "$GROOVY_VERSION" ] || [ -z "$ICEBERG_VERSION" ]; then
    echo "Error: DEBEZIUM_VERSION or GROOVY_VERSION or ICEBERG_VERSION could not be read from .env file."
    exit 1
fi

echo "DEBEZIUM_VERSION=$DEBEZIUM_VERSION"
echo "GROOVY_VERSION=$GROOVY_VERSION"
echo "ICEBERG_VERSION=$ICEBERG_VERSION"
echo ""

# 대상 디렉터리 생성
echo "Creating 'source' and 'sink' directories if they don't exist..."
mkdir -p source sink

# 다운로드된 파일 목록 정의
# This list should match the files from your download script.
declare -a downloaded_files=(
  "debezium-connector-mysql-$DEBEZIUM_VERSION.Final-plugin.tar.gz"
  "debezium-connector-sqlserver-$DEBEZIUM_VERSION.Final-plugin.tar.gz"
  "confluentinc-kafka-connect-s3-11.0.2.zip"
  "apache-iceberg-$ICEBERG_VERSION.tar.gz"
  "debezium-scripting-$DEBEZIUM_VERSION.Final.tar.gz"
  "groovy-$GROOVY_VERSION.jar"
  "groovy-jsr223-$GROOVY_VERSION.jar"
  "groovy-json-$GROOVY_VERSION.jar"
)

# 각 파일을 적절한 디렉터리로 이동 또는 압축 해제
echo "Starting to organize connector plugins and libraries..."
for file in "${downloaded_files[@]}"; do
    # 파일이 존재하는지 먼저 확인
    if [ ! -f "$file" ]; then
        echo "Warning: File '$file' not found. Skipping."
        continue
    fi

    case "$file" in
        *debezium-connector-mysql* | *debezium-connector-sqlserver* | *apache-iceberg*)
            # Debezium Source Connectors and scripting library
            echo "Extracting Source Plugin: $file -> to source/"
            tar -xzf "$file" -C ./source/
            ;;
        *debezium-scripting*)
            # Debezium scripting library
            echo "Extracting Source Plugin: $file -> to source/"
            tar -xzf "$file" -C ./source/
            cp ./source/debezium-scripting/*.jar ./source/debezium-connector-mysql/
            cp ./source/debezium-scripting/*.jar ./source/debezium-connector-sqlserver/

            rm -rf ./source/debezium-scripting
            ;;

        *groovy*)
            # Groovy jars are dependencies for Debezium scripting
            echo "Moving Source Dependency: $file -> to source/"
            cp "$file" ./source/debezium-connector-mysql/
            cp "$file" ./source/debezium-connector-sqlserver/
            ;;
        *kafka-connect-s3* | *iceberg-kafka-connect*)
            # Sink Connectors
            echo "Extracting Sink Plugin: $file -> to sink/"
            # Use -o to overwrite files without prompting
            unzip -o "$file" -d ./sink/
            ;;
        *)
            # Handle unknown files
            echo "Warning: Don't know how to handle '$file'. Skipping."
            ;;
    esac
done

echo ""
echo "File organization complete."
echo "Please check the 'source' and 'sink' directories for the results."
