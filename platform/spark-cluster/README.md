# Spark Cluster with Yarn

## S3 연동 방법

---

### MinIO 디렉토리 생성 ([setup.sh](config/setup.sh) 생성 실패 시)

```bash
S3_BUCKET=s3a://my-bucket-name
docker exec admin hadoop fs -mkdir -p $S3_BUCKET/spark/logs
docker exec admin hadoop fs -mkdir -p $S3_BUCKET/spark/staging
docker exec admin hadoop fs -mkdir -p $S3_BUCKET/spark/venv
docker exec admin hadoop fs -mkdir -p $S3_BUCKET/spark/jars
```

### 가상환경 구성 및 패키징 (컨테이너 내부 실행)

```bash
python3 -m venv /opt/pyspark_venv
source /opt/pyspark_venv/bin/activate
(pyspark_venv) pip install -U pip setuptools wheel
(pyspark_venv) pip install pyarrow pandas pydantic-core pydantic pydantic_settings PyMySQL hvac venv-pack confluent-kafka
(pyspark_venv) pip install boto3 attrs orjson httpx cachetools authlib
(pyspark_venv) venv-pack -o /opt/pyspark_venv_$ARCH.tar.gz
```

### JAR Archive 구성 (컨테이너 내부 실행)

```bash
cd /opt/spark/jars
tar -zcvf /opt/spark-libs.tar.gz *
```

### 파일 복사 (컨테이너 내부 실행)

#### MinIO

```bash
hadoop fs -put -f /opt/spark-libs.tar.gz s3a://blueriver-datalake/spark/jars/
hadoop fs -put -f /opt/pyspark_venv_$ARCH.tar.gz s3a://blueriver-datalake/spark/venv/
```

#### AWS S3

```bash
aws s3 cp /opt/spark-libs.tar.gz s3://blueriver-datalake/spark/jars/
aws s3 cp /opt/pyspark_venv_$ARCH.tar.gz s3://blueriver-datalake/spark/venv/
```

## 테스트

---

#### Host ↔︎ Admin 컨테이너 SSH 등록

```bash
cat ~/.ssh/id_ed25519.pub | docker exec -i admin sh -c 'mkdir -p /root/.ssh && cat >> /root/.ssh/authorized_keys'
ssh -p 23 root@localhost
```

#### Spark Submit (컨테이너 내부 실행)

```bash
cd /opt/tests
bash [submit.sh](tests/submit.sh)submit.sh
```

## AWS 인증 관련

---

> Hadoop Yarn 컨테이너 구성 과정에서의 파일 배포 시 (--py-files, spark-libs.tar.gz, pyspark_venv.tar.gz)

[core-site.xml](config/hadoop/core-site.xml) 파일에 AWS S3 인증 정보를 작성.
Yarn 관련 작업에서만 core-site.xml에 작성된 AWS 인증 정보를 참조함.

> Spark Session에서 Glue Catalog 조회 또는 데이터 읽기/쓰기 시

`spark.hadoop.fs.s3a.aws.credentials.provider` 옵션에 작성된 인증 체인(Chain)에 따라 다름.

1. AWS SDK for Java v1 (`com.amazonaws.auth.DefaultAWSCredentialsProviderChain`)

   2025년도 12월 31일 지원 종료, V2 전환 필요

2. AWS SDK for Java v2 (`software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider`)
   1. JAVA System Properties (`aws.region`, `aws.accessKeyId`, `aws.secretKey`)
   2. 환경 변수 (`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_ACCESS_KEY_ID`)
   3. 웹 ID 토큰 및 IAM 역할 ARN (`AWS_WEB_IDENTITY_TOKEN_FILE`, `AWS_ROLE_ARN`)
   4. credentials및 config파일 내 `[default]` 프로필 (`~/.aws/credentials`, `~/.aws/config`)
   5. Amazon ECS 컨테이너 자격 증명
   6. Amazon EC2 인스턴스 IAM 역할에서 제공하는 자격 증명

   ```plain
   software.amazon.awssdk.core.exception.SdkClientException: Unable to load credentials from any of the providers
   in the chain AwsCredentialsProviderChain(credentialsProviders=[SystemPropertyCredentialsProvider(),
   EnvironmentVariableCredentialsProvider(), WebIdentityTokenCredentialsProvider(), ProfileCredentialsProvider(),
   ContainerCredentialsProvider(), InstanceProfileCredentialsProvider()])
   ```

   모든 과정 실패 시 위와 같은 오류 발생

