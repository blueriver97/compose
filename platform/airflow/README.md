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
