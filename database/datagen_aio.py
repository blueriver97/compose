import time
import random
import asyncio
import argparse
import aiomysql
import numpy as np
from tqdm import tqdm
from faker import Faker

# Faker 인스턴스 생성
fake = Faker()


async def get_table_schema(pool, table_name):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"DESCRIBE {table_name}")
            columns = await cursor.fetchall()
            return {column[0]: column for column in columns}


def get_primary_key_columns(columns):
    return [column[0] for column in columns if column[3] == 'PRI']


def get_auto_increment_columns(columns):
    return [column[0] for column in columns if 'auto_increment' in column[5].lower()]


def generate_data(columns_dict, primary_key_columns, auto_increment_columns):
    data = {}
    for column_name, column_info in columns_dict.items():
        column_type = column_info[1].lower()
        column_default = column_info[4]

        if '(' in column_type and ')' in column_type:
            start_idx = column_type.find('(')
            end_idx = column_type.find(')')
            type_name = column_type[:start_idx]
            type_length = column_type[start_idx + 1:end_idx]
        else:
            type_name = column_type
            type_length = None

        if column_default is not None:
            continue

        if column_name in primary_key_columns and column_name not in auto_increment_columns:
            if 'int' in type_name:
                if 'bigint' in type_name:
                    data[column_name] = fake.random_int(min=0, max=9223372036854775807)
                elif 'tinyint' in type_name and type_length == '1':
                    data[column_name] = random.choice([0, 1])
                else:
                    data[column_name] = fake.random_int(min=0, max=2147483647)
            elif 'varchar' in type_name or 'text' in type_name or 'char' in type_name:
                data[column_name] = fake.uuid4()
        else:
            null_chance = 0.1  # 예시로 10%의 확률로 null 값을 할당하도록 설정
            if random.random() < null_chance:
                data[column_name] = None
            else:
                if 'int' in type_name:
                    if 'bigint' in type_name:
                        data[column_name] = fake.random_int(min=0, max=9223372036854775807)
                    elif 'tinyint' in type_name and type_length == '1':
                        data[column_name] = random.choice([0, 1])
                    else:
                        data[column_name] = fake.random_int(min=0, max=2147483647)
                elif 'varchar' in type_name or 'text' in type_name or 'char' in type_name:
                    max_length = int(type_length) if type_length else 255
                    data[column_name] = fake.text(max_nb_chars=max_length)
                elif 'date' in type_name:
                    data[column_name] = fake.date_this_decade()
                elif 'time' in type_name:
                    data[column_name] = fake.time()
                elif 'datetime' in type_name or 'timestamp' in type_name:
                    data[column_name] = fake.date_time_this_decade()
                elif 'float' in type_name:
                    data[column_name] = fake.pyfloat(left_digits=4, right_digits=2, positive=True)
                elif 'double' in type_name:
                    data[column_name] = fake.pyfloat(left_digits=6, right_digits=3, positive=True)
                elif 'decimal' in type_name:
                    precision = int(type_length.split(',')[0]) if type_length else 5
                    scale = int(type_length.split(',')[1]) if type_length and ',' in type_length else 2
                    data[column_name] = fake.pydecimal(left_digits=precision - scale, right_digits=scale, positive=True)

    return data


async def insert_data(pool, table_name, columns_dict, primary_key_columns, auto_increment_columns):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            data = generate_data(columns_dict, primary_key_columns, auto_increment_columns)
            insert_columns = [col for col in data.keys() if col not in auto_increment_columns]
            insert_values = [data[col] for col in insert_columns]
            sql = f"INSERT INTO {table_name} ({', '.join(insert_columns)}) VALUES ({', '.join(['%s'] * len(insert_columns))})"
            await cursor.execute(sql, insert_values)
            await conn.commit()


async def update_data(pool, table_name, columns_dict, primary_key_columns, auto_increment_columns):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"SELECT {', '.join(primary_key_columns)} FROM {table_name} ORDER BY RAND() LIMIT 1")
            row = await cursor.fetchone()
            if row:
                data = generate_data(columns_dict, primary_key_columns, auto_increment_columns)
                update_values = {key: value for key, value in data.items() if key not in primary_key_columns}
                update_values = {key: value for key, value in update_values.items() if
                                 key not in auto_increment_columns}
                set_clause = ', '.join([f"{key}=%s" for key in update_values.keys()])
                where_conditions = {key: row[index] for index, key in enumerate(primary_key_columns)}
                where_clause = ' AND '.join([f"{key}=%s" for key in where_conditions.keys()])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                await cursor.execute(sql, list(update_values.values()) + list(where_conditions.values()))
                await conn.commit()


async def delete_data(pool, table_name, primary_key_columns):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"SELECT {', '.join(primary_key_columns)} FROM {table_name} ORDER BY RAND() LIMIT 1")
            row = await cursor.fetchone()
            if row:
                where_clause = ' AND '.join([f"{key}=%s" for key in primary_key_columns])
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                await cursor.execute(sql, row)
                await conn.commit()


async def perform_transactions(pool, table_name, num_transactions, insert_ratio, update_ratio, delete_ratio,
                               columns_dict, primary_key_columns, auto_increment_columns):
    transactions: np.ndarray = np.random.choice(['insert', 'update', 'delete'],
                                                size=num_transactions,
                                                p=[insert_ratio, update_ratio, delete_ratio])
    for _, action in enumerate(transactions):
        if action == 'insert':
            await insert_data(pool, table_name, columns_dict, primary_key_columns, auto_increment_columns)
        elif action == 'update':
            await update_data(pool, table_name, columns_dict, primary_key_columns, auto_increment_columns)
        elif action == 'delete':
            await delete_data(pool, table_name, primary_key_columns)


async def schedule_transactions(table_name, transactions_per_second, total_transactions,
                                insert_ratio=0.40, update_ratio=0.40, delete_ratio=0.20):
    pool = await aiomysql.create_pool(host='localhost', user='root', password='mysql', db='store')

    # 테이블 스키마 정보 한 번 받아오기
    columns_dict = await get_table_schema(pool, table_name)
    primary_key_columns = get_primary_key_columns(columns_dict.values())
    auto_increment_columns = get_auto_increment_columns(columns_dict.values())

    num_intervals = total_transactions // transactions_per_second  # 총 실행 시간 동안 실행할 횟수

    for _ in tqdm(range(num_intervals), desc="Processing intervals"):
        start_time = time.time()
        await perform_transactions(pool, table_name, transactions_per_second,
                                   insert_ratio, update_ratio, delete_ratio,
                                   columns_dict, primary_key_columns, auto_increment_columns)
        time_taken = time.time() - start_time
        await asyncio.sleep(max(1 - time_taken, 0))

    pool.close()
    await pool.wait_closed()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Async MySQL Transactions Scheduler')
    parser.add_argument('--table', type=str, default='tb_lower', help='Name of the table to perform transactions on')
    parser.add_argument('--transactions-per-second', type=int, default=10,
                        help='Number of transactions to perform per second')
    parser.add_argument('--total-transactions', type=int, default=100, help='Total number of transactions to perform')
    parser.add_argument('--insert-rate', type=float, default=0.40, help='Insert Transaction ratio')
    parser.add_argument('--update-rate', type=float, default=0.40, help='Update Transaction ratio')
    parser.add_argument('--delete-rate', type=float, default=0.20, help='Delete Transaction ratio')
    args = parser.parse_args()

    asyncio.run(schedule_transactions(args.table, args.transactions_per_second, args.total_transactions,
                                      args.insert_rate, args.update_rate, args.delete_rate))
