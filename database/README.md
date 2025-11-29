# SQL 실행 명령

## MySQL

### 1. 원격 쿼리 실행

```bash
docker exec -i mysql mysql -uadmin -padmin store < mysql/sample_ddl.sql
```

## SQL Server

### 1. 원격 쿼리 실행

```bash
cat sqlserver/sample_ddl.sql | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'foqaktmxj01!' -C -N
```

### 2. CDC 활성화

```bash
cat sqlserver/enable_cdc.sql | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'foqaktmxj01!' -C -N
```
