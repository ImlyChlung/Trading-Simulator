import indicator
import trading_simulator as trade
import pandas as pd
from getdata import get_stock_data

ticker = 'AAPL'
start_date = "2020-1-1"
end_date = "2025-5-20"

full_data, extended_full_data, close_prices, extended_prices, volume, extended_volume = get_stock_data(ticker, start_date, end_date)

sma = indicator.SMA(close_prices, extended_prices, [5, 10, 20, 50, 100, 200])
rsi = indicator.RSI(close_prices, extended_prices, [7, 14])
pct_change = indicator.pct_change(close_prices)
macd = indicator.MACD(close_prices, extended_prices)
kdj = indicator.KDJ(extended_full_data, close_prices)
boll = indicator.BOLL(close_prices, extended_prices)

indicator_df = pd.concat([full_data, pct_change, sma, rsi, macd, kdj, boll], axis=1)
indicator_df = indicator_df.round(2)
indicator_df.to_csv('indicator.csv')


signals = trade.generate_signals(indicator_df)
trade.generate_trades(signals)



