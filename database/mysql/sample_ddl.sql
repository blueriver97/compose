CREATE TABLE IF NOT EXISTS tb_lower
(
    id               INT AUTO_INCREMENT COMMENT '기본키',
    char36           CHAR(36)       NULL COMMENT 'char',
    varchar36        VARCHAR(36)    NULL COMMENT 'varchar',
    integer1         INT            NULL COMMENT 'int',
    integer2         BIGINT         NULL COMMENT 'bigint',
    unsigned_int     INT UNSIGNED   NULL COMMENT 'unsigned int',
    float1           FLOAT          NULL COMMENT 'float',
    double1          DOUBLE         NULL COMMENT 'double',
    decimal1         DECIMAL(12, 8) NULL COMMENT 'decimal',
    boolean1         BOOLEAN        NULL COMMENT 'boolean',
    blob1            BLOB           NULL COMMENT 'blob',
    text1            TEXT           NULL COMMENT 'text',
    date1            DATE           NULL COMMENT 'date',
    time1            TIME           NULL COMMENT 'time',
    datetime1        DATETIME       NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'datetime',
    create_datetime  DATETIME(6)    NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시_datetime',
    update_timestamp TIMESTAMP(6)   NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시_timestamp',
    CONSTRAINT PK PRIMARY KEY (id)
) COMMENT '단일키 테이블';

CREATE TABLE IF NOT EXISTS TB_UPPER
(
    ID               INT AUTO_INCREMENT COMMENT '기본키1',
    CHAR36           CHAR(36)       NOT NULL COMMENT '기본키2',
    VARCHAR36        VARCHAR(36)    NULL COMMENT 'VARCHAR',
    INTEGER1         INT            NULL COMMENT 'INT',
    INTEGER2         BIGINT         NULL COMMENT 'BIGINT',
    UNSIGNED_INT     INT UNSIGNED   NULL COMMENT 'UNSIGNED INT',
    FLOAT1           FLOAT          NULL COMMENT 'FLOAT',
    DOUBLE1          DOUBLE         NULL COMMENT 'DOUBLE',
    DECIMAL1         DECIMAL(12, 8) NULL COMMENT 'DECIMAL',
    BOOLEAN1         BOOLEAN        NULL COMMENT 'BOOLEAN',
    BLOB1            BLOB           NULL COMMENT 'BLOB',
    TEXT1            TEXT           NULL COMMENT 'TEXT',
    DATE1            DATE           NULL COMMENT 'DATE',
    TIME1            TIME           NULL COMMENT 'TIME',
    DATETIME1        DATETIME       NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'DATETIME',
    CREATE_DATETIME  DATETIME(6)    NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시_DATETIME',
    UPDATE_TIMESTAMP TIMESTAMP(6)   NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시_TIMESTAMP',
    CONSTRAINT CPK PRIMARY KEY (ID, CHAR36)
) COMMENT '복합키 테이블';

CREATE TABLE IF NOT EXISTS TB_COMPOSITE_KEY
(
    id               INT AUTO_INCREMENT COMMENT '기본키1',
    char36           CHAR(36)       NOT NULL COMMENT '기본키4',
    varchar36        VARCHAR(36)    NULL COMMENT 'VARCHAR',
    integer1         INT            NOT NULL COMMENT '기본키3',
    integer2         BIGINT         NULL COMMENT 'BIGINT',
    unsigned_int     INT UNSIGNED   NULL COMMENT 'UNSIGNED INT',
    float1           FLOAT          NULL COMMENT 'FLOAT',
    double1          DOUBLE         NULL COMMENT 'DOUBLE',
    decimal1         DECIMAL(12, 8) NULL COMMENT 'DECIMAL',
    boolean1         BOOLEAN        NULL COMMENT 'BOOLEAN',
    BLOB1            BLOB           NULL COMMENT 'BLOB',
    TEXT1            TEXT           NULL COMMENT 'TEXT',
    DATE1            DATE           NOT NULL COMMENT '기본키2',
    TIME1            TIME           NULL COMMENT 'TIME',
    DATETIME1        DATETIME       NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'DATETIME',
    CREATE_DATETIME  DATETIME(6)    NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시_DATETIME',
    UPDATE_TIMESTAMP TIMESTAMP(6)   NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시_TIMESTAMP',
    CONSTRAINT CPK PRIMARY KEY (id, DATE1, integer1, char36)
) COMMENT '복합키2 테이블';
