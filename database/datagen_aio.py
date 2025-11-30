import time
import logging
import random
import re
from typing import Dict, List, Any, Optional, Tuple, Callable

import aiomysql
import asyncio
from mysql.connector.cursor import MySQLCursor
import numpy as np
from faker import Faker
from tqdm import tqdm

from config import DatagenConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TableSchema:
    """테이블 스키마 정보를 저장하고 파싱하는 클래스"""

    def __init__(self, table_name: str, columns: List[Tuple]):
        self.table_name = table_name
        self.columns_info: Dict[str, Dict[str, Any]] = {}
        self.primary_keys: List[str] = []
        self.auto_increments: List[str] = []

        for col in columns:
            # MySQL DESCRIBE output format:
            # Field, Type, Null, Key, Default, Extra
            col_name = col[0]
            col_type = col[1]
            col_nullable = col[2]
            col_key = col[3]
            col_extra = col[5]

            type_name, type_length = self._parse_type(col_type)

            self.columns_info[col_name] = {
                "type_name": type_name,
                "type_length": type_length,
                "is_nullable": col_nullable == "YES"
            }

            if col_key == "PRI":
                self.primary_keys.append(col_name)
            if "auto_increment" in col_extra.lower():
                self.auto_increments.append(col_name)

    def _parse_type(self, column_type: str) -> Tuple[str, Optional[str]]:
        # e.g., "varchar(255)" -> ("varchar", "255")
        match = re.match(r"([a-z]+)(?:\((.+)\))?", column_type.lower())
        if match:
            return match.group(1), match.group(2)
        return column_type, None


class AsyncMySQLDataGenerator:
    """MySQL 데이터 생성 및 부하 테스트 실행기"""

    def __init__(self, config: DatagenConfig):
        self.config = config
        self.fake = Faker()
        # DB 연결 설정
        self.pool: Optional[aiomysql.Pool] = None

        # random.Generator
        self.rng = np.random.default_rng(self.config.generate.seed)

        # 타입별 데이터 생성 전략 매핑
        self.type_generators: Dict[str, Callable] = {
            "int": self._gen_int,
            "tinyint": self._gen_tinyint,
            "bigint": self._gen_bigint,
            "varchar": self._gen_string,
            "char": self._gen_string,
            "text": self._gen_string,
            "date": lambda length, **kwargs: self.fake.date_this_decade(),
            "time": lambda length, **kwargs: self.fake.time(),
            "datetime": lambda length, **kwargs: self.fake.date_time_this_decade(),
            "timestamp": lambda length, **kwargs: self.fake.date_time_this_decade(),
            "float": self._gen_float,
            "double": self._gen_double,
            "decimal": self._gen_decimal,
            "blob": self._gen_blob,
            "longblob": self._gen_blob,
        }

    async def setup(self):
        """DB Connection Pool 생성"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.user,
                password=self.config.database.password,
                db=self.config.database.database,
                autocommit=False,  # 트랜잭션 수동 제어
                minsize=1,
                maxsize=10  # 필요에 따라 조절
            )
            logger.info("Database connection pool created.")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    async def close(self):
        """Pool 종료"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed.")

    # --- Value Generators ---
    def _gen_int(self, length: str, **kwargs) -> int:
        return self.fake.random_int(min=0, max=2147483647)

    def _gen_tinyint(self, length: str, **kwargs) -> int:
        return random.choice([0, 1]) if length == "1" else self.fake.random_int(0, 127)

    def _gen_bigint(self, length: str, **kwargs) -> int:
        return self.fake.random_int(min=0, max=9223372036854775807)

    def _gen_string(self, length: str, **kwargs) -> str:
        max_chars = int(length) if length else 255
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

    def _generate_row_data(self, schema: TableSchema) -> Dict[str, Any]:
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

    # --- SQL Operations ---
    async def insert_data(self, cursor: MySQLCursor, schema: TableSchema):
        data = self._generate_row_data(schema)
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)

        sql = f"INSERT INTO {schema.table_name} ({col_names}) VALUES ({placeholders})"
        await cursor.execute(sql, values)

    async def update_data(self, cursor: MySQLCursor, schema: TableSchema):
        if not schema.primary_keys:
            return

        pk_select = ", ".join(schema.primary_keys)
        await cursor.execute(f"SELECT {pk_select} FROM {schema.table_name} ORDER BY RAND() LIMIT 1")
        row = await cursor.fetchone()

        if row:
            data = self._generate_row_data(schema)
            update_data = {
                k: v for k, v in data.items()
                if k not in schema.primary_keys and k not in schema.auto_increments
            }
            if not update_data:
                return

            set_clause = ", ".join([f"{k}=%s" for k in update_data.keys()])
            where_clause = " AND ".join([f"{k}=%s" for k in schema.primary_keys])

            sql = f"UPDATE {schema.table_name} SET {set_clause} WHERE {where_clause}"
            await cursor.execute(sql, list(update_data.values()) + list(row))

    async def delete_data(self, cursor: MySQLCursor, schema: TableSchema):
        if not schema.primary_keys:
            return

        pk_select = ", ".join(schema.primary_keys)
        await cursor.execute(f"SELECT {pk_select} FROM {schema.table_name} ORDER BY RAND() LIMIT 1")
        row = await cursor.fetchone()

        if row:
            where_clause = " AND ".join([f"{k}=%s" for k in schema.primary_keys])
            sql = f"DELETE FROM {schema.table_name} WHERE {where_clause}"
            await cursor.execute(sql, row)

    async def process_table(self, table_name: str):
        logger.info(f"Processing table: {table_name}")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"DESCRIBE {table_name}")
                columns = await cursor.fetchall()
                schema = TableSchema(table_name, columns)

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
            batch_actions = self.rng.choice(actions, size=tps, p=probs)
            logger.info(f"Batch actions: {batch_actions.tolist()}")

            # Connection Pool에서 커넥션 획득
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    try:
                        for action in batch_actions:
                            if action == "I":
                                await self.insert_data(cursor, schema)
                            elif action == "U":
                                await self.update_data(cursor, schema)
                            elif action == "D":
                                await self.delete_data(cursor, schema)

                        await conn.commit()

                    except Exception as e:
                        logger.error(f"[{table_name}] Transaction batch failed: {e}")
                        await conn.rollback()

            # TPS 유지를 위한 Sleep
            elapsed = time.time() - start_time
            sleep_time = max(1.0 - elapsed, 0)
            await asyncio.sleep(sleep_time)


async def main():
    try:
        config = DatagenConfig()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        exit(1)

    generator = AsyncMySQLDataGenerator(config)

    try:
        await generator.setup()

        # 모든 테이블에 대해 동시에 태스크 생성 (Concurrency)
        tasks = [generator.process_table(table) for table in config.tables]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        await generator.close()
    except Exception:
        logger.error(f"Unexpected fatal error: {e}")
    finally:
        await generator.close()


if __name__ == '__main__':
    asyncio.run(main())
