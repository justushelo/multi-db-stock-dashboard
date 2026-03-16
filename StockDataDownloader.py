import pandas as pd
import yfinance as yf


class StockDataDownloader:
    """
    Download data from Yahoo Finance with choosen ticker on a monthly level.
    """

    def __init__(self, start="2020-01-01", end=None):
        """
        Initialize StockDataDownloader with start and end date.
        Parameters:
            start: Start date for download. Default value 2020-01-01.
            end: End date for download. Default value None to get up to date data.
        """
        self.start = start
        self.end = end

    def get_data(self, ticker: str):
        """
        Get monthly data for chosen ticker with given time period.
        Parameters:
            ticker (str): chosen ticker symbol
        Returns:
            pd.DataFrame: DataFrame containing the following columns:
                - date (datetime64[ns]): The date of the record (month end).
                - open (float): Opening price of the month.
                - high (float): Highest price of the month.
                - low (float): Lowest price of the month.
                - close (float): Closing price of the month.
                - adj close (float): Adjusted closing price (dividends/splits adjusted).
                - symbol (str): The ticker symbol of the stock.
        """
        data = yf.download(
            ticker,
            start=self.start,
            end=self.end,
            interval="1mo",
            progress=False,
            auto_adjust=False,
        )
        # Reset index
        data = data.reset_index()

        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Format columns
        data.columns = [col.lower().replace(" ", "_") for col in data.columns]
        data["symbol"] = ticker.upper()

        # Choose only wanted columns
        data = data[["date", "open", "high", "low", "close", "adj_close", "symbol"]]
        return data
