# SQL 실행 명령

## MySQL

---

### 1. 원격 쿼리 실행

```bash
docker exec -i mysql mysql -uadmin -padmin store < mysql/sample_ddl.sql
```

## SQL Server

---

### 1. 원격 쿼리 실행

```bash
cat sqlserver/sample_ddl.sql | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'foqaktmxj01!' -C -N
```

### 2. CDC 활성화

```bash
cat sqlserver/enable_cdc.sql | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'foqaktmxj01!' -C -N
```

## Redis

---

Config: redis/redis.conf (기본 비밀번호: admin)

```bash
cd redis
docker-compose up -d
```

## Data Generator

---

MySQL 및 MSSQL 테스트 데이터 생성을 위한 Python 스크립트입니다.

### 1. 사전 준비 (Setup)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 설정 (Configuration)

settings.yaml 파일을 수정하여 타겟 DB 접속 정보와 트랜잭션 비율(Insert/Update/Delete)을 조정하십시오.

### 3. 실행 (Run)

```bash
# 동기 방식 (기본)
python datagen.py

# 비동기 방식 (고성능)
python datagen_aio.py
```
