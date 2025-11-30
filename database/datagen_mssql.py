import random
import time
import pyodbc
from pyodbc import Cursor, Connection
import numpy as np
from faker import Faker
import logging
from contextlib import contextmanager
from config import DatagenConfig
from typing import Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TableSchema:
    def __init__(self, table_name: str, columns: list[tuple]):
        self.table_name = table_name
        self.columns_info: dict[str, dict[str, Any]] = {}
        self.primary_keys: list[str] = []
        self.auto_increments: list[str] = []

        for col in columns:
            col_name = col[0]
            col_type = col[1]
            col_length = col[2]
            col_nullable = col[3]
            col_key = col[4]
            col_default = col[5]
            col_auto = col[6]

            self.columns_info[col_name] = {
                "type_name": col_type,
                "type_length": col_length,
                "is_nullable": col_nullable == "YES"
            }

            if col_key == "YES":
                self.primary_keys.append(col_name)
            if col_auto == "YES":
                self.auto_increments.append(col_name)


class SQLServerDataGenerator:
    def __init__(self, config: DatagenConfig):
        self.config = config
        self.fake = Faker()
        self.db_config = self.config.database
        self.conn: Optional[Connection] = None

        # 타입별 데이터 생성 전략 매핑
        self.type_generators: dict[str, callable] = {
            "int": self._gen_int,
            "tinyint": self._gen_tinyint,
            "bigint": self._gen_bigint,
            "varchar": self._gen_string,
            "char": self._gen_string,
            "text": self._gen_string,
            "date": lambda length, **kwargs: self.fake.date_this_decade(),
            "time": lambda length, **kwargs: self.fake.time(),
            "datetime": lambda length, **kwargs: self.fake.date_time_this_decade(),
            "datetime2": lambda length, **kwargs: self.fake.date_time_this_decade(),
            "timestamp": lambda length, **kwargs: self.fake.date_time_this_decade(),
            "float": self._gen_float,
            "double": self._gen_double,
            "decimal": self._gen_decimal,
            "blob": self._gen_blob,
            "longblob": self._gen_blob,
            "mediumblob": self._gen_blob,
            "tinyblob": self._gen_blob,
            "varbinary": self._gen_blob,
            "binary": self._gen_blob,
            "image": self._gen_blob,
            "bit": self._gen_boolean,
        }

    @contextmanager
    def get_cursor(self):
        """DB 커서 컨텍스트 매니저 (재연결 로직 포함)"""
        try:
            if self.conn is None or self.conn.closed:
                conn_str = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={self.db_config.host},{self.db_config.port};"
                    f"DATABASE={self.db_config.database};"
                    f"UID={self.db_config.user};PWD={self.db_config.password};"
                    f"Encrypt=no;TrustServerCertificate=yes"
                )
                self.conn = pyodbc.connect(conn_str)
            cursor = self.conn.cursor()
            yield cursor
        except pyodbc.Error as err:
            logger.error(f"Database connection error: {err}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed")

    def _gen_boolean(self, length: str, **kwargs) -> bool:
        return self.fake.boolean()

    def _gen_int(self, length: str, **kwargs) -> int:
        return self.fake.random_int(min=0, max=2147483647)

    def _gen_tinyint(self, length: str, **kwargs) -> int:
        return random.choice([0, 1]) if length == "1" else self.fake.random_int(0, 127)

    def _gen_bigint(self, length: str, **kwargs) -> int:
        return self.fake.random_int(min=0, max=9223372036854775807)

    def _gen_string(self, length: str, **kwargs) -> str:
        max_chars = int(length) if length else 255
        max_chars = 65535 if max_chars < 0 else max_chars
        return self.fake.text(max_nb_chars=min(max_chars, 1000))

    def _gen_float(self, length: str, **kwargs) -> float:
        return self.fake.pyfloat(left_digits=4, right_digits=2, positive=True)

    def _gen_double(self, length: str, **kwargs) -> float:
        return self.fake.pyfloat(left_digits=6, right_digits=3, positive=True)

    def _gen_decimal(self, length: str, **kwargs) -> Any:
        prec, scale = (5, 2)
        if length and "," in length:
            parts = length.split(",")
            prec, scale = int(parts[0]), int(parts[1])
        return self.fake.pydecimal(left_digits=prec - scale, right_digits=scale, positive=True)

    def _gen_blob(self, length: str, type_name: str = "blob") -> bytes:
        size_map = {"tinyblob": 255, "blob": 65535, "mediumblob": 16777215}
        limit = min(size_map.get(type_name, 65535), 1024)
        return self.fake.binary(length=limit)

    def _generate_row_data(self, schema: TableSchema) -> dict[str, Any]:
        """스키마에 맞는 랜덤 데이터 생성"""
        data = {}
        for col_name, info in schema.columns_info.items():
            if col_name in schema.auto_increments:
                continue

            # Nullable 컬럼에 대해 10% 확률로 NULL 처리
            if info["is_nullable"] and random.random() < 0.1:
                data[col_name] = None
                continue

            generator = self.type_generators.get(info["type_name"])
            if generator:
                data[col_name] = generator(info["type_length"], type_name=info["type_name"])
            else:
                data[col_name] = self.fake.text(max_nb_chars=50)
        return data

    def insert_data(self, cursor: Cursor, schema: TableSchema):
        data = self._generate_row_data(schema)
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(['?'] * len(columns))
        col_names = ", ".join(columns)
        sql = f"INSERT INTO dbo.{schema.table_name} ({col_names}) VALUES ({placeholders});"
        cursor.execute(sql, values)

    def update_data(self, cursor: Cursor, schema: TableSchema):
        if not schema.primary_keys:
            return

        pk_select = ", ".join(schema.primary_keys)
        cursor.execute(f"SELECT TOP 1 {pk_select} FROM dbo.{schema.table_name} ORDER BY NEWID();")
        row = cursor.fetchone()

        if row:
            data = self._generate_row_data(schema)
            update_data = {
                k: v for k, v in data.items()
                if k not in schema.primary_keys and k not in schema.auto_increments
            }
            if not update_data:
                return

            set_clause = ", ".join([f"{k}=?" for k in update_data.keys()])
            where_clause = " AND ".join([f"{k}=?" for k in schema.primary_keys])

            sql = f"UPDATE dbo.{schema.table_name} SET {set_clause} WHERE {where_clause};"
            cursor.execute(sql, list(update_data.values()) + list(row))

    def delete_data(self, cursor: Cursor, schema: TableSchema):
        if not schema.primary_keys:
            return

        pk_select = ", ".join(schema.primary_keys)
        cursor.execute(f"SELECT TOP 1 {pk_select} FROM dbo.{schema.table_name} ORDER BY NEWID();")
        row = cursor.fetchone()

        if row:
            where_clause = " AND ".join([f"{k}=?" for k in schema.primary_keys])
            sql = f"DELETE FROM dbo.{schema.table_name} WHERE {where_clause};"
            cursor.execute(sql, row)

    def process_table(self, table_name: str):
        logger.info(f"Processing table {table_name}")

        with self.get_cursor() as cursor:
            cursor.execute(self.schema_statement(table_name))
            result = cursor.fetchall()
            schema = TableSchema(table_name, result)

        gen_config = self.config.generate
        total_duration = gen_config.duration
        tps = gen_config.transactions

        # 확률 정규화 (합이 1이 되도록 조정)
        raw_probs = [gen_config.insert_rate, gen_config.update_rate, gen_config.delete_rate]
        total_rate = sum(raw_probs)
        if total_rate == 0:
            probs = [1.0, 0.0, 0.0]  # 기본값: Insert Only
        else:
            probs = [r / total_rate for r in raw_probs]

        actions = ["I", "U", "D"]
        logger.info(
            f"Workload distribution for {table_name}: I={probs[0]:.2f}, U={probs[1]:.2f}, D={probs[2]:.2f}")

        for _ in range(total_duration):
            start_time = time.time()

            # TPS 만큼 동작 결정
            batch_actions = np.random.choice(actions, size=tps, p=probs)
            logger.info(f"Batch actions: {batch_actions.tolist()}")

            with self.get_cursor() as cursor:
                try:
                    for action in batch_actions:
                        if action == "I":
                            self.insert_data(cursor, schema)
                        elif action == "U":
                            self.update_data(cursor, schema)
                        elif action == "D":
                            self.delete_data(cursor, schema)
                    self.conn.commit()
                except Exception as e:
                    logger.error(f"Transaction batch failed: {e}")
                    self.conn.rollback()

            # TPS 유지를 위한 Sleep
            elapsed = time.time() - start_time
            sleep_time = max(1.0 - elapsed, 0)
            time.sleep(sleep_time)

    def schema_statement(self, table_name: str):
        stmt = f"""
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
WHERE TBL_SPEC.TABLE_NAME = '{table_name}'
ORDER BY TBL_SPEC.TABLE_NAME, TBL_SPEC.ORDINAL_POSITION;
        """
        return stmt


if __name__ == '__main__':
    try:
        config = DatagenConfig()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        exit(1)

    generator = SQLServerDataGenerator(config)

    try:
        for table in config.tables:
            generator.process_table(table)

    except KeyboardInterrupt:
        logger.info("Stopping data generation...")
    except Exception as e:
        logger.error(f"Unexpected fatal error: {e}")
    finally:
        generator.close()
