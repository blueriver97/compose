-- sample_ddl.sql
CREATE DATABASE store;
GO

SELECT name FROM sys.databases;
GO

USE store;
GO

CREATE TABLE tb_lower
(
    id               INT IDENTITY(1,1) NOT NULL,
    char36           CHAR(36)       NULL,
    varchar36        VARCHAR(36)    NULL,
    integer1         INT            NULL,
    integer2         BIGINT         NULL,
    unsigned_int     BIGINT         NULL,  -- MSSQL은 unsigned 없음, BIGINT으로 대체
    float1           FLOAT          NULL,
    double1          FLOAT          NULL,  -- DOUBLE → FLOAT in MSSQL
    decimal1         DECIMAL(12, 8) NULL,
    boolean1         BIT            NULL,
    blob1            VARBINARY(MAX) NULL,
    text1            VARCHAR(MAX)   NULL,
    date1            DATE           NULL,
    time1            TIME           NULL,
    datetime1        DATETIME       NULL DEFAULT GETDATE(),
    create_datetime  DATETIME2(6)   NULL DEFAULT SYSUTCDATETIME(),
    update_timestamp DATETIME2(6)   NULL DEFAULT SYSUTCDATETIME(),  -- ON UPDATE는 트리거로 구현 가능
    CONSTRAINT PK_tb_lower PRIMARY KEY (id)
);
GO

CREATE TABLE TB_UPPER
(
    ID               INT IDENTITY(1,1) NOT NULL,
    CHAR36           CHAR(36)       NOT NULL,
    VARCHAR36        VARCHAR(36)    NULL,
    INTEGER1         INT            NULL,
    INTEGER2         BIGINT         NULL,
    UNSIGNED_INT     BIGINT         NULL,
    FLOAT1           FLOAT          NULL,
    DOUBLE1          FLOAT          NULL,
    DECIMAL1         DECIMAL(12, 8) NULL,
    BOOLEAN1         BIT            NULL,
    BLOB1            VARBINARY(MAX) NULL,
    TEXT1            VARCHAR(MAX)   NULL,
    DATE1            DATE           NULL,
    TIME1            TIME           NULL,
    DATETIME1        DATETIME       NULL DEFAULT GETDATE(),
    CREATE_DATETIME  DATETIME2(6)   NULL DEFAULT SYSUTCDATETIME(),
    UPDATE_TIMESTAMP DATETIME2(6)   NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT CPK_TB_UPPER PRIMARY KEY (ID, CHAR36)
);
GO

CREATE TABLE TB_COMPOSITE_KEY
(
    id               INT IDENTITY(1,1) NOT NULL,
    char36           CHAR(36)       NOT NULL,
    varchar36        VARCHAR(36)    NULL,
    integer1         INT            NOT NULL,
    integer2         BIGINT         NULL,
    unsigned_int     BIGINT         NULL,
    float1           FLOAT          NULL,
    double1          FLOAT          NULL,
    decimal1         DECIMAL(12, 8) NULL,
    boolean1         BIT            NULL,
    BLOB1            VARBINARY(MAX) NULL,
    TEXT1            VARCHAR(MAX)   NULL,
    DATE1            DATE           NOT NULL,
    TIME1            TIME           NULL,
    DATETIME1        DATETIME       NULL DEFAULT GETDATE(),
    CREATE_DATETIME  DATETIME2(6)   NULL DEFAULT SYSUTCDATETIME(),
    UPDATE_TIMESTAMP DATETIME2(6)   NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT CPK_TB_COMPOSITE_KEY PRIMARY KEY (id, DATE1, integer1, char36)
);
GO
