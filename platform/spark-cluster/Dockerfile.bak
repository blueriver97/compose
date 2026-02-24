# ----------------------------------------------------------------
# 1. Builder Stage: 의존성 다운로드 및 빌드
# ----------------------------------------------------------------
FROM blueriver97/python:3.12 AS builder

ENV TZ=Asia/Seoul
ARG ZOOKEEPER_VERSION
ARG HADOOP_VERSION
ARG SPARK_VERSION
ARG ICEBERG_VERSION
ARG TARGETARCH

WORKDIR /opt

# 패키지 다운로드
COPY download/spark-$SPARK_VERSION-bin-without-hadoop.tgz .
COPY download/hadoop-$HADOOP_VERSION-lean.tar.gz .
COPY download/hadoop-$HADOOP_VERSION-aarch64-lean.tar.gz .
COPY download/apache-zookeeper-$ZOOKEEPER_VERSION-bin.tar.gz .
COPY download/$SPARK_VERSION/*.jar /tmp/spark-jars/

# 아키텍처에 따라 Hadoop 압축 해제
RUN case "$TARGETARCH" in \
        arm64) \
            tar --no-same-owner -zxvf hadoop-$HADOOP_VERSION-aarch64-lean.tar.gz; \
            ;; \
        *) \
            tar --no-same-owner -zxvf hadoop-$HADOOP_VERSION-lean.tar.gz; \
            ;; \
    esac && \
    ln -s hadoop-$HADOOP_VERSION hadoop

# Spark, Zookeeper 압축 해제
RUN tar --no-same-owner -zxvf spark-$SPARK_VERSION-bin-without-hadoop.tgz && \
    ln -s spark-$SPARK_VERSION-bin-without-hadoop spark && \
    tar --no-same-owner -zxvf apache-zookeeper-$ZOOKEEPER_VERSION-bin.tar.gz && \
    ln -s apache-zookeeper-$ZOOKEEPER_VERSION-bin zookeeper

# 불필요한 파일 제거
RUN rm -rf \
    /opt/spark/examples \
    /opt/spark/data \
    /opt/hadoop/share/doc \
    /opt/hadoop/share/hadoop/tools/sources \
    /opt/zookeeper/docs && \
    find /opt -name "*.tgz" -type f -delete && \
    find /opt -name "*.tar.gz" -type f -delete

# ----------------------------------------------------------------
# 2. Final Stage: 최종 이미지 생성
# ----------------------------------------------------------------
FROM blueriver97/python:3.12

ARG HADOOP_VERSION
WORKDIR /opt

ENV TZ=Asia/Seoul
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV SPARK_HOME=/opt/spark
ENV SPARK_CONF_DIR=$SPARK_HOME/conf
ENV PYSPARK_PYTHON=./environment/bin/python
ENV PATH=$SPARK_HOME/sbin:$SPARK_HOME/bin:$HADOOP_HOME/sbin:$HADOOP_HOME/bin:$JAVA_HOME/bin:$PATH
# HADOOP_CLASSPATH=`hadoop classpath`


# Builder 스테이지에서 필요한 파일만 복사
COPY --from=builder /opt/spark /opt/spark
COPY --from=builder /opt/hadoop /opt/hadoop
COPY --from=builder /opt/zookeeper /opt/zookeeper
COPY --from=builder /tmp/spark-jars /opt/spark/jars

# Hadoop/Spark 연동에 필요한 파일 복사
# lean 버전 사용 시, /opt/spark/jars 에서 aws 관련 jar를 /opt/hadoop/share/hadoop/tools/lib/ 아래로 복사 필요
# POSIX sh/bash 호환을 위한 case 구문 사용 (블록 종료기호: ;;)
RUN cp /opt/spark/yarn/*.jar /opt/hadoop/share/hadoop/yarn/lib/ && \
    cp /opt/hadoop/share/hadoop/tools/lib/hadoop-aws-*.jar /opt/spark/jars/ && \
    cp /opt/hadoop/share/hadoop/tools/lib/hadoop-kafka-*.jar /opt/spark/jars/ && \
    case "$HADOOP_VERSION" in \
        3.3*) \
            cp /opt/spark/jars/aws-java-sdk-bundle-*.jar /opt/hadoop/share/hadoop/tools/lib/; \
            ;; \
        3.4*) \
            cp /opt/spark/jars/bundle-*.jar /opt/hadoop/share/hadoop/tools/lib/; \
            ;; \
    esac

# 설정 파일 복사
COPY config/hadoop/* /opt/hadoop/etc/hadoop/
COPY config/spark/* /opt/spark/conf/
COPY config/zookeeper/* /opt/zookeeper/conf/

# 필요한 디렉토리 생성
RUN mkdir -p  \
    /data01/spark /data02/spark \
    /data01/yarn/nm /data02/yarn/nm \
    /data/yarn/nm-recovery \
    /data/zookeeper/snapshot  \
    /data/zookeeper/transaction_log  \
    /var/log/yarn/container-logs  \
    /var/log/zookeeper &&\
    echo -e "export HADOOP_CLASSPATH=$(hadoop classpath)" >> ~/.bashrc

### cron setting
#RUN echo '* * * * * /root/cron.sh >> /root/stdout.log 2>&1\n' > /etc/cron.d/mycron &&\
#    chmod 0644 /etc/cron.d/mycron

### entrypoint script
# COPY entrypoint.sh /root
# RUN  chmod +x /root/entrypoint.sh
