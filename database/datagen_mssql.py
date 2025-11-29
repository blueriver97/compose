import random
import time
import pyodbc
import numpy as np
from faker import Faker
from tqdm import tqdm

# TODO. MSSQL 연결 정보
DB_HOST = "localhost"
DB_PORT = 1433
DB_USER = "SA"
DB_PASSWORD = "foqaktmxj01!"
DEFAULT_DATABASE = "store"

# TODO. 트랜잭션 설정
TRANSACTIONS_PER_SECOND = 20
TOTAL_DURATION_SECONDS = 1
INSERT_RATIO = 0.60
UPDATE_RATIO = 0.30
DELETE_RATIO = 0.10

# TODO. 테이블 목록
# 공백을 제거해 주는 strip() 로 정리
TABLE_LIST = [t.strip() for t in """store.tb_lower,store.TB_UPPER,store.TB_COMPOSITE_KEY""".split(",")]

# pyodbc 연결 설정
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={DB_HOST},{DB_PORT};"
    f"DATABASE={DEFAULT_DATABASE};"
    f"UID={DB_USER};PWD={DB_PASSWORD};"
    f"Encrypt=no;TrustServerCertificate=yes"
)
db = pyodbc.connect(conn_str)
cursor = db.cursor()

fake = Faker()


def get_table_schema(table):
    schema_name, table_name = table.split(".")
    cursor.execute(
        f"""
        WITH
/*테이블 명세서*/
    TBL_SPEC       AS (SELECT SYS_TBLS.object_id /*테이블 ID*/
                                , SYS_TBLS.create_date /*테이블 생성 시간*/
                                , SYS_TBLS.modify_date /*테이블 최종 수정 시간*/
                                , SYS_COLS.column_id /*컬럼 ID*/
                                , INFO_COL.TABLE_CATALOG /*카탈로그 이름*/
                                , INFO_COL.TABLE_NAME /*테이블 이름*/
                                , INFO_COL.ORDINAL_POSITION /*컬럼의 순서*/
                                , INFO_COL.COLUMN_NAME /*컬럼 이름*/
                                , INFO_COL.CHARACTER_MAXIMUM_LENGTH /*최대 문자 길이*/
                                , INFO_COL.NUMERIC_PRECISION /*숫자의 정밀도*/
                                , INFO_COL.NUMERIC_SCALE /*숫자의 소수 자릿수*/
                                , INFO_COL.COLUMN_DEFAULT /*컬럼의 기본값*/
                                , INFO_COL.DATA_TYPE /*데이터 타입*/
                                , INFO_COL.IS_NULLABLE /*NULL 허용 여부*/
                                , INFO_COL.COLLATION_NAME /*정렬 방식 (문자셋 포함)*/
                           FROM sys.tables AS SYS_TBLS
                                    INNER JOIN sys.columns AS SYS_COLS
                                               ON SYS_TBLS.object_id = SYS_COLS.object_id
                                    INNER JOIN INFORMATION_SCHEMA.COLUMNS AS INFO_COL
                                               ON SYS_TBLS.name = INFO_COL.TABLE_NAME
                                                   AND SYS_COLS.name = INFO_COL.COLUMN_NAME
                           WHERE SYS_TBLS.schema_id = 1)
/*PK 컬럼 목록*/
   , KEY_COLS      AS (SELECT DISTINCT TABLE_NAME /*테이블 이름*/
                                     , COLUMN_NAME /*PK 컬럼 이름*/
                           FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                           WHERE (CONSTRAINT_NAME LIKE 'pk_%')
                              OR (CONSTRAINT_NAME LIKE 'cpk_%')
                              OR (CONSTRAINT_NAME LIKE 'npk_%')
                              OR (CONSTRAINT_NAME LIKE '%_pk')
                              OR (CONSTRAINT_NAME LIKE 'pk%_'))
/* AUTO_INCREMENT (IDENTITY) 컬럼 */
   , IS_IDENTITY   AS (SELECT TABLE_NAME, COLUMN_NAME
                       FROM INFORMATION_SCHEMA.COLUMNS
                       WHERE COLUMNPROPERTY(OBJECT_ID(TABLE_NAME), COLUMN_NAME, 'IsIdentity') = 1)

SELECT TBL_SPEC.COLUMN_NAME                                           AS COLUMN_NAME /*컬럼 이름*/
     , TBL_SPEC.DATA_TYPE                                             AS DATA_TYPE /*데이터 타입*/
     , ISNULL(CAST(TBL_SPEC.CHARACTER_MAXIMUM_LENGTH AS VARCHAR),
              CAST(TBL_SPEC.NUMERIC_PRECISION AS VARCHAR) + ',' +
              CAST(TBL_SPEC.NUMERIC_SCALE AS VARCHAR))                AS COLUMN_LENGTH /*컬럼 길이*/
     , TBL_SPEC.IS_NULLABLE                                           AS IS_NULLABLE /*NULL 허용 여부*/
     , IIF(KEY_COLS.COLUMN_NAME IS NULL, 'NO', 'YES')                 AS PK /*주 키 여부*/
     , TBL_SPEC.COLUMN_DEFAULT                                        AS COLUMN_DEFAULT /*컬럼의 기본값*/
     , IIF(IS_IDENTITY.COLUMN_NAME IS NOT NULL, 'YES', 'NO')          AS IS_AUTO_INCREMENT /*AUTO_INCREMENT 여부*/


-- SELECT COUNT(1)
FROM TBL_SPEC
         LEFT JOIN KEY_COLS
                   ON TBL_SPEC.TABLE_NAME = KEY_COLS.TABLE_NAME
                       AND TBL_SPEC.COLUMN_NAME = KEY_COLS.COLUMN_NAME
         LEFT JOIN IS_IDENTITY
                   ON TBL_SPEC.TABLE_NAME = IS_IDENTITY.TABLE_NAME
                       AND TBL_SPEC.COLUMN_NAME = IS_IDENTITY.COLUMN_NAME
WHERE TBL_SPEC.TABLE_NAME = ?
ORDER BY TBL_SPEC.TABLE_NAME, TBL_SPEC.ORDINAL_POSITION;
        """,
        (table_name,),
    )
    return {row.COLUMN_NAME: row for row in cursor.fetchall()}