3. `AWS_PROFILE` 환경 변수를 통한 선택적 인증 방법

   선행 조건: AWS 자격 증명(~/.aws/credentials, ~/.aws/config)이 각 노드에 이미 설정 완료되어 있어야 함.

   Airflow에서 SparkSubmitOperator를 통해 Yarn 클러스터로 작업을 제출하는 경우, SPARK_CONF에 AWS_PROFILE을 지정하면 각 노드에서 해당 프로필을 찾아 인증에 사용한다.

   ```python
   submit_job = SparkSubmitOperator(
       conn_id="spark_default",
       task_id="submit_spark_job",
       spark_binary="/opt/spark/bin/spark-submit",
       name=DAG_ID,
       deploy_mode="cluster",
       application="/opt/airflow/src/glue_mysql_to_iceberg.py",
       py_files="/opt/airflow/src/utils.zip",
       conf={
           "spark.yarn.appMasterEnv.AWS_PROFILE": "prod",
           "spark.executorEnv.AWS_PROFILE": "prod"
       },
       env_vars=ENV_VARS
   )
   ```

4. AWS IAM 설정
   1. AmazonS3FullAccess

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:*", "s3-object-lambda:*"],
         "Resource": "*"
       }
     ]
   }
   ```

   2. Glue

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "GlueTableManagement",
         "Effect": "Allow",
         "Action": [
           "glue:GetDatabase",
           "glue:GetTable",
           "glue:CreateTable",
           "glue:GetPartitions",
           "glue:UpdateTable"
         ],
         "Resource": [
           "arn:aws:glue:ap-northeast-2:************:catalog",
           "arn:aws:glue:ap-northeast-2:************:database/*",
           "arn:aws:glue:ap-northeast-2:************:table/*/*"
         ]
       }
     ]
   }
   ```

## 트러블슈팅(Troubleshooting)

---

### 1. spark-without-hadoop 사용 시 YARN 로그가 안 보이는 문제 (without-hadoop은 가능 여부 다시 검증 필요)

1. `spark-with-hadoop` 패키지에서 `slf4j-api-<version>.jar` 파일을 찾음.
2. 해당 JAR 파일을 `spark-without-hadoop` 환경에 추가

### 2. ConnectionRefused

1. 아래 같은 로그가 나타나면, RM을 재시작해본다.

