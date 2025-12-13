# DataHub

이 프로젝트는 Docker Compose를 사용하여 DataHub(데이터 카탈로그 플랫폼)를 온프레미스 또는 클라우드 VM 환경에 배포하기 위한 구성을 담고 있습니다.

## 사전 요구 사항 (Prerequisites)

---

이 구성을 실행하기 위해 서버는 다음 최소 사양을 충족해야 합니다.

- CPU: 4 vCPU 이상
- RAM: 16GB 이상 (Elasticsearch/OpenSearch와 GMS가 메모리를 많이 사용함)
- Disk: 50GB 이상의 여유 공간

### 설치 및 실행 (Installation & Setup)

보안을 위해 비밀번호와 시크릿 키는 `.env` 파일에서 관리합니다.

| 변수명                       | 설명                                               |
| ---------------------------- | -------------------------------------------------- |
| DATAHUB_VERSION              | 배포할 DataHub 이미지 태그 (예: v0.13.0)           |
| MYSQL_ROOT_PASSWORD          | MySQL 루트 비밀번호                                |
| MYSQL_PASSWORD               | DataHub가 사용할 DB 비밀번호                       |
| DATAHUB_SECRET               | 세션 토큰 암호화 키 (무작위의 긴 문자열 입력 권장) |
| DATAHUB_SYSTEM_CLIENT_SECRET | 내부 서비스 간 통신용 비밀키                       |

```bash
docker-compose up -d
```

### 접속 및 사용

- DataHub Frontend: http://localhost:9002 (또는 서버 IP:9002)
- 기본 관리자 계정: datahub / datahub

### 백업 (Backup)

모든 중요한 데이터는 호스트의 ./data/ 디렉토리에 저장됩니다.

- MySQL: ./data/mysql (주기적으로 mysqldump 권장)
  ```bash
  docker compose exec mysql /usr/bin/mysqldump -u datahub --password=${MYSQL_PASSWORD} datahub > backup_$(date +%F).sql
  ```
- OpenSearch: ./data/opensearch (스냅샷 권장)

## 트러블슈팅 (Troubleshooting)

---
