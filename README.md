# Docker Compose Collection

이 저장소는 데이터 엔지니어링 및 DevOps 환경 구축을 위한 다양한 Docker Compose 스택과 유틸리티를 모아둔 모노레포입니다.
Base OS 이미지부터 데이터베이스, 모니터링, 플랫폼 서비스까지 모듈화하여 관리합니다.

---

## 1. 디렉토리 구조 (Directory Map)

| 분류           | 서비스 / 모듈  | 경로                          | 설명                                               |
| :------------- | :------------- | :---------------------------- | :------------------------------------------------- |
| **Base**       | OS Images      | [`base/`](./base)             | Ubuntu, Rocky, AmazonLinux 베이스 이미지           |
| **Database**   | RDBMS / NoSQL  | [`database/`](./database)     | MySQL, MSSQL, Redis 및 Data Generator              |
| **Platform**   | Big Data & Ops | [`platform/`](./platform)     | Superset, Iceberg, MinIO, Vault, Nexus, GitSync 등 |
| **Monitoring** | Observability  | [`monitoring/`](./monitoring) | Prometheus, Grafana, VictoriaMetrics, Exporters    |
| **Runtime**    | Language / AI  | [`runtime/`](./runtime)       | Python Runtime, Ollama(LLM)                        |

---

## 2. 필수 요구 사항 (Prerequisites)

- Docker Desktop or Docker Engine (Compose plugin 포함)
- Python 3.11+ (스크립트 실행용)

---

## 3. 시작하기 (Getting Started)

각 디렉토리의 README.md를 참조하여 개별 서비스를 실행할 수 있습니다.