```plain
[2025-09-23, 16:24:34 UTC] {job.py:229} INFO - Heartbeat recovered after 12.14 seconds
[2025-09-23, 16:24:35 UTC] {spark_submit.py:644} INFO - 25/09/23 16:24:35 INFO RetryInvocationHandler: java.net.ConnectException: Call From 8a8e73d6d791/172.80.1.19 to node01:8032 failed on connection exception: java.net.ConnectException: Connection refused; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused, while invoking ApplicationClientProtocolPBClientImpl.getApplicationReport over rm01. Trying to failover immediately.
[2025-09-23, 16:24:35 UTC] {spark_submit.py:644} INFO - 25/09/23 16:24:35 INFO ConfiguredRMFailoverProxyProvider: Failing over to rm02
[2025-09-23, 16:24:35 UTC] {spark_submit.py:644} INFO - 25/09/23 16:24:35 INFO RetryInvocationHandler: java.net.ConnectException: Call From 8a8e73d6d791/172.80.1.19 to node02:8032 failed on connection exception: java.net.ConnectException: Connection refused; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused, while invoking ApplicationClientProtocolPBClientImpl.getApplicationReport over rm02 after 1 failover attempts. Trying to failover after sleeping for 163ms.
[2025-09-23, 16:24:35 UTC] {spark_submit.py:644} INFO - 25/09/23 16:24:35 INFO ConfiguredRMFailoverProxyProvider: Failing over to rm01
[2025-09-23, 16:24:35 UTC] {spark_submit.py:644} INFO - 25/09/23 16:24:35 INFO RetryInvocationHandler: java.net.ConnectException: Call From 8a8e73d6d791/172.80.1.19 to node01:8032 failed on connection exception: java.net.ConnectException: Connection refused; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused, while invoking ApplicationClientProtocolPBClientImpl.getApplicationReport over rm01 after 2 failover attempts. Trying to failover after sleeping for 352ms.
[2025-09-23, 16:24:35 UTC] {spark_submit.py:644} INFO - 25/09/23 16:24:35 INFO ConfiguredRMFailoverProxyProvider: Failing over to rm02
[2025-09-23, 16:24:35 UTC] {spark_submit.py:611} INFO - Identified spark application id: application_1758644046787_0002
```

```bash
$HADOOP_HOME/sbin/yarn-daemon.sh stop resourcemanager
$HADOOP_HOME/sbin/yarn-daemon.sh start resourcemanager
```

### 3. Unable to make protected final java.lang.Class java.lang.ClassLoader.defineClass

