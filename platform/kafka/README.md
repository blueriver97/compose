# Kafka 플랫폼 운영 및 배포 가이드

## 1. 개요 (Overview)

본 디렉토리는 KRaft(Kafka Raft) 모드를 기반으로 하는 차세대 Kafka 에코시스템의
로컬 및 스테이징 배포 설정을 관리합니다.

ZooKeeper 의존성을 제거하고 컨트롤러와 브로커 역할을 분리하여
확장성과 관리 편의성을 극대화한 아키텍처를 채택하고 있습니다.

## 2. 시스템 아키텍처

- Controller & Broker (KRaft)
  - 별도의 Controller 노드(ID: 1)
  - Broker 노드(ID: 100)
  - KRaft quorum 구성

- Security
  - 내부 통신: SSL (mTLS)
  - 외부 클라이언트: SASL_SSL (SCRAM-SHA-256)

- Kafka Connect (Isolated)
  - Source 전용: src-connect
  - Sink 전용: sink-connect
  - 워크로드 및 플러그인 충돌 방지를 위해 물리적 분리 운영

- Schema Registry
  - Avro, JSON Schema 중앙 관리
  - Kafka 브로커와 SSL 통신

## 3. 사전 준비 사항 (Pre-requisites)

### 3.1 환경 변수 설정

.env 파일에 정의된 버전을 확인하십시오.

- Kafka / Confluent: 8.0.3
  - Confluent Platform 8.0.x == Apache Kafka 4.0
  - Confluent Platform 8.1.x == Apache Kafka 4.1

- Debezium: 3.4.0
- Groovy: 4.0.28

### 3.2 인증서 생성 (SSL / TLS)

브로커 간 통신 및 클라이언트 암호화를 위한
JKS(Java Keystore) 인증서를 생성해야 합니다.

실행 방법:

cd secrets/
./generate-kafka-certs.sh

생성 결과물:

- truststore.jks
- controller.keystore.jks
- broker.keystore.jks
- client.keystore.jks

보안 주의사항:

- 모든 keystore 비밀번호는 기본값 `changeit`
- 프로덕션 배포 시 반드시 변경 필요

## 4. 실행 가이드

### 4.1 서비스 기동

docker compose up -d

### 4.2 SASL 유저 생성 (SCRAM)

브로커 기동 후, 클라이언트 및 Schema Registry에서
사용할 계정을 생성해야 합니다.

- 자동화 서비스: init-scram
- 대상 유저:
  - broker
  - schemaregistry
  - client

설정 내용:

- SSL 관리자 권한으로 브로커 접속
- SCRAM-SHA-256 자격 증명 생성 및 저장

## 5. 컴포넌트별 세부 설정

### 5.1 Kafka Connect 레이어

커넥터는 플러그인 경로를 분리하여 마운트합니다.

- Source Plugins
  - 경로: ./connect-plugins/source
  - Debezium (MySQL, SQL Server)
  - Groovy 라이브러리

- Sink Plugins
  - 경로: ./connect-plugins/sink
  - S3 커넥터
  - Iceberg 커넥터

### 5.2 모니터링 및 UI

- Kafbat UI
  - 접속 주소: http://localhost:8080
  - SSL 환경에서 브로커 및 두 개의 Connect 클러스터 통합 모니터링

- JMX Exporter
  - 포트: 7071
  - Prometheus 포맷 메트릭 노출
  - 필요 시 KAFKA_OPTS 주석 해제하여 활성화

## 6. 운영 및 장애 대응 (SRE)

### 6.1 리스너 구성 주의사항

보안 강화를 위해 용도별 리스너를 엄격히 분리합니다.

- CONTROLLER
  - 컨트롤러 간 통신
  - SSL 사용

- BROKER
  - 브로커 간 통신
  - 동일 Docker 네트워크 내 서드파티 접근
  - SSL 사용

- HOST
  - 외부 클라이언트 / 애플리케이션 접속
  - SASL_SSL 사용

# Appendix

## 프로토콜 비교

| 프로토콜       | 인증 (Who are you?)  | 암호화 (Private?) | 권장 사용 환경                         |
| -------------- | -------------------- | ----------------- | -------------------------------------- |
| PLAINTEXT      | 없음 (보안 없음)     | 없음 (평문 전송)  | 로컬 개발, 신뢰된 내부 Docker 네트워크 |
| SSL (TLS)      | 인증서 기반 (선택적) | 있음 (TLS)        | 보안이 필요한 전송 계층 암호화         |
| SASL_PLAINTEXT | 있음 (ID / PW 등)    | 없음 (평문 전송)  | 폐쇄적 내부망, 성능 우선 환경          |
| SASL_SSL       | 있음 (ID / PW 등)    | 있음 (TLS)        | 운영 환경 표준 (공용망, 클라우드)      |

## TLS / SSL의 대전제

"서버는 무조건 신분증이 있어야 한다"

TLS 통신에서 접속을 받는 쪽(서버)은
자신이 누구인지 증명할 의무가 있습니다.

- 서버의 의무
  - "나는 진짜 카프카 브로커다"라는 것을 증명
  - 인증서(Certificate) 제시
  - 인증서 + 개인키가 저장된 보관함 = keystore

- 클라이언트의 선택
  - 서버가 제시한 인증서를 검증
  - 신뢰 여부 판단
  - 이때 사용하는 것이 truststore

## ssl.client.auth = none 의 진짜 의미

이 설정은
"서버가 클라이언트에게 신분증을 요구할 것인가?"
에 대한 설정입니다.

- none
  - 서버가 클라이언트의 keystore 인증서를 확인하지 않음

- required
  - 서버가 클라이언트의 keystore 인증서를 확인함
  - 클라이언트는 keystore + truststore 모두 필요
