# 股票模擬交易器 Stock Trading Simulator

股票模擬交易器是一款基於技術分析的股票交易模擬系統，幫助投資者和策略開發者從資料獲取、技術指標計算、訊號生成到績效回測，實現完整的交易閉環，從而驗證和優化您的量化交易策略。

## 核心功能

- 數據獲取
  使用 getdata.py 模組，通過 yfinance 獲取最新股票數據，確保交易策略基於實時市場狀況。

- 用股票數據計算技術指標的數據(indicator.py)，可使用的技術指標包括SMA, MACD, 布林帶, RSI, KDJ等投資者常用指標, 而且可以自定義參數

- 可以在trading_simulator.py自定義買賣策略，在generate_signals函數中的buy_condition可修改買入條件, sell_condition則是賣出條件, 模擬交易器不考慮做空, 只有在有持倉的情況下賣出信號才有效, 每次買賣均假設交易股數相同, 例如每次交易100股

- 生成indicator.csv和simulator_trades.csv文件, 用於查閱數據, indicator.csv包括用戶想分析的所有數據, simulator_trades.csv則是模擬交易記錄

- 最後提供買賣策略的績效分析, 列出模擬交易的平均收益率, 最大盈利, 最大虧損, 勝率

- 完整交易閉環：從資料取得→指標計算→訊號產生→交易配對→績效分析
