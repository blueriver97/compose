# Airflow

Apache Airflow는 프로그래밍 방식으로 워크플로우를 작성, 스케줄링 및 모니터링하는 오픈소스 플랫폼입니다.

주요 특징

- Python으로 작성된 DAG(Directed Acyclic Graph)를 통한 워크플로우 정의
- 웹 UI를 통한 작업 모니터링 및 관리
- 다양한 외부 시스템과의 통합을 위한 풍부한 Operator 제공
- 확장 가능한 아키텍처로 커스텀 기능 구현 가능
- 실패한 태스크의 재시도 및 복구 기능 제공
- 워크플로우 버전 관리 및 테스트 지원

활용 사례

- ETL/ELT 파이프라인 자동화
- 머신러닝 모델 학습 및 배포
- 데이터 웨어하우스 적재 작업
- 정기적인 리포트 생성
- 배치 작업 스케줄링

## 커스텀 이미지 빌드 (Building Custom Images)

---

- 기본 apache/airflow:3.x 이미지에 JAVA와 Spark 바이너리를 설치합니다.
- SparkSubmitOperator는 로컬 spark-submit 스크립트를 호출하므로 Worker 노드에 Spark 클라이언트가 필요합니다.
- [Dockerfile](Dockerfile)을 참조합니다.

```bash
docker-compose build --no-cache
```

### 의존성 (Dependencies)

- astronomer-cosmos는 Airflow에서 dbt를 Task Group으로 렌더링하기 위한 라이브러리입니다.
- apache-airflow-providers-apache-spark는 Spark 연동 오퍼레이터입니다.
- dbt-core, dbt-athena는 dbt 프로젝트 실행에 필요한 라이브러리입니다.

### UID 설정

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

## 환경변수 설정 (Airflow Configuration)

---

`AIRFLOW__API__EXPOSE_CONFIG`: Airflow 내 설정 페이지 접근 허용

# Apache Airflow 배포 및 운영 가이드

이 문서는 Docker Compose를 사용하여 Apache Airflow, Spark, Hadoop(S3 연동 포함) 환경을 구성하고 운영하기 위한 가이드입니다.

특히 최근 업데이트된 **AWS 인증 방식 변경**과 **Hadoop 버전 업그레이드**에 따른 주의사항 및 해결 방법을 포함하고 있습니다.

<!-- TOC -->

