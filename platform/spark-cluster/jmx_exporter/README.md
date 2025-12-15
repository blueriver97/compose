# HDFS Prometheus JMX Exporter Configuration

이 문서는 Hadoop HDFS(NameNode, DataNode)의 핵심 지표를 Prometheus로 수집하기 위한 JMX Exporter 설정과 수집되는 주요 메트릭의 의미를 기술합니다.

## 1. 개요 (Overview)

Hadoop JMX는 수천 개의 메트릭을 노출하지만, 모든 데이터를 수집할 경우 Prometheus의 부하(High Cardinality)를 유발합니다.
이 설정 파일은 "운영에 필수적인 핵심 지표(Signal)"는 화이트리스트로 수집하고, "데이터 양이 과도한 상세 로그(Noise)"는 블랙리스트로 차단하여 모니터링 효율성을 극대화하도록
설계되었습니다.

적용 대상: NameNode, DataNode
주요 기능:
HDFS 핵심 상태 (Block, Capacity, Volume Failure) 수집
RPC 성능 분석 (Queue Time, Processing Time)
JVM 건전성 (Heap Memory, GC Time)
Prometheus 포맷으로의 네이밍 정규화 (Snake Case)

## 2. 설정 파일 (hadoop.yaml)

[hadoop.yaml](hadoop.yaml) 파일은 NameNode와 DataNode에 공통으로 적용할 수 있는 유니버셜 설정입니다.

## 3. 주요 메트릭 설명 및 운영 가이드

수집된 메트릭 중 운영상 반드시 모니터링해야 할 핵심 지표입니다.

### 3.1. NameNode RPC 성능 (The Brain's Speed)

NameNode가 클라이언트(Spark, Airflow 등)의 요청을 얼마나 빠르게 처리하는지 나타냅니다.

| 메트릭 이름 (Metric Name)                 | 설명 (Description)                                            | 운영 의미 및 임계치 가이드                                                                                                                        |
| :---------------------------------------- | :------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------ |
| `hadoop_rpc_rpc_queue_time_avg_time`      | RPC 대기 시간 (평균)<br>요청이 처리되기 전 큐에서 대기한 시간 | [Critical] 가장 중요한 성능 지표.<br>• 정상: < 100ms<br>• 경고: > 1s (클러스터 과부하 시작)<br>• 위험: > 3s (Spark Job 타임아웃 발생 가능성 높음) |
| `hadoop_rpc_rpc_processing_time_avg_time` | RPC 처리 시간 (평균)<br>실제 로직을 수행하는 데 걸린 시간     | • 의미: 이 수치가 높다면 NameNode 내부 연산이 무겁거나(예: 전체 파일 리스트 조회), GC로 인한 멈춤 현상일 수 있음.                                 |
| `hadoop_rpc_num_open_connections`         | 활성 연결 수<br>현재 맺어진 소켓 연결 개수                    | • 의미: 급격히 증가하면 클라이언트(Spark Executors)가 과도하게 생성되었거나, 연결 누수(Leak)를 의심해야 함.                                       |

### 3.2. DataNode 및 디스크 상태 (Storage Health)

데이터의 물리적 저장소 상태를 나타냅니다.

| 메트릭 이름 (Metric Name)                      | 설명 (Description)                                          | 운영 의미 및 임계치 가이드                                                                         |
| :--------------------------------------------- | :---------------------------------------------------------- | :------------------------------------------------------------------------------------------------- |
| `hadoop_fs_dataset_state_volume_failures`      | 디스크 장애 개수<br>I/O 에러로 인해 오프라인 된 볼륨 수     | [Critical]<br>• 정상: 0<br>• 위험: 1 이상 (즉시 디스크 교체 또는 노드 점검 필요)                   |
| `hadoop_fs_namesystem_missing_blocks`          | 유실된 블록 수<br>복제본이 하나도 남지 않은 블록 수         | [Fatal]<br>• 의미: 데이터 영구 손실 발생. 즉각적인 복구 절차 필요.                                 |
| `hadoop_fs_namesystem_under_replicated_blocks` | 복제본 부족 블록 수<br>지정된 복제 수(기본 3)보다 적은 블록 | • 의미: DataNode가 다운되었거나 복제 속도가 느림. 일시적으로 증가할 수 있으나 장기간 지속 시 위험. |
| `hadoop_fs_namesystem_capacity_remaining`      | 남은 디스크 용량                                            | • 의미: 전체 용량이 10% 미만으로 떨어지면 HDFS는 쓰기 모드를 제한할 수 있음.                       |

### 3.3. JVM 및 프로세스 상태 (Process Health)

Hadoop 데몬(Java Process) 자체의 건전성을 나타냅니다.

| 메트릭 이름 (Metric Name)    | 설명 (Description)                             | 운영 의미 및 임계치 가이드                                                                                            |
| :--------------------------- | :--------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `hadoop_jvm_gc_time_millis`  | GC 누적 시간<br>가비지 컬렉션에 소요된 총 시간 | • 활용: `rate()` 함수로 미분하여 초당 GC 시간을 모니터링.<br>• 급증 시 Stop-the-world로 인한 전체 서비스 프리징 발생. |
| `hadoop_jvm_mem_heap_used_m` | 힙 메모리 사용량 (MB)                          | • 활용: Max Heap 대비 90% 이상 지속 시 OOM(Out Of Memory) 발생 위험.                                                  |
| `hadoop_jvm_threads_blocked` | 블록된 스레드 수                               | • 의미: 락(Lock) 경합 등으로 인해 멈춰있는 스레드 수. 높을수록 병목 현상 심각.                                        |

---

## 4. Alerting Rules (권장 알람 설정)

Prometheus AlertManager 설정 시 권장하는 규칙입니다.

1. NameNode Slow Response
   조건: `rate(hadoop_rpc_rpc_queue_time_avg_time[5m]) > 1000` (1초 이상)
   조치: 과도한 Spark Job 중단 또는 NameNode 리소스 증설 검토

2. DataNode Volume Failure
   조건: `hadoop_fs_dataset_state_volume_failures > 0`
   조치: 해당 DataNode 장비의 디스크 교체 작업 지시

3. HDFS Capacity Warning
   조건: `(hadoop_fs_namesystem_capacity_used / hadoop_fs_namesystem_capacity_total)  100 > 85`
   조치: 불필요한 데이터 삭제 또는 노드 증설 계획 수립
