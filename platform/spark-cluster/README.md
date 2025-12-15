# Spark Cluster with Yarn

## S3 연동 방법

---

### MinIO 디렉토리 생성 ([setup.sh](config/setup.sh) 생성 실패 시)

```bash
docker exec admin hadoop fs -mkdir -p s3a://datalake/spark/logs
docker exec admin hadoop fs -mkdir -p s3a://datalake/spark/staging
docker exec admin hadoop fs -mkdir -p s3a://datalake/spark/venv
docker exec admin hadoop fs -mkdir -p s3a://datalake/spark/jars
```

### 가상환경 생성

```bash
python3 -m venv /opt/pyspark_venv
```

### 가상환경 구성 및 패키징

```bash
source /opt/pyspark_venv/bin/activate
(pyspark_venv) pip install -U pip setuptools wheel
(pyspark_venv) pip install pyarrow pandas pydantic pydantic_settings PyMySQL hvac venv-pack confluent-kafka
(pyspark_venv) pip install boto3 attrs orjson httpx cachetools authlib
(pyspark_venv) venv-pack -o /opt/pyspark_venv.tar.gz
```

### JAR Archive 구성

```bash
cd /opt/spark/jars
tar -zcvf /opt/spark-libs.tar.gz *
```

### 파일 복사

#### MinIO

```bash
hadoop fs -put /opt/spark-libs.tar.gz s3a://datalake/spark/jars/
hadoop fs -put /opt/pyspark_venv.tar.gz s3a://datalake/spark/venv/
```

#### AWS S3

```bash
aws s3 cp /opt/spark-libs.tar.gz s3://datalake/spark/jars/
aws s3 cp /opt/pyspark_venv.tar.gz s3://datalake/spark/venv/
```

## 테스트

---

```bash
/opt/spark/bin/spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --class org.apache.spark.examples.SparkPi \
  --num-executors 1 \
  --executor-cores 1 \
  --executor-memory 2G \
  --driver-memory 2G \
  $SPARK_HOME/examples/jars/spark-examples_2.12-3.5.6.jar \
  10
```

---

## AWS 인증 관련 테스트

|     | core-site.xml | env               | $HOME/.aws | spark.yarn.appMasterEnv | Accepted | Running |
| --- | ------------- | ----------------- | ---------- | ----------------------- | -------- | ------- |
| 1   | O             | X                 | X          |                         | ✅       | ✅      |
| 2   | X             | X                 | O          |                         | ❌       | ❌      |
| 3   | X             | O                 | X          |                         | ✅       | ❌      |
| 4   | X             | O                 | X          | O                       | ✅       | ✅      |
| 5   | X             | O                 | O          |                         | ✅       | ❌      |
| 6   | X             | O                 | O          | O                       | ✅       | ✅      |
| 7   | X             | X(spark-submit O) | X          |                         | ✅       | ❌      |
| 8   | X             | X(spark-submit O) | X          | O                       | ✅       | ❌      |

**성공 케이스 1)** core-site.xml에 인증 정보 설정

**성공 케이스 2)** 전체 노드에 AWS ENV 구성 후, Submit 시 spark.yarn.appMasterEnv 옵션으로 AWS 인증 전달

- `$HOME/.aws`는 아무런 영향을 주지 않음.

---

## 이슈

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
