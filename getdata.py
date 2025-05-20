import yfinance as yf
from datetime import datetime, timedelta

def get_stock_data(ticker, start_date, end_date, pre_days=300):

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        extended_start_dt = start_dt - timedelta(days=pre_days)
        extended_start = extended_start_dt.strftime("%Y-%m-%d")

        extended_full_data = yf.download(ticker, start=extended_start, end=end_date)
        extended_full_data.columns = extended_full_data.columns.droplevel('Ticker')
        close_prices = extended_full_data.loc[start_date:end_date]['Close'].squeeze()
        extended_prices = extended_full_data.loc[extended_start:end_date]['Close'].squeeze()
        volume = extended_full_data.loc[start_date:end_date]['Volume'].squeeze()
        extended_volume = extended_full_data.loc[extended_start:end_date]['Volume'].squeeze()
        full_data = extended_full_data.loc[start_date:end_date]

        if full_data.empty:
            raise ValueError("未獲取到數據，請檢查股票代碼和日期範圍")

        return full_data, extended_full_data, close_prices, extended_prices, volume, extended_volume

    except Exception as e:
        print(f"數據獲取失敗: {str(e)}")

        return None, None, None, None, None, None

