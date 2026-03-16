import pandas as pd
import pymongo
import streamlit as st
from sqlalchemy import create_engine
from library import DatabaseManager

st.set_page_config(page_title="Stock Dashboard", initial_sidebar_state="expanded")
st.title("Stock Dashboard")

DB_HOST = st.secrets["postgres"]["host"]
DB_PORT = st.secrets["postgres"]["port"]
DB_NAME = st.secrets["postgres"]["db"]
DB_USER = st.secrets["postgres"]["user"]
DB_PASSWORD = st.secrets["postgres"]["password"]
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

mongo_url = st.secrets.get("mongo", {}).get("url", "mongodb://localhost:27017")
mongo_db_name = st.secrets.get("mongo", {}).get("db", "Assignment4")
sqlite_path = st.secrets.get("sqlite", {}).get("path", "assignment3.db")

@st.cache_resource
def get_database_manager():
    postgres_engine = create_engine(DATABASE_URL)
    mongo_db = pymongo.MongoClient(mongo_url)[mongo_db_name]
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    return DatabaseManager(postgres_engine, mongo_db, sqlite_engine)

database_manager = get_database_manager()

pg_tables = database_manager.get_postgres_tables() or []
mongo_tables = database_manager.get_mongo_tables() or []
sqlite_tables = database_manager.get_sqlite_tables() or []
all_tables = list(set(pg_tables + mongo_tables + sqlite_tables))

selected_tables = st.multiselect("Choose table", all_tables)

def load_table_data(table):
    dataframes = []
    # PostgreSQL tables into dataframe list
    if table in pg_tables:
        cols = database_manager.get_postgres_columns(table)
        df_pg = database_manager.load_postgres_data(table, cols)
        dataframes.append(df_pg)
    # SQLite tables into dataframe list
    if table in sqlite_tables:
        cols = database_manager.get_sqlite_columns(table)
        df_sql = database_manager.load_sqlite_data(table, cols)
        dataframes.append(df_sql)
    # MongoDB tables into dataframe list
    if table in mongo_tables:
        cols = database_manager.get_mongo_columns(table)
        df_mongo = database_manager.load_mongo_data(table, cols)
        dataframes.append(df_mongo)
    # No dataframe found
    if not dataframes:
        return None
    # Concat dataframes
    return pd.concat(dataframes, ignore_index=True, sort=False)

# UI for merging tables into dataframe and session state
if st.button("Load and merge selected tables"):
    merged_dataframes = []
    # Append dataframes for merge
    for table in selected_tables:
        df = load_table_data(table)
        if df is not None and not df.empty:
            merged_dataframes.append(df)
    # Concat all chosen tables into one DataFrame
    if merged_dataframes:
        final_df = pd.concat(merged_dataframes, ignore_index=True, sort=False)
        st.dataframe(final_df, use_container_width=True)
        st.success("Tables merged successfully into session state.")
        st.session_state["merged_df"] = final_df
    else:
        st.info("No data found in the selected tables.")
