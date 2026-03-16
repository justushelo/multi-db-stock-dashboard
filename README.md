# Stock Dashboard

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-FF4B4B)

A multi-database CRUD Streamlit dashboard that connects simultaneously to PostgreSQL, MongoDB, and SQLite to manage and display stock market data (via `yfinance`).

## Quickstart (Docker Recommended)

The easiest way to run the full stack (PostgreSQL + MongoDB + App) is using Docker.

1. Create a secrets file from the template:
   ```bash
   cp .streamlit/secrets.example.toml .streamlit/secrets.toml
   ```
2. Run the services:
   ```bash
   docker-compose up --build
   ```
3. Access the dashboard at [http://localhost:8501](http://localhost:8501)

## Local Development Setup

1. Install [uv](https://astral.sh/uv/) and the project dependencies:
   ```bash
   uv sync
   ```
2. Provide your database credentials in `.streamlit/secrets.toml` (copy from `.streamlit/secrets.example.toml`).
3. Make sure your PostgreSQL and MongoDB instances are running.
4. Start the application:
   ```bash
   uv run streamlit run main.py
   ```

*Note: On your first run, the databases will be empty. Use the "Edit Data" page to fetch the initial stock records from Yahoo Finance.*

## Project Structure

- `main.py`: Main dashboard displaying merged data.
- `pages/`: Additional Streamlit pages (e.g., Data editing/CRUD operations).
- `library.py`: Database management across SQL & NoSQL.
- `StockDataDownloader.py`: Integration with Yahoo Finance.
