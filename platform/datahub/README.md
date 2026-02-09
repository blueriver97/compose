# DataHub

이 프로젝트는 Docker Compose를 사용하여 DataHub(데이터 카탈로그 플랫폼)를 온프레미스 또는 클라우드 VM 환경에 배포하기 위한 구성을 담고 있습니다.

## 사전 요구 사항 (Prerequisites)

---

이 구성을 실행하기 위해 서버는 다음 최소 사양을 충족해야 합니다.

- CPU: 4 vCPU 이상
- RAM: 16GB 이상 (Elasticsearch/OpenSearch와 GMS가 메모리를 많이 사용함)
- Disk: 50GB 이상의 여유 공간

### 설치 및 실행 (Installation & Setup)

보안을 위해 시크릿 키는 `.env` 파일에서 관리합니다.

| 변수명          | 설명                                               |
| --------------- | -------------------------------------------------- |
| DATAHUB_VERSION | 배포할 DataHub 이미지 태그 (예: v0.13.0)           |
| DATAHUB_SECRET  | 세션 토큰 암호화 키 (무작위의 긴 문자열 입력 권장) |

```bash
docker-compose up -d
```

### 접속 및 사용

- DataHub Frontend: http://localhost:9002 (또는 서버 IP:9002)
- 기본 관리자 계정: datahub / datahub

## 트러블슈팅 (Troubleshooting)

### 1. Ingestion 구성 관련 이슈

- Ingestion 구성 시 'Advanced' 속성에서 `CLI Version`, `Extra Enviroment Variables` 추가 설정 필요.
- datahub-actions 컨테이너에 직접 선언해도, 실제 수집 파이프라인이 참조하지 못하는 것으로 파악함.
- 또한 venv 구성 후 자동으로 requirements.txt를 설치해서 환경을 구성해야 하는데, 이 부분이 계속 실패하면 수동 설치 후 재시작
  이 부분은 수동 설치로 인해 남아있는 캐시를 사용해 설치되는 것으로 추측함.

```json
// CLI Version
1.3.1.5

// Extra Enviroment Variables
{"UV_INDEX_URL":"https://nexus.example.com/repository/pypi-remote/simple"}
```

### 2. `sink`, `datahub_api` 사용 시, PAT 토큰 필요

- 수집 결과를 반영하기 위한 `sink` 및 기존 수집된 엔티티의 메타정보를 확인하는 용도로 사용되는 `datahub_api` 설정 시, PAT 토큰 값 필요.

---
