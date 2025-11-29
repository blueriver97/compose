import random
import time

import mysql.connector
import numpy as np
from faker import Faker
from tqdm import tqdm

# TODO. MySQL 연결 정보
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "admin"
DB_PASSWORD = "admin"
DEFAULT_DATABASE = "store"

# TODO. 데이터 생성 수 및 비율
TRANSACTIONS_PER_SECOND = 20  # 초당 트랜잭션 수
TOTAL_DURATION_SECONDS = 1  # 총 실행 시간 (초)
INSERT_RATIO = 0.60  # 삽입 비율
UPDATE_RATIO = 0.30  # 갱신 비율
DELETE_RATIO = 0.10  # 삭제 비율

# TODO. 테이블 목록 (<schema>.<table>)
TABLE_LIST = """store.tb_lower,store.TB_UPPER,store.TB_COMPOSITE_KEY""".split(",")

# MySQL 연결 설정
db = mysql.connector.connect(
    host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DEFAULT_DATABASE
)
cursor = db.cursor()

# Faker 인스턴스 생성
fake = Faker()


# 테이블 스키마 가져오기 함수
def get_table_schema(table_name):
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()

    # 컬럼 정보를 딕셔너리로 변환하여 반환
    return {column[0]: column for column in columns}


# Primary Key 컬럼 찾기 함수
def get_primary_key_columns(columns):
    return [column[0] for column in columns if column[3] == "PRI"]


# Auto Increment 키 컬럼 찾기 함수
def get_auto_increment_columns(columns):
    return [column[0] for column in columns if "auto_increment" in column[5].lower()]


def parse_type_and_length(column_type):
    if "(" in column_type and ")" in column_type:
        start_idx = column_type.find("(")
        end_idx = column_type.find(")")
        type_name = column_type[:start_idx]
        type_length = column_type[start_idx + 1: end_idx]
    else:
        type_name = column_type
        type_length = None
    return type_name, type_length


def generate_integer_value(type_name, type_length):
    if "bigint" in type_name:
        return fake.random_int(min=0, max=9223372036854775807)
    elif "tinyint" in type_name and type_length == "1":
        return random.choice([0, 1])
    else:
        return fake.random_int(min=0, max=2147483647)


def generate_string_value(type_name, type_length):
    max_length = int(type_length) if type_length else 255
    return (
        fake.text(max_nb_chars=max_length)
        if "varchar" in type_name or "text" in type_name or "char" in type_name
        else fake.uuid4()
    )


def generate_date_time_value(type_name):
    if "date" in type_name:
        return fake.date_this_decade()
    elif "time" in type_name:
        return fake.time()
    elif "datetime" in type_name or "timestamp" in type_name:
        return fake.date_time_this_decade()


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

    return fake.binary(length=type_length)  # 기본적으로 BLOB 크기로 제한


# 데이터 생성 함수
def generate_data(columns_dict, primary_key_columns, auto_increment_columns):
    data = {}

    for column_name, column_info in columns_dict.items():
        column_type = column_info[1].lower()
        column_default = column_info[4]

        if column_default is not None or column_name in auto_increment_columns:
            continue

        type_name, type_length = parse_type_and_length(column_type)

        if (
                column_name in primary_key_columns
                and column_name not in auto_increment_columns
        ):
            if "int" in type_name:
                data[column_name] = generate_integer_value(type_name, type_length)
            elif ("date" in type_name
                  or "time" in type_name
                  or "datetime" in type_name
                  or "timestamp" in type_name):
                data[column_name] = generate_date_time_value(type_name)
            elif ("float" in type_name
                  or "double" in type_name
                  or "decimal" in type_name):
                data[column_name] = generate_numeric_value(type_name, type_length)
            else:
                data[column_name] = generate_string_value(type_name, type_length)

        else:
            if random.random() < 0.1:  # 10% 확률로 null 값을 할당
                data[column_name] = None
            else:
                if "int" in type_name:
                    data[column_name] = generate_integer_value(type_name, type_length)
                elif (
                        "varchar" in type_name or "text" in type_name or "char" in type_name
                ):
                    data[column_name] = generate_string_value(type_name, type_length)
                elif (
                        "date" in type_name
                        or "time" in type_name
                        or "datetime" in type_name
                        or "timestamp" in type_name
                ):
                    data[column_name] = generate_date_time_value(type_name)
                elif (
                        "float" in type_name
                        or "double" in type_name
                        or "decimal" in type_name
                ):
                    data[column_name] = generate_numeric_value(type_name, type_length)
                elif "blob" in type_name:
                    data[column_name] = generate_blob_value(type_name, type_length)

    return data


# 데이터 삽입 함수
def insert_data(table_name, columns_dict, primary_key_columns, auto_increment_columns):
    data = generate_data(columns_dict, primary_key_columns, auto_increment_columns)
    insert_columns = [col for col in data.keys() if col not in auto_increment_columns]
    insert_values = [data[col] for col in insert_columns]
    sql = f"INSERT INTO {table_name} ({', '.join(insert_columns)}) VALUES ({', '.join(['%s'] * len(insert_columns))})"
    cursor.execute(sql, insert_values)
    db.commit()


# 데이터 갱신 함수
def update_data(table_name, columns_dict, primary_key_columns, auto_increment_columns):
    cursor.execute(
        f"SELECT {', '.join(primary_key_columns)} FROM {table_name} ORDER BY RAND() LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        data = generate_data(columns_dict, primary_key_columns, auto_increment_columns)
        update_values = {
            key: value for key, value in data.items() if key not in primary_key_columns
        }
        update_values = {
            key: value
            for key, value in update_values.items()
            if key not in auto_increment_columns
        }
        set_clause = ", ".join([f"{key}=%s" for key in update_values.keys()])
        where_conditions = {
            key: row[index] for index, key in enumerate(primary_key_columns)
        }
        where_clause = " AND ".join([f"{key}=%s" for key in where_conditions.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        cursor.execute(
            sql, list(update_values.values()) + list(where_conditions.values())
        )
        db.commit()


# 데이터 삭제 함수
def delete_data(table_name, primary_key_columns):
    cursor.execute(
        f"SELECT {', '.join(primary_key_columns)} FROM {table_name} ORDER BY RAND() LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        where_clause = " AND ".join([f"{key}=%s" for key in primary_key_columns])
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        cursor.execute(sql, row)
        db.commit()


# 트랜잭션 발생 함수
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
    transactions: np.ndarray = np.random.choice(
        ["insert", "update", "delete"],
        size=num_transactions,
        p=[insert_ratio, update_ratio, delete_ratio],
    )
    for _, action in enumerate(transactions):
        if action == "insert":
            insert_data(
                table_name, columns_dict, primary_key_columns, auto_increment_columns
            )
        elif action == "update":
            update_data(
                table_name, columns_dict, primary_key_columns, auto_increment_columns
            )
        elif action == "delete":
            delete_data(table_name, primary_key_columns)
    print(f"{[t[0] for t in transactions]}")


# 주기적인 트랜잭션 수행 함수
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
