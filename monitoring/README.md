# Monitoring Layer

이 디렉토리는 서비스 상태, 인프라 리소스, 그리고 빅데이터 애플리케이션(Spark, YARN)의 관측 가능성(Observability)을 확보하기 위한 모니터링 스택을 정의합니다.

Prometheus 기반의 메트릭 수집 파이프라인을 구축하며, 대용량 처리를 위한 VictoriaMetrics와 시각화를 위한 Grafana를 통합하여 제공합니다.

## 1. 아키텍처 (Architecture)

데이터의 흐름은 메트릭 노출(Exporter) -> 수집/저장(Prometheus/VictoriaMetrics) -> 시각화(Grafana)로 구성됩니다.

- Collection: 각 서비스(YARN, Spark 등)의 메트릭을 Exporter가 수집하여 Prometheus가 읽을 수 있는 포맷으로 노출합니다.
- Storage: Prometheus가 주기적으로 데이터를 수집(Scrape)하며, 장기 보관 및 고성능 쿼리를 위해 VictoriaMetrics를 원격 저장소로 활용합니다.
- Visualization: Grafana를 통해 수집된 데이터를 대시보드 형태로 시각화합니다.

## 2. 구성 요소 (Components)

### Prometheus & VictoriaMetrics

메트릭 수집 및 저장을 담당하는 핵심 계층입니다.

- Prometheus: `prometheus.yml`에 정의된 타겟(Node, YARN, Spark 등)으로부터 주기적으로 메트릭을 수집(Pull)합니다.
- VictoriaMetrics: Prometheus와 호환되는 고성능 시계열 데이터베이스(TSDB)입니다. 기본 3개월(`VM_RETENTION_PERIOD: 3`)의 데이터 보관 주기가 설정되어 있습니다.

### Exporters

애플리케이션 특화 메트릭을 수집하는 컨테이너입니다.

- Yarn Exporter: Python 기반의 자체 제작 Exporter입니다. Hadoop YARN 리소스 매니저 API를 호출하여 클러스터 상태(메모리, 코어, 앱 상태 등)를 수집합니다.
- Graphite Exporter: Spark와 같이 Graphite 프로토콜을 사용하는 애플리케이션의 메트릭을 변환하여 Prometheus에 연동합니다. `graphite_mapping.conf`를 통해
  Spark 메트릭을 정제합니다.

### Grafana

수집된 데이터를 시각화하는 플랫폼입니다. `prometheus` 및 `victoriametrics`를 데이터 소스로 연결하여 사용합니다.

## 3. 서비스 포트 (Service Ports)

각 컴포넌트는 호스트의 다음 포트를 통해 접근할 수 있습니다.

| 서비스 (Service)  | 포트 (Port) | 설명 (Description)                         |
| :---------------- | :---------- | :----------------------------------------- |
| Grafana           | 3000        | 웹 대시보드 UI                             |
| Prometheus        | 9090        | 메트릭 수집 서버 및 웹 UI                  |
| VictoriaMetrics   | 8428        | 시계열 데이터 저장소 (PromQL 호환 API)     |
| Graphite Exporter | 9108        | Prometheus Scrape 포트 (수집용)            |
| Graphite Exporter | 9109        | Graphite Protocol 수신 포트 (Spark 연동용) |
| Yarn Exporter     | 9459        | YARN 메트릭 노출 포트                      |

## 4. 실행 방법 (Usage)

각 구성 요소는 독립적인 `compose.yml`을 가지고 있어 개별 실행이 가능합니다.

### 전체 스택 실행

```bash
# 1. 메트릭 수집 및 저장소 실행
cd prometheus
docker compose up -d

cd ../victoriametrics
docker compose up -d

# 2. Exporter 실행 (필요 시)
cd ../exporter
docker compose up -d

# 3. 대시보드 실행
cd ../grafana
docker compose up -d
```
