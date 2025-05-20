import indicator
import trading_simulator as trade
import pandas as pd
from getdata import get_stock_data

"""
可否幫我為股價數據進行詳細的技術分析, 包括 1.多空力量對比, 2. 趨勢強度量化分數（每一個評分項0-10分）, 
然後預測之後最有可能的股價走勢, 推測可能的支持和壓力位, 然後判斷現時最佳的策略,如果你建議了多個策略, 
為你提出的策略排列優先度, 建議越具體越好 
"""

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



