# Imports
import pandas as pd
import pymongo
import streamlit as st
from sqlalchemy import create_engine, text

from library import DatabaseManager
from StockDataDownloader import StockDataDownloader

st.set_page_config(
    page_title="Write Into Database", layout="wide", initial_sidebar_state="expanded"
)

st.title("Edit data inside database")

# Database connections
DB_HOST = st.secrets["postgres"]["host"]
DB_PORT = st.secrets["postgres"]["port"]
DB_NAME = st.secrets["postgres"]["db"]
DB_USER = st.secrets["postgres"]["user"]
DB_PASSWORD = st.secrets["postgres"]["password"]
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
postgres_engine = create_engine(DATABASE_URL)

mongo_url = st.secrets.get("mongo", {}).get("url", "mongodb://localhost:27017")
mongo_db_name = st.secrets.get("mongo", {}).get("db", "Assignment3")
mongo_connection = pymongo.MongoClient(mongo_url)
mongo_db = mongo_connection[mongo_db_name]

sqlite_path = st.secrets.get("sqlite", {}).get("path", "assignment3.db")
sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")

# Create database manager object
database_manager = DatabaseManager(postgres_engine, mongo_db, sqlite_engine)

pg_tables = database_manager.get_postgres_tables() or []
mongo_tables = database_manager.get_mongo_tables() or []
sqlite_tables = database_manager.get_sqlite_tables() or []

all_tables = list(set(pg_tables + mongo_tables + sqlite_tables))

# UI for choosing tables
selected_tables = st.multiselect("Choose table", all_tables)


# Get tables/collections
def get_table_locations(table):
    locations = []
    if table in pg_tables:
        locations.append("postgres")
    if table in sqlite_tables:
        locations.append("sqlite")
    if table in mongo_tables:
        locations.append("mongo")
    return locations


# Choose ticker and dates
col1, col2, col3 = st.columns(3)

with col1:
    ticker_input = st.text_input("Stock Ticker", placeholder="AAPL")
    ticker = ticker_input.upper().strip() if ticker_input else ""

with col2:
    start_date = st.date_input("Start Date", value=pd.to_datetime("2015-01-01"))
    if isinstance(start_date, tuple):
        start_date = start_date[0] if start_date else pd.to_datetime("2015-01-01").date()

with col3:
    end_date = st.date_input("End Date", value=pd.to_datetime("2015-01-02"))
    if isinstance(end_date, tuple):
        end_date = end_date[0] if end_date else pd.to_datetime("2015-01-02").date()

if ticker and st.button("Download Data"):
    try:
        downloader = StockDataDownloader(start=start_date, end=end_date)
        df = downloader.get_data(ticker)

        st.success(f"Downloaded {len(df)} records")
        st.dataframe(df, use_container_width=True)

        st.session_state["df_to_write"] = df

    except Exception as e:
        st.error(f"Download error: {e}")


# Writing functionality
if "df_to_write" in st.session_state and selected_tables:
    if st.button("Insert Into Database(s)"):
        df = st.session_state["df_to_write"]

        for table in selected_tables:
            locations = get_table_locations(table)

            for location in locations:
                try:
                    if location == "postgres":
                        database_manager.insert_postgresql_data(
                            df, table, mode="append"
                        )
                    elif location == "sqlite":
                        database_manager.insert_sqlite_data(df, table, mode="append")
                    elif location == "mongo":
                        database_manager.insert_mongo_data(df, table, mode="append")

                    st.success(f"Inserted into {table} ({location})")
                except Exception as e:
                    st.error(f"Insertion failed for {table} in {location}: {e}")

st.subheader("Delete Data")

delete_table = st.selectbox("Delete from table", all_tables)
delete_ticker = st.text_input("Ticker to delete (symbol column)")


def delete_symbol(table, ticker):
    locations = get_table_locations(table)
    messages = []

    for database in locations:
        try:
            if database == "postgres":
                with postgres_engine.begin() as conn:
                    result = conn.execute(
                        text(f"DELETE FROM {table} WHERE symbol = :sym"),
                        {"sym": ticker},
                    )
                    messages.append(
                        f"{result.rowcount} rows deleted from PostgreSQL table '{table}'"
                    )

            elif database == "sqlite":
                with sqlite_engine.begin() as conn:
                    result = conn.execute(
                        text(f"DELETE FROM {table} WHERE symbol = :sym"),
                        {"sym": ticker},
                    )
                    messages.append(
                        f"{result.rowcount} rows deleted from SQLite table '{table}'"
                    )

            elif database == "mongo":
                result = mongo_db[table].delete_many({"symbol": ticker})
                messages.append(
                    f"{result.deleted_count} documents deleted from MongoDB collection '{table}'"
                )

        except Exception as e:
            messages.append(f"Delete error in {database}: {e}")

    return "\n".join(messages) if messages else "No databases found to delete from."


if st.button("Delete"):
    if not delete_ticker:
        st.warning("Please enter the ticker to delete.")
    else:
        msg = delete_symbol(delete_table, delete_ticker)
        st.success(msg)

st.subheader("Update Data")
update_table = st.selectbox("Update in table", all_tables, key="update_table")
if not update_table:
    update_table = ""
update_ticker = st.text_input(
    "Ticker to update (symbol column)", key="update_ticker"
).upper()
update_date = st.date_input(
    "Date of record to update", value=pd.to_datetime("2015-01-01")
)
if isinstance(update_date, tuple):
    update_date = update_date[0] if update_date else pd.to_datetime("2015-01-01").date()
update_close = st.number_input("New Close Price", value=0.0, format="%.2f")

if st.button("Update"):
    if not update_ticker:
        st.warning("Please enter the ticker to update.")
    elif update_date is None:
        st.warning("Please provide a valid date.")
    else:
        locations = get_table_locations(update_table)
        messages = []

        from datetime import datetime

        dt_obj = datetime.combine(update_date, datetime.min.time())
        # SQLite pandas default datetime serialization is string formatted.
        dt_str = dt_obj.strftime("%Y-%m-%d 00:00:00.000000")

        for loc in locations:
            try:
                if loc == "postgres":
                    cnt = database_manager.update_postgresql_data(
                        update_table,
                        {"close": update_close},
                        {"symbol": update_ticker, "date": dt_obj},
                    )
                    messages.append(
                        f"Updated {cnt} rows in PostgreSQL '{update_table}'"
                    )
                elif loc == "sqlite":
                    cnt = database_manager.update_sqlite_data(
                        update_table,
                        {"close": update_close},
                        {"symbol": update_ticker, "date": dt_str},
                    )
                    messages.append(f"Updated {cnt} rows in SQLite '{update_table}'")
                elif loc == "mongo":
                    cnt = database_manager.update_mongo_data(
                        update_table,
                        {"close": update_close},
                        {"symbol": update_ticker, "date": dt_obj},
                    )
                    messages.append(
                        f"Updated {cnt} documents in MongoDB '{update_table}'"
                    )
            except Exception as e:
                messages.append(f"Update error in {loc}: {e}")

        st.success("\n".join(messages))
