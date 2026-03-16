# Imports
import pandas as pd
import plotly.express as px
import streamlit as st

# Overview and visualization of data
st.set_page_config(page_title="Overview", layout="wide")
st.title("Market Overview")

# Get session state data
if "merged_df" not in st.session_state:
    st.warning("No downloaded tables. Choose tables from main page")
    st.stop()

# Get DataFrame from session state
df = st.session_state["merged_df"]

# Check required columns
required_columns = ["symbol", "date"]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    st.warning(f"Data is missing required columns: {', '.join(missing_cols)}")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
tickers = df["symbol"].unique()
selected_tickers = st.sidebar.multiselect(
    "Select tickers", tickers, default=tickers[:3]
)

# Prepare "date" column and initialize min and max date
df["date"] = pd.to_datetime(df["date"], utc=True)
min_date = df["date"].min().date()
max_date = df["date"].max().date()

# Sidebar UI Inputs for dates
start_input = st.sidebar.date_input(
    "Start date", value=min_date, min_value=min_date, max_value=max_date
)
end_input = st.sidebar.date_input(
    "End date", value=max_date, min_value=min_date, max_value=max_date
)

# Handle potential tuple returns from st.date_input
if isinstance(start_input, tuple):
    start_input = start_input[0] if start_input else min_date
if start_input is None:
    start_input = min_date

if isinstance(end_input, tuple):
    end_input = end_input[0] if end_input else max_date
if end_input is None:
    end_input = max_date

start_date = pd.Timestamp(start_input, tz="UTC")
end_date = pd.Timestamp(end_input, tz="UTC")

# Filter data with given parameters
filtered_dataframe = df[
    (df["symbol"].isin(selected_tickers))
    & (df["date"] >= start_date)
    & (df["date"] <= end_date)
]
fig = px.line(
    filtered_dataframe,
    x="date",
    y="close",
    color="symbol",  # This automatically creates a legend with ticker symbols
    title="Stock Closing Prices",
    labels={"close": "Close Price", "date": "Date", "symbol": "Ticker Symbol"},
)

# Customize layout
fig.update_layout(
    legend_title_text="Ticker Symbol",
    template="plotly_white",
    hovermode="x unified",
    width=1000,
    height=500,
)

st.plotly_chart(fig, use_container_width=True)