- Java 17 이후 더 엄격해진 모듈 접근 제한으로 인해, java.base/java.lang 모듈 내부를 외부 모듈에서는 기본 접근 불가하게 되어 발생될 수 있다.
- Hadoop 3.3.6의 경우 Java 11까지 지원하며, Java 17 지원에 대한 논의가 진행중인 것으로
  확인된다. (https://issues.apache.org/jira/browse/HADOOP-18887)
- 해당 이슈에 대해 일반적인 해결책으로는 아래와 같이 옵션을 추가하는 방법이 있다.

```bash
# /opt/hadoop/etc/hadoop/hadoop-env.sh
export HADOOP_OPTS="$HADOOP_OPTS --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.lang.reflect=ALL-UNNAMED"
```

```plain
2025-09-27 17:38:38,941 ERROR org.apache.hadoop.yarn.server.resourcemanager.ResourceManager: Error starting ResourceManager
java.lang.ExceptionInInitializerError
        at com.google.inject.internal.cglib.reflect.$FastClassEmitter.<init>(FastClassEmitter.java:67)
        at com.google.inject.internal.cglib.reflect.$FastClass$Generator.generateClass(FastClass.java:72)
        at com.google.inject.internal.cglib.core.$DefaultGeneratorStrategy.generate(DefaultGeneratorStrategy.java:25)
        at com.google.inject.internal.cglib.core.$AbstractClassGenerator.create(AbstractClassGenerator.java:216)
        at com.google.inject.internal.cglib.reflect.$FastClass$Generator.create(FastClass.java:64)
        at com.google.inject.internal.BytecodeGen.newFastClass(BytecodeGen.java:204)
        at com.google.inject.internal.ProviderMethod$FastClassProviderMethod.<init>(ProviderMethod.java:256)
        at com.google.inject.internal.ProviderMethod.create(ProviderMethod.java:71)
        at com.google.inject.internal.ProviderMethodsModule.createProviderMethod(ProviderMethodsModule.java:275)
        at com.google.inject.internal.ProviderMethodsModule.getProviderMethods(ProviderMethodsModule.java:144)
        at com.google.inject.internal.ProviderMethodsModule.configure(ProviderMethodsModule.java:123)
        at com.google.inject.spi.Elements$RecordingBinder.install(Elements.java:340)
        at com.google.inject.spi.Elements$RecordingBinder.install(Elements.java:349)
        at com.google.inject.AbstractModule.install(AbstractModule.java:122)
        at com.google.inject.servlet.ServletModule.configure(ServletModule.java:52)
        at com.google.inject.AbstractModule.configure(AbstractModule.java:62)
        at com.google.inject.spi.Elements$RecordingBinder.install(Elements.java:340)
        at com.google.inject.spi.Elements.getElements(Elements.java:110)
        at com.google.inject.internal.InjectorShell$Builder.build(InjectorShell.java:138)
        at com.google.inject.internal.InternalInjectorCreator.build(InternalInjectorCreator.java:104)
        at com.google.inject.Guice.createInjector(Guice.java:96)
        at com.google.inject.Guice.createInjector(Guice.java:73)
        at com.google.inject.Guice.createInjector(Guice.java:62)
        at org.apache.hadoop.yarn.webapp.WebApps$Builder.build(WebApps.java:417)
        at org.apache.hadoop.yarn.webapp.WebApps$Builder.start(WebApps.java:465)
        at org.apache.hadoop.yarn.server.resourcemanager.ResourceManager.startWepApp(ResourceManager.java:1389)
        at org.apache.hadoop.yarn.server.resourcemanager.ResourceManager.serviceStart(ResourceManager.java:1498)
        at org.apache.hadoop.service.AbstractService.start(AbstractService.java:194)
        at org.apache.hadoop.yarn.server.resourcemanager.ResourceManager.main(ResourceManager.java:1700)
Caused by: java.lang.reflect.InaccessibleObjectException: Unable to make protected final java.lang.Class java.lang.ClassLoader.defineClass(java.lang.String,byte[],int,int,java.security.ProtectionDomain) throws java.lang.ClassFormatError accessible: module java.base does not "opens java.lang" to unnamed module @d41f816
        at java.base/java.lang.reflect.AccessibleObject.checkCanSetAccessible(AccessibleObject.java:354)
        at java.base/java.lang.reflect.AccessibleObject.checkCanSetAccessible(AccessibleObject.java:297)
        at java.base/java.lang.reflect.Method.checkCanSetAccessible(Method.java:200)
        at java.base/java.lang.reflect.Method.setAccessible(Method.java:194)
        at com.google.inject.internal.cglib.core.$ReflectUtils$2.run(ReflectUtils.java:56)
        at java.base/java.security.AccessController.doPrivileged(AccessController.java:318)
        at com.google.inject.internal.cglib.core.$ReflectUtils.<clinit>(ReflectUtils.java:46)
        ... 29 more
```

### 4. Caused by: java.io.IOException: Cannot run program "./environment/bin/python": error=2, No such file or directory

- 해당 Spark Cluster의 구성은 AWS S3에 업로드된 pyspark_venv.tar.gz를 다운로드 받아 사용한다.
- 이 경우, pyspark_venv.tar.gz 내 ./environment/bin/python의 심볼릭 링크가 이미지에 설치된 python3의 경로와 맞지 않아 python3을 찾지 못해 발생될 수 있다.
- README.md 내용을 따라 다시 pyspark_venv.tar.gz를 구성해 업로드하면 된다.

### 5. Caused by: java.lang.ClassNotFoundException: org.slf4j.spi.LoggingEventBuilder

- Spark 4.0.1 / Hadoop 3.4.2-lean 조합에서 /opt/spark/jar/ 경로에 slf4j-api-\*.jar 파일이 없어서 발생하는 이슈
- Spark 4.0.1은 SLF4J 2.x API(org.slf4j.spi.LoggingEventBuilder 포함)를 필요로 함.
- log4j-slf4j2-impl-2.24.3.jar는 바인더 역할만 하기 때문에 라이브러리(slf4j-api-2.x)가 없으면 동작하지 않음.

```
starting org.apache.spark.deploy.history.HistoryServer, logging to /opt/spark/logs/spark-root-org.apache.spark.deploy.history.HistoryServer-1-admin.out
starting org.apache.spark.sql.connect.service.SparkConnectServer, logging to /opt/spark/logs/spark-root-org.apache.spark.sql.connect.service.SparkConnectServer-1-admin.out
failed to launch: nice -n 0 bash /opt/spark/bin/spark-submit --class org.apache.spark.sql.connect.service.SparkConnectServer --name Spark Connect server
        at org.apache.spark.deploy.SparkSubmit$$anon$2.parseArguments(SparkSubmit.scala:1101)
        at org.apache.spark.deploy.SparkSubmit.doSubmit(SparkSubmit.scala:72)
        at org.apache.spark.deploy.SparkSubmit$$anon$2.doSubmit(SparkSubmit.scala:1132)
        at org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:1141)
        at org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)
  Caused by: java.lang.ClassNotFoundException: org.slf4j.spi.LoggingEventBuilder
        at java.base/jdk.internal.loader.BuiltinClassLoader.loadClass(BuiltinClassLoader.java:641)
        at java.base/jdk.internal.loader.ClassLoaders$AppClassLoader.loadClass(ClassLoaders.java:188)
        at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:525)
        ... 24 more
full log in /opt/spark/logs/spark-root-org.apache.spark.sql.connect.service.SparkConnectServer-1-admin.out
```

### 6.Exception in thread "main" java.lang.NoSuchMethodError: 'java.lang.Object org.apache.logging.log4j.util.LoaderUtil.newCheckedInstanceOfProperty(java.lang.String, java.lang.Class, java.util.function.Supplier)'

- Spark 작업 실행 중 LoaderUtil 클래스 내 newCheckedInstanceOfProperty 메서드를 호출하는데, 포함된 log4j 의존성에 해당 메서드가 없는 버전의 jar가 포함되어 나타나는
  이슈.
- 기본적으로 Spark 4.0.1은 2.24.3 버전의 log4j 라이브러리를 사용하므로, 2.20 버전에 추가된 newCheckedInstanceOfProperty(java.lang.String,
  java.lang.Class, java.util.function.Supplier) 메서드가 존재해야 한다.
- 여기서 문제가 되는 부분이 iceberg-aws-bundle.jar인데, 1.10.0 버전 기준으로 이전 버전의 log4j 라이브러리가 포함되어 있어, 의존성 설정 과정에서 spark의 의존성 대신
  iceberg-aws-bundle의 의존성이 먼저 설정되면 이 이슈가 발생한다.
- 관련하여 https://github.com/apache/gravitino/issues/8949 유사한 이슈가 gravitino 저장소 이슈에 등록되어 있다.
- 이에 iceberg-aws-bundle.jar를 사용하지 않고, iceberg-aws.jar를 사용하였으며, iceberg에서 참조하는 AWS SDK v2 의존성으로 bundle-\*.jar를 별도로
  포함하였다. (원래도 bundle.jar는 필요함)

```
Exception in thread "main" java.lang.NoSuchMethodError: 'java.lang.Object org.apache.logging.log4j.util.LoaderUtil.newCheckedInstanceOfProperty(java.lang.String, java.lang.Class, java.util.function.Supplier)'
        at org.apache.logging.log4j.core.LoggerContext.createInstanceFromFactoryProperty(LoggerContext.java:115)
        at org.apache.logging.log4j.core.LoggerContext.<clinit>(LoggerContext.java:93)
        at org.apache.logging.log4j.core.selector.ClassLoaderContextSelector.createContext(ClassLoaderContextSelector.java:265)
        at org.apache.logging.log4j.core.selector.ClassLoaderContextSelector.lambda$new$0(ClassLoaderContextSelector.java:57)
        at org.apache.logging.log4j.util.LazyUtil$SafeLazy.value(LazyUtil.java:113)
        at org.apache.logging.log4j.util.Lazy.get(Lazy.java:39)
        at org.apache.logging.log4j.core.selector.ClassLoaderContextSelector.getDefault(ClassLoaderContextSelector.java:273)
        at org.apache.logging.log4j.core.selector.ClassLoaderContextSelector.getContext(ClassLoaderContextSelector.java:152)
        at org.apache.logging.log4j.core.selector.ClassLoaderContextSelector.getContext(ClassLoaderContextSelector.java:125)
        at org.apache.logging.log4j.core.impl.Log4jContextFactory.getContext(Log4jContextFactory.java:241)
        at org.apache.logging.log4j.core.impl.Log4jContextFactory.getContext(Log4jContextFactory.java:46)
        at org.apache.logging.log4j.LogManager.getContext(LogManager.java:176)
        at org.apache.logging.log4j.LogManager.getLogger(LogManager.java:666)
        at org.apache.logging.log4j.LogManager.getRootLogger(LogManager.java:700)
        at org.apache.spark.internal.Logging.initializeLogging(Logging.scala:333)
        at org.apache.spark.internal.Logging.initializeLogIfNecessary(Logging.scala:318)
        at org.apache.spark.internal.Logging.initializeLogIfNecessary$(Logging.scala:312)
        at org.apache.spark.deploy.yarn.ApplicationMaster$.initializeLogIfNecessary(ApplicationMaster.scala:880)
        at org.apache.spark.internal.Logging.initializeLogIfNecessary(Logging.scala:309)
        at org.apache.spark.internal.Logging.initializeLogIfNecessary$(Logging.scala:308)
        at org.apache.spark.deploy.yarn.ApplicationMaster$.initializeLogIfNecessary(ApplicationMaster.scala:880)
        at org.apache.spark.internal.Logging.log(Logging.scala:139)
        at org.apache.spark.internal.Logging.log$(Logging.scala:137)
        at org.apache.spark.deploy.yarn.ApplicationMaster$.log(ApplicationMaster.scala:880)
        at org.apache.spark.deploy.yarn.ApplicationMaster$.main(ApplicationMaster.scala:895)
        at org.apache.spark.deploy.yarn.ApplicationMaster.main(ApplicationMaster.scala)
```

### 7. Spark 작업 Log의 출력이 stderr ↔︎ stdout 서로 바뀌어서 출력되는 현상

- Spark는 기본적으로 Spark 작업 로그(INFO, WARN 포함)가 stderr로 향하도록 기본 설정되어 있다.
- 실제로 log4j2.properties 템플릿 파일 내용을 살펴보면 `appender.console.target = SYSTEM_ERR` 부분에서 로그 방향이 SYSTEM_ERR로 설정되어 있는 것을 확인할 수
  있다.
- 이 값을 SYSTEM_ERR에서 SYSTEM_OUT으로 변경할 경우, Spark 작업 로그가 stdout 채널에 출력된다.
- 이렇게 설정된 이유를 추측해보면, 사용자가 print() 함수 등으로 직접 출력하는 내용을 stdout에 보여주고, 그 외 작업 로그를 stderr로 전달해서 용도를 분리하려는게 아닐까 싶다.

### 8. PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target

- Java 애플리케이션이 외부 서버와 HTTPS 통신을 할 때 발생하는 문제로, 서버가 제시한 SSL 인증서를 Java의 신뢰 저장소(Truststore)에서 검증할 수 없어서 발생하는 보안 예외이다.
- 검증되지 않은 인증서 및 자체 서명 인증서를 사용하거나 사내 프록시나 방화벽이 SSL 트래픽을 가로채기 위해 중간 인증서를 삽입하면서 발생될 수 있다.
- 가장 권장되는 해결책은 문제가 되는 해당 인증서(root CA 인증서, Intermediate 인증서)를 Java의 cacerts 파일에 추가하는 것이다.
- [setup.sh](config/setup.sh) 내용 참조
  ```bash
  echo "INFO: Registering Staging SSL Certificate..."
  STAGING_CERT_PATH="/tmp/ssl/letsencrypt-stg-root-x1.pem" # 실제 경로에 맞춰 수정 필요
  TRUSTSTORE_PATH="$JAVA_HOME/lib/security/cacerts"
  CERT_ALIAS="letsencrypt-staging-root"
  if [ -f "$STAGING_CERT_PATH" ]; then
      # 인증서가 이미 Java Truststore에 등록되어 있는지 확인
      keytool -list -keystore "$TRUSTSTORE_PATH" -storepass changeit -alias "$CERT_ALIAS" > /dev/null 2>&1
      if [ $? -eq 0 ]; then
          echo "INFO: SSL Certificate '$CERT_ALIAS' already exists in truststore."
      else
          # 인증서 등록 수행 (관리자 권한 필요)
          keytool -importcert -trustcacerts -keystore "$TRUSTSTORE_PATH" \
                  -storepass changeit -alias "$CERT_ALIAS" -file "$STAGING_CERT_PATH" -noprompt
          echo "INFO: SSL Certificate '$CERT_ALIAS' has been successfully registered."
      fi
  else
      echo "WARN: Staging certificate file not found at $STAGING_CERT_PATH. Skipping registration."
  fi
  ```

### 9. Concurrent update to the log. Multiple streaming jobs detected for <offset_number>.

```plain
checkpoint/
├── offsets/      # 각 배치에서 읽기로 결정한 오프셋 로그 (WAL)
│   ├── 0
│   ├── 1
│   └── 284       # 현재 문제가 된 그 파일
├── commits/      # 처리가 완료된 배치 목록
│   ├── 0
│   ├── 1
│   └── 283       # 284가 여기 없으면 재처리 대상, 만약 이미 284가 있다면 [CONCURRENT_STREAM_LOG_UPDATE] 오류 발생
├── metadata      # Query ID 등 쿼리 고유 정보
└── sources/      # Kafka 특정 정보 (Topic, Partition 수 등)
```

- Kafka에서 메시지를 읽어 Spark Streaming으로 처리할 때 발생하는 오류로, offset과 commit의 시퀀스 불일치가 주요 원인이다.
- **배치 시작 단계**: Spark는 Kafka에서 읽어올 시작 오프셋과 종료 오프셋을 결정한다. 이 정보는 체크포인트 디렉토리의 `offsets/` 폴더에 배치 번호(예: 284)로 기록된다.
- **데이터 처리 단계**: 설정된 오프셋 범위만큼 Kafka에서 데이터를 가져와 변환 작업을 수행한 후 저장소에 저장한다. 저장이 완료되면 `commits/` 폴더에 동일한 배치 번호(284) 파일을 생성하여
  처리 완료를 표시한다.
- **오류 발생 조건**: `offsets/`에 기록되지 않은 배치 번호가 `commits/`에만 존재할 경우 이 오류가 발생한다. 이는 동일한 배치에 대해 중복된 스트리밍 작업이 감지되었음을 의미한다.
- **재처리 메커니즘**: `offsets/`에는 존재하지만 `commits/`에는 없는 배치의 경우, Spark는 해당 오프셋 구간을 재처리하고 완료 후 `commits/`에 기록한다.

```plain
26/01/08 17:07:22 ERROR MicroBatchExecution: Query [id = 28c7b2a1-b805-4575-8235-82e741ad1b7f, runId = af193f90-c6f8-4387-ab1e-805685f11630] terminated with error
org.apache.spark.SparkException: [CONCURRENT_STREAM_LOG_UPDATE] Concurrent update to the log. Multiple streaming jobs detected for 284.
Please make sure only one streaming job runs on a specific checkpoint location at a time. SQLSTATE: 40000
```

---

## Appendix

- https://spark.apache.org/docs/latest/running-on-yarn.html
