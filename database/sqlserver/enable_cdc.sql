-- 1. CLR 설정 활성화
EXEC sp_configure 'clr enabled', 1;
RECONFIGURE;

-- 2. Agent 상태 확인 (결과 확인용, 필요시 생략 가능)
SELECT status_desc
FROM sys.dm_server_services
WHERE servicename LIKE '%Agent%';

-- 3. 스키마 CDC 활성화
USE store;
EXEC sys.sp_cdc_enable_db;

-- -- 스키마 CDC 비활성화 (필요 시 주석 해제하고 실행)
-- USE store;
-- EXEC sys.sp_cdc_disable_db;

-- 스키마 CDC 활성 여부 확인
SELECT name, is_cdc_enabled
FROM sys.databases
WHERE name = 'store';

-- 4. 테이블 CDC 활성화
EXEC sys.sp_cdc_enable_table
     @source_schema = N'dbo',
     @source_name = N'tb_lower',
     @role_name = NULL;

EXEC sys.sp_cdc_enable_table
     @source_schema = N'dbo',
     @source_name = N'TB_UPPER',
     @role_name = NULL;

EXEC sys.sp_cdc_enable_table
     @source_schema = N'dbo',
     @source_name = N'TB_COMPOSITE_KEY',
     @role_name = NULL;

-- -- 테이블 CDC 비활성화 (필요 시 주석 해제 후 실행)
-- EXEC sys.sp_cdc_disable_table
--     @source_schema = N'dbo',
--     @source_name   = N'tb_lower',
--     @capture_instance = N'dbo_tb_lower';

-- 테이블 CDC 활성 여부 확인
SELECT *
FROM cdc.change_tables;

-- 5. CDC Job 활성 여부 확인
SELECT *
FROM msdb.dbo.sysjobs;

-- 6. Agent가 없는 환경에서 트랜잭션을 _CT에 반영하는 임시 방법 (필요 시만 실행)
-- EXEC sys.sp_MScdc_capture_job;