- [Apache Airflow 배포 및 운영 가이드](#apache-airflow-배포-및-운영-가이드)
  - [1. 업데이트 개요 (필독)](#1-업데이트-개요-필독)
  - [2. 주요 변경사항 및 주의사항](#2-주요-변경사항-및-주의사항)
    - [2.1. AWS 인증 방식 변경: `.env` 파일 중앙 관리](#21-aws-인증-방식-변경-env-파일-중앙-관리)
    - [2.2. Hadoop 및 의존성 라이브러리 버전 변경](#22-hadoop-및-의존성-라이브러리-버전-변경)
    - [2.3. Docker-Compose 멀티 플랫폼 적용](#23-docker-compose-멀티-플랫폼-적용)
  - [3. 시작 전 필수 확인 및 작업](#3-시작-전-필수-확인-및-작업)
    - [STEP 1: `.env` 파일 설정](#step-1-env-파일-설정)
    - [STEP 2: 의존성 라이브러리 다운로드](#step-2-의존성-라이브러리-다운로드)
    - [STEP 3: Airflow 실행](#step-3-airflow-실행)
  - [4. 자주 발생하는 문제 및 해결 방법 (Troubleshooting)](#4-자주-발생하는-문제-및-해결-방법-troubleshooting)
    - [문제 1: Spark 작업에서 S3 접근 시
      `Access Denied` (403 Forbidden) 오류 발생](#문제-1-spark-작업에서-s3-접근-시-access-denied-403-forbidden-오류-발생)
    - [문제 2: `java.lang.ClassNotFoundException` 관련 오류 발생](#문제-2-javalangclassnotfoundexception-관련-오류-발생)
    - [문제 3: Docker 이미지 빌드 또는 컨테이너 실행 시 `exec format error`](#문제-3-docker-이미지-빌드-또는-컨테이너-실행-시-exec-format-error)
  - [5. 기본 설정 및 사용 가이드](#5-기본-설정-및-사용-가이드)
    - [5.1. SparkSubmitOperator 필수 설정](#51-sparksubmitoperator-필수-설정)
    - [5.2. `AIRFLOW_UID` 환경변수의 용도](#52-airflow_uid-환경변수의-용도)
    - [5.3. Airflow 컨테이너 접속](#53-airflow-컨테이너-접속)

## <!-- TOC -->

## 1. 업데이트 개요 (필독)

이번 업데이트의 핵심은 두 가지입니다.

1. **Hadoop 버전 업그레이드**: `3.3.4`에서 `3.3.6`으로 변경되었습니다.
2. **AWS 인증 방식 간소화**: 기존에는 `conf.hadoop/core-site.xml` 파일을 직접 수정하여 AWS 자격 증명을 관리했지만, 이제는 프로젝트 루트의 `.env` 파일에서 모든 것을
   관리합니다.

따라서 기존 방식대로 `core-site.xml`을 수정하면 설정이 적용되지 않거나 덮어씌워질 수 있으니, 반드시 새로운 방식을 숙지해야 합니다.

> **⚠️ 2025-09-26: Airflow 3.x 버전은 추후 재검토가 필요하므로 사용을 권장하지 않습니다.**

---

## 2. 주요 변경사항 및 주의사항

### 2.1. AWS 인증 방식 변경: `.env` 파일 중앙 관리

가장 중요한 변경점입니다. S3 접근을 위한 AWS Key는 이제 `.env` 파일을 통해 주입됩니다.

> **기존 방식 (Deprecated)**:
>
> ```xml
> > <property>
>     <name>fs.s3a.access.key</name>
>     <value>수동으로 키 입력</value>
> </property>
> ```
>
> **⚠️ 위 방식은 더 이상 사용하지 않습니다.**

> **새로운 방식 (Current)**:
>
> 1. 프로젝트 루트의 `.env` 파일에 AWS 자격 증명을 추가합니다.
>
>    ```bash
>    # .env
>    AWS_ACCESS_KEY_ID=액세스_키_ID
>    AWS_SECRET_ACCESS_KEY=시크릿_액세스_키
>    ```
>
> 2. `docker-compose up` 실행 시, `airflow-init` 서비스가 `setup.sh` 스크립트를 통해 이 값을 컨테이너 내부의 `core-site.xml`에 자동으로 주입합니다.
>
> **❗️주의사항**: S3 접근 권한에 문제가 있다면, `core-site.xml`이 아닌 `.env` 파일의 값을 가장 먼저 확인해야 합니다.

### 2.2. Hadoop 및 의존성 라이브러리 버전 변경

`.env` 파일의 `HADOOP_VERSION`이 `3.3.6`으로 변경됨에 따라, S3 연동에 필요한 `hadoop-aws`, `aws-java-sdk-bundle` 등의 의존성 버전도 함께 변경되었습니다.

`download/download.sh` 스크립트는 `.env` 파일의 `HADOOP_VERSION`을 읽어 그에 맞는 버전의 라이브러리를 자동으로 다운로드합니다.

**❗️주의사항**: Hadoop 버전을 직접 변경할 경우, 반드시 기존 `download` 디렉터리의 JAR 파일들을 삭제하고 `download.sh` 스크립트를 다시 실행하여 버전에 맞는 라이브러리를 새로 받아야
합니다. 그렇지 않으면 `ClassNotFoundException`이 발생할 수 있습니다.

### 2.3. Docker-Compose 멀티 플랫폼 적용

Apple Silicon과 같은 ARM 기반 환경을 지원하기 위해 `airflow-compose.yml` 파일의 플랫폼 영역에 `linux/arm64/v8` 옵션을 추가했습니다.

**❗️주의사항**: Intel/AMD 등 x86-64 환경에서 이미지 빌드 시, 다중 플랫폼 설정으로 인해 빌드가 되지 않는 이슈가 발생할 수 있습니다.
이 경우, `airflow-compose.yml` 파일 내의 `platforms` 설정을 해당하는 환경의 값으로 설정 후 빌드해야 합니다.

```yaml
# airflow-compose.yml
...
services:
  airflow-webserver:
    build:
      ...
      platforms:
        - linux/amd64
        - linux/arm64/v8
...
# scheduler, worker 등 다른 airflow 서비스에도 동일하게 적용
```

---

## 3. 시작 전 필수 확인 및 작업

### STEP 1: `.env` 파일 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 환경에 맞게 수정합니다.

```bash
# .env

# Spark 및 Hadoop 버전 (가급적 수정하지 않는 것을 권장)
SPARK_VERSION=3.5.6
HADOOP_VERSION=3.3.6

# [필수] S3 접근을 위한 AWS 자격 증명 입력
AWS_ACCESS_KEY_ID=AKIATV...
AWS_SECRET_ACCESS_KEY=vAc4Ig...

# [필수] 현재 작업 환경(Host)의 사용자 UID 입력 (터미널에서 `id -u` 명령어로 확인)
# 컨테이너 내부 파일 권한 문제를 방지하기 위해 중요합니다.
AIRFLOW_UID=1001
```

### STEP 2: 의존성 라이브러리 다운로드

새로운 Hadoop 버전에 맞는 JAR 파일들을 다운로드합니다.

```bash
# 기존 다운로드 파일이 있다면 깨끗하게 삭제
rm -rf ./download/*.jar ./download/*.tgz

# 다운로드 스크립트 실행
bash ./download/download.sh
```

### STEP 3: Airflow 실행

필요한 디렉터리를 생성하고 Docker Compose를 실행합니다.

```bash
mkdir -p ./dags ./logs ./plugins ./config
docker-compose -f airflow-compose.yml up -d --build
```

> **팁**: 설정 변경 후에는 `--build` 옵션을 추가하여 이미지를 새로 빌드하는 것이 안전합니다.

---

## 4. 자주 발생하는 문제 및 해결 방법 (Troubleshooting)

### 문제 1: Spark 작업에서 S3 접근 시 `Access Denied` (403 Forbidden) 오류 발생

가장 흔한 문제입니다. 원인은 대부분 AWS 자격 증명이 Spark에 제대로 전달되지 않았기 때문입니다.

- **체크리스트 1: `.env` 파일 확인**
  - `AWS_ACCESS_KEY_ID`와 `AWS_SECRET_ACCESS_KEY` 값이 정확한지, 오타는 없는지 확인합니다.
  - 키 값에 특수문자가 포함된 경우 따옴표로 감싸는 것을 고려해볼 수 있습니다. (`KEY="값"`)

- **체크리스트 2: `airflow-init` 컨테이너 로그 확인**
  - `docker logs airflow-init` 명령어로 로그를 확인했을 때, `setup.sh` 스크립트가 오류 없이 실행되었는지 확인합니다. 만약 스크립트 실행 관련 오류가 보인다면 설정 파일이나 권한
    문제를 의심해야 합니다.

### 문제 2-a: `java.lang.ClassNotFoundException` 관련 오류 발생

Spark 작업 로그에 `ClassNotFoundException`이 보인다면, Hadoop 버전과 의존성 JAR 파일 버전이 일치하지 않을 확률이 매우 높습니다.

- **원인**: `.env`의 `HADOOP_VERSION`만 변경하고, 그에 맞는 `hadoop-aws.jar`, `aws-java-sdk-bundle.jar`, `hadoop-common.jar` 등을 새로
  다운로드하지 않았기 때문입니다.
- **해결책**: 위 **[STEP 2: 의존성 라이브러리 다운로드](#step-2-의존성-라이브러리-다운로드)** 과정을 다시 정확히 수행하여 현재 버전에 맞는 JAR 파일들로 교체합니다.

### 문제 2-b:

`Caused by: java.lang.ClassNotFoundException: org.apache.hadoop.fs.impl.prefetch.PrefetchingStatistics` 관련 오류 발생

Spark 작업 로그에 `org.apache.hadoop.fs.impl.prefetch.PrefetchingStatistics`이 보인다면, Airflow에서 사용하는 Hadoop의 버전과 Spark-submit
작업을 받아 수행하는 스파크 클러스터의 Hadoop 버전이 서로 다를 가능성이 있습니다.

- **원인**: Airflow에서 사용하는 Hadoop의 버전과 Spark Cluster의 Hadoop 버전과 다를 가능성이 있다.
- **해결책**: Spark Cluster의 Hadoop 버전과 동일한 `hadoop-common-$VERSION.jar` 파일을 다운로드 받은 후 `/opt/spark/jars/*` 에 옮기고 테스트합니다.

### 문제 3: Docker 이미지 빌드 또는 컨테이너 실행 시 `exec format error`

사용자 환경의 CPU 아키텍처(예: `amd64`)와 Docker 이미지의 타겟 아키텍처(예: `arm64`)가 맞지 않아 발생하는 문제입니다.

- **해결책**: **[2.3. Docker-Compose 플랫폼 기본값 변경](#23-docker-compose-플랫폼-기본값-변경)** 항목을 참고하여 `airflow-compose.yml` 파일의
  `platforms` 설정을 자신의 환경에 맞게 수정하고, 이미지를 다시 빌드하세요.

---

## 5. 기본 설정 및 사용 가이드

### 5.1. SparkSubmitOperator 필수 설정

Airflow UI의 `Admin > Connections`에서 아래 내용으로 `spark_default` 커넥션을 생성해야 합니다.

| 항목                | 값              |
| :------------------ | :-------------- |
| **Connection ID**   | `spark_default` |
| **Connection Type** | `Spark`         |
| **Host**            | `yarn`          |
| **Deploy mode**     | `cluster`       |

DAG 코드에서는 다음과 같이 `conn_id`와 `spark_binary` 경로를 명시해야 합니다.
그리고 실행할 파일을 `application`에 명시하고, 추가적으로 필요한 모듈은 `py_files`에 추가합니다.
`py_files`는 콤마(,)로 구분하여 여러 개의 zip 파일을 추가할 수 있습니다.

```bash
cd /opt/airflow/src
zip -r utils.zip utils
```

```python
submit_job = SparkSubmitOperator(
    conn_id="spark_default",
    task_id="spark-submit",
    # [Errno 13] Permission denied 오류 방지를 위해 전체 경로 명시
    spark_binary="/opt/spark/bin/spark-submit",
    application="/opt/airflow/src/your_spark_job.py",
    py_files="/opt/airflow/src/utils.zip",
    ...
)
```

### 5.2. `AIRFLOW_UID` 환경변수의 용도

`.env` 파일에 설정하는 `AIRFLOW_UID`는 호스트(로컬 PC)의 사용자 UID와 컨테이너 내부의 `airflow` 사용자 UID를 일치시켜주는 역할을 합니다. 이는 `dags`, `logs`,
`plugins` 폴더를 호스트와 마운트할 때 발생할 수 있는 파일 권한 문제를 예방하기 위한 중요한 설정입니다.

### 5.3. Airflow 컨테이너 접속

디버깅 등을 위해 Airflow 컨테이너에 직접 접속해야 할 경우 아래 명령어를 사용합니다.

```bash
# airflow 사용자로 워커 컨테이너에 접속
docker exec -it -u airflow airflow-worker bash

# root 사용자로 스케줄러 컨테이너에 접속
docker exec -it -u root airflow-scheduler bash
```
