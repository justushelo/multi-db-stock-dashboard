# Imports
from typing import Literal, Optional

import pandas as pd
from pymongo.database import Database
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


class DatabaseManager:
    """
    Class for connecting to PostgreSQL, MongoDB and SQLite.
    Functions include getting tables, columns and loading data for further processing.
    Additional functions help to write or delete data from databases.
    """

    def __init__(self, postgres_engine: Engine, mongo_db: Database, sqlite_engine: Engine) -> None:
        self.postgres_engine = postgres_engine
        self.mongo_db = mongo_db
        self.sqlite_engine = sqlite_engine

    # PostgreSQL functions

    def get_postgres_tables(self) -> list:
        """
        Get list of PostgreSQL tables.
        """
        inspector = inspect(self.postgres_engine)
        tables = inspector.get_table_names()
        return tables

    def get_postgres_columns(self, table: str) -> list:
        """
        Fetch column names for given table in PostgreSQL.
        """
        inspector = inspect(self.postgres_engine)
        columns = inspector.get_columns(table)
        column_names = [col["name"] for col in columns]
        return column_names

    def load_postgres_data(self, table: str, columns: list) -> pd.DataFrame:
        """
        Load data from PostgreSQL into DataFrame.
        """
        query_columns = ", ".join(columns)
        df = pd.read_sql(
            text(f"SELECT {query_columns} FROM {table}"), self.postgres_engine.connect()
        )
        return df

    def insert_postgresql_data(
        self, df: pd.DataFrame, table: str, mode: Literal["fail", "replace", "append"] = "replace"
    ) -> None:
        """
        Insert or replace data in PostgreSQL while preserving table schema and ensuring atomicity.
        """
        if mode == "replace":
            with self.postgres_engine.begin() as conn:
                conn.execute(text(f"TRUNCATE TABLE {table}"))
                df.to_sql(name=table, con=conn, if_exists="append", index=False)
        else:
            with self.postgres_engine.begin() as conn:
                df.to_sql(name=table, con=conn, if_exists=mode, index=False)
        return None

    def delete_postgres_table(self, table: str) -> None:
        with self.postgres_engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            conn.commit()
        return None

    def update_postgresql_data(
        self, table: str, set_values: dict, condition_values: dict
    ) -> int:
        """
        Update specific records in PostgreSQL table based on conditions.
        """
        if not set_values or not condition_values:
            return 0
        set_clause = ", ".join([f"{k} = :{k}_set" for k in set_values.keys()])
        where_clause = " AND ".join(
            [f"{k} = :{k}_cond" for k in condition_values.keys()]
        )
        query = text(f"UPDATE {table} SET {set_clause} WHERE {where_clause}")

        params = {f"{k}_set": v for k, v in set_values.items()}
        params.update({f"{k}_cond": v for k, v in condition_values.items()})

        with self.postgres_engine.begin() as conn:
            result = conn.execute(query, params)
            return result.rowcount

    # SQLite functions

    def get_sqlite_tables(self) -> list:
        """
        Get list of SQLite tables.
        """
        inspector = inspect(self.sqlite_engine)
        tables = inspector.get_table_names()
        return tables

    def get_sqlite_columns(self, table: str) -> list:
        """
        Fetch column names for given table in SQLite.
        """
        inspector = inspect(self.sqlite_engine)
        columns = inspector.get_columns(table)
        column_names = [col["name"] for col in columns]
        return column_names

    def load_sqlite_data(self, table: str, columns: list) -> pd.DataFrame:
        """
        Load data from SQLite into DataFrame.
        """
        query_columns = ", ".join(columns)
        df = pd.read_sql(
            text(f"SELECT {query_columns} FROM {table}"), self.sqlite_engine.connect()
        )
        return df

    def insert_sqlite_data(
        self, df: pd.DataFrame, table: str, mode: Literal["fail", "replace", "append"] = "replace"
    ) -> None:
        """
        Insert or replace data in SQLite while preserving table schema and ensuring atomicity.
        """
        if mode == "replace":
            with self.sqlite_engine.begin() as conn:
                conn.execute(text(f"DELETE FROM {table}"))
                df.to_sql(name=table, con=conn, if_exists="append", index=False)
        else:
            with self.sqlite_engine.begin() as conn:
                df.to_sql(name=table, con=conn, if_exists=mode, index=False)

    def delete_sqlite_table(self, table: str) -> None:
        with self.sqlite_engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            conn.commit()
        return None

    def update_sqlite_data(
        self, table: str, set_values: dict, condition_values: dict
    ) -> int:
        """
        Update specific records in SQLite table based on conditions.
        """
        if not set_values or not condition_values:
            return 0
        set_clause = ", ".join([f"{k} = :{k}_set" for k in set_values.keys()])
        where_clause = " AND ".join(
            [f"{k} = :{k}_cond" for k in condition_values.keys()]
        )
        query = text(f"UPDATE {table} SET {set_clause} WHERE {where_clause}")

        params = {f"{k}_set": v for k, v in set_values.items()}
        params.update({f"{k}_cond": v for k, v in condition_values.items()})

        with self.sqlite_engine.begin() as conn:
            result = conn.execute(query, params)
            return result.rowcount

    # MongoDB functions

    def get_mongo_tables(self) -> list:
        """
        Get list of all MongoDB tables.
        """
        tables = self.mongo_db.list_collection_names()
        return tables

    def get_mongo_columns(self, table: str) -> list:
        """
        Get column names from first document in MongoDB collection.
        """
        first_doc = self.mongo_db[table].find_one()
        if not first_doc:
            return []
        columns = [column for column in first_doc.keys() if column != "_id"]
        return columns

    def load_mongo_data(self, table: str, columns: list) -> pd.DataFrame:
        """
        Load data from MongoDB collection with selected columns.
        Return Pandas DataFrame.
        """
        projection = dict.fromkeys(columns, 1)
        projection["_id"] = 0
        data = list(self.mongo_db[table].find({}, projection))
        df = pd.DataFrame(data)
        return df

    def insert_mongo_data(
        self, df: pd.DataFrame, collection_name: str, mode: Literal["fail", "replace", "append"] = "append"
    ) -> Optional[int]:
        """
        Insert or replace data in MongoDB collection.
        """
        collection = self.mongo_db[collection_name]

        # Convert DataFrame to records
        records = df.to_dict("records")

        # Convert datetime columns to MongoDB-compatible format
        for record in records:
            for key, value in record.items():
                if hasattr(value, "to_pydatetime"):
                    record[key] = value.to_pydatetime()
                elif pd.isna(value):
                    record[key] = None

        # Replace mode: drop collection first
        if mode == "replace":
            collection.drop()

        # Insert records
        if records:
            result = collection.insert_many(records)
            return len(result.inserted_ids)
        return None

    def update_mongo_data(self, table: str, set_values: dict, condition_values: dict) -> int:
        """
        Update specific records in MongoDB collection based on conditions.
        """
        if not set_values or not condition_values:
            return 0

        result = self.mongo_db[table].update_many(
            condition_values, {"$set": set_values}
        )
        return result.modified_count