# Primary Key 컬럼 찾기 함수
def get_primary_key_columns(columns):
    return [column[0] for column in columns if column[4] == "YES"]


# Auto Increment 키 컬럼 찾기 함수
def get_auto_increment_columns(columns):
    return [column[0] for column in columns if column[6] == "YES"]


def generate_integer_value(type_name, type_length):
    if "bigint" in type_name:
        return fake.random_int(min=0, max=9223372036854775807)
    elif "tinyint" in type_name and type_length == "1":
        return random.choice([0, 1])
    else:
        return fake.random_int(min=0, max=2147483647)


def generate_string_value(type_name, type_length):
    max_length = int(type_length) if type_length else 255
    if max_length < 0:
        max_length = 255
    if "varchar" in type_name or "text" in type_name or "char" in type_name:
        return fake.text(max_nb_chars=max_length)
    else:
        return fake.uuid4()


def generate_date_time_value(type_name):
    if "date" in type_name:
        return fake.date_this_decade()
    elif "time" in type_name:
        return fake.time()
    elif "datetime" in type_name or "timestamp" in type_name:
        return fake.date_time_this_decade()
    else:
        return None


def generate_numeric_value(type_name, type_length):
    if "float" in type_name:
        return fake.pyfloat(left_digits=4, right_digits=2, positive=True)
    elif "double" in type_name:
        return fake.pyfloat(left_digits=6, right_digits=3, positive=True)
    elif "decimal" in type_name:
        precision = int(type_length.split(",")[0]) if type_length else 5
        scale = (
            int(type_length.split(",")[1]) if type_length and "," in type_length else 2
        )
        return fake.pydecimal(
            left_digits=precision - scale, right_digits=scale, positive=True
        )
    else:
        return None


def generate_blob_value(type_name, type_length):
    # 타입 이름을 소문자로 변환하여 대소문자 구분 없이 비교 가능하도록 함
    type_name = type_name.lower()

    # 기본 BLOB 타입의 길이를 지정 (예: 65,536 bytes = 64 KB)
    if type_length is None:
        if "tinyblob" in type_name:
            type_length = 255  # TINYBLOB 최대 크기
        elif "blob" in type_name:
            type_length = 65535  # BLOB 최대 크기
        elif "mediumblob" in type_name:
            type_length = 16777215  # MEDIUMBLOB 최대 크기
        elif "longblob" in type_name:
            type_length = 4294967295  # LONGBLOB 최대 크기
        else:
            type_length = 65535  # 기본 BLOB 길이 (64 KB)
    else:
        if type_length == "-1":
            type_length = 65535
    return fake.binary(length=type_length)


def generate_boolean_value():
    return fake.boolean()


# 데이터 생성 함수
def generate_data(columns_dict, primary_key_columns, auto_increment_columns):
    data = {}
    for column_name, column_info in columns_dict.items():
        type_name = column_info[1].lower()
        type_length = column_info[2]
        column_default = column_info[5]

        if column_default is not None or column_name in auto_increment_columns:
            continue

        if (
                column_name in primary_key_columns
                and column_name not in auto_increment_columns
        ):
            if "int" in type_name:
                data[column_name] = generate_integer_value(type_name, type_length)
            elif ("date" in type_name
                  or "time" in type_name
                  or "datetime" in type_name
                  or "datetime2" in type_name):
                data[column_name] = generate_date_time_value(type_name)
            elif ("float" in type_name
                  or "double" in type_name
                  or "decimal" in type_name):
                data[column_name] = generate_numeric_value(type_name, type_length)
            else:
                data[column_name] = generate_string_value(type_name, type_length)
        else:
            if random.random() < 0.1:
                data[column_name] = None
            else:
                if "int" in type_name:
                    data[column_name] = generate_integer_value(type_name, type_length)
                elif (
                        "varchar" in type_name
                        or "text" in type_name
                        or "char" in type_name
                ):
                    data[column_name] = generate_string_value(type_name, type_length)
                elif (
                        "date" in type_name
                        or "time" in type_name
                        or "datetime" in type_name
                        or "datetime2" in type_name
                ):
                    data[column_name] = generate_date_time_value(type_name)
                elif (
                        "float" in type_name
                        or "double" in type_name
                        or "decimal" in type_name
                ):
                    data[column_name] = generate_numeric_value(type_name, type_length)
                elif "blob" in type_name or "binary" in type_name:
                    data[column_name] = generate_blob_value(type_name, type_length)
                elif "bit" in type_name:
                    data[column_name] = generate_boolean_value()
    return data


# 데이터 삽입 함수
def insert_data(table_name, columns_dict, primary_key_columns, auto_increment_columns):
    data = generate_data(columns_dict, primary_key_columns, auto_increment_columns)
    insert_columns = [col for col in data.keys() if col not in auto_increment_columns]
    insert_values = [data[col] for col in insert_columns]
    schema, table = table_name.split(".")
    sql = f"INSERT INTO {schema}.dbo.{table} ({', '.join(insert_columns)}) VALUES ({', '.join(['?'] * len(insert_columns))})"
    cursor.execute(sql, insert_values)
    db.commit()


# 데이터 갱신 함수
def update_data(table_name, columns_dict, primary_key_columns, auto_increment_columns):
    schema, table = table_name.split(".")

    cursor.execute(
        f"SELECT TOP 1 {', '.join(primary_key_columns)} FROM {schema}.dbo.{table} ORDER BY NEWID()"
    )
    row = cursor.fetchone()
    if row:
        data = generate_data(columns_dict, primary_key_columns, auto_increment_columns)
        update_values = {k: v for k, v in data.items() if k not in primary_key_columns}
        update_values = {k: v for k, v in update_values.items() if k not in auto_increment_columns}
        set_clause = ", ".join([f"{key}=?" for key in update_values.keys()])
        where_conditions = {key: row[idx] for idx, key in enumerate(primary_key_columns)}
        where_clause = " AND ".join([f"{key}=?" for key in where_conditions.keys()])

        sql = f"UPDATE {schema}.dbo.{table} SET {set_clause} WHERE {where_clause}"
        cursor.execute(
            sql, list(update_values.values()) + list(where_conditions.values())
        )
        db.commit()


# 데이터 삭제 함수
def delete_data(table_name, primary_key_columns):
    schema, table = table_name.split(".")
    cursor.execute(
        f"SELECT TOP 1 {', '.join(primary_key_columns)} FROM {schema}.dbo.{table} ORDER BY RAND()"
    )
    row = cursor.fetchone()
    if row:
        where_clause = " AND ".join([f"{key}=?" for key in primary_key_columns])
        sql = f"DELETE FROM {schema}.dbo.{table} WHERE {where_clause}"
        cursor.execute(sql, row)
        db.commit()


def perform_transactions(
        table_name,
        num_transactions,
        insert_ratio,
        update_ratio,
        delete_ratio,
        columns_dict,
        primary_key_columns,
        auto_increment_columns,
):
    transactions = np.random.choice(
        ["i", "u", "d"],
        size=num_transactions,
        p=[insert_ratio, update_ratio, delete_ratio],
    )
    for action in transactions:
        if action == "i":
            insert_data(table_name, columns_dict, primary_key_columns, auto_increment_columns)
        elif action == "u":
            update_data(table_name, columns_dict, primary_key_columns, auto_increment_columns)
        elif action == "d":
            delete_data(table_name, primary_key_columns)
    print([str(i) for i in transactions])


def schedule_transactions(
        table_name,
        transactions_per_second,
        total_duration_seconds,
        insert_ratio,
        update_ratio,
        delete_ratio,
):
    columns_dict = get_table_schema(table_name)
    primary_key_columns = get_primary_key_columns(columns_dict.values())
    auto_increment_columns = get_auto_increment_columns(columns_dict.values())

    for _ in tqdm(range(total_duration_seconds), desc="Processing duration"):
        start_time = time.time()
        perform_transactions(
            table_name,
            transactions_per_second,
            insert_ratio,
            update_ratio,
            delete_ratio,
            columns_dict,
            primary_key_columns,
            auto_increment_columns,
        )
        time_taken = time.time() - start_time
        time.sleep(max(1 - time_taken, 0))


for table_name in TABLE_LIST:
    schedule_transactions(
        table_name,
        TRANSACTIONS_PER_SECOND,
        TOTAL_DURATION_SECONDS,
        INSERT_RATIO,
        UPDATE_RATIO,
        DELETE_RATIO,
    )

# 연결 종료
db.close()
