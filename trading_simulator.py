import pandas as pd
import numpy as np
from collections import deque


def generate_signals(indicator_df):
    """
    輸入參數 indicator_df 為包含股價數據和技術指標的DataFrame
    在 buy_conition 和 sell_conition 自定義買賣策略
    最後函數返還 signals (DataFrame)
    """

    buy_condition = (
                        (indicator_df['RSI_14'] < 55 ) &
                        (indicator_df['MACD'] > 0) &
                        (indicator_df['Close'] > indicator_df['SMA_20'])


    )


    sell_condition = (
                        (indicator_df['RSI_7'] > 75)

    )


    # 標記信號（使用astype(int)轉換為01值）
    signals = pd.DataFrame({
        'Close': indicator_df['Close'],          # 保留收盤價
        'buy_signal': buy_condition.astype(int),
        'sell_signal': sell_condition.astype(int)
    }, index=indicator_df.index)

    return signals


def generate_trades(signals):
    """
    模擬交易假設每次買賣的股數相同, e.g 每次買入100股/賣出100股, 沒有持倉時的賣出信號無效
    """
    buys = signals[signals['buy_signal'] == 1].index.tolist()
    sells = signals[signals['sell_signal'] == 1].index.tolist()

    buys.sort()
    sells.sort()

    buy_queue = deque()
    trades = []
    sell_idx = 0  # 追蹤賣出信號的索引

    # 遍歷所有日期（嚴格按時間順序）
    for date in signals.index:
        # 處理買入信號：加入佇列
        if date in buys:
            buy_queue.append(date)

        # 處理賣出信號：配對最早未平倉買入
        if date in sells:
            # 只配對一個買入（避免重複使用賣出信號）
            if buy_queue and sell_idx < len(sells):
                # 找到第一個符合條件的買入（最早未平倉）
                while buy_queue and buy_queue[0] > date:
                    # 若買入晚於賣出，跳過此賣出信號
                    sell_idx += 1
                    break
                if buy_queue and buy_queue[0] < date:
                    buy_date = buy_queue.popleft()  # 先進先出
                    trades.append({
                        'buy_date': buy_date,
                        'buy_price': signals.loc[buy_date, 'Close'],
                        'sell_date': date,
                        'sell_price': signals.loc[date, 'Close']
                    })
                    sell_idx += 1

    # 處理未平倉買入
    for buy_date in buy_queue:
        trades.append({
            'buy_date': buy_date,
            'buy_price': signals.loc[buy_date, 'Close'],
            'sell_date': pd.NaT,
            'sell_price': np.nan
        })

    # 生成 DataFrame 並排序
    trades_df = pd.DataFrame(trades)
    trades_df.sort_values('buy_date', inplace=True)
    trades_df.set_index('buy_date', inplace=True)
    trades_df["profit_pct"] = (
            (trades_df["sell_price"] - trades_df["buy_price"]) /
            trades_df["buy_price"] * 100
    ).round(2)

    trades_df.to_csv("simulate_trades.csv")

    # 過濾未平倉交易 (移除 sell_date 為空值)
    closed_trades = trades_df.dropna(subset=["sell_date"]).copy()

    # 計算平均收益率 (保留兩位小數)
    average_buy = closed_trades["buy_price"].mean().round(2)
    average_sell = closed_trades["sell_price"].mean().round(2)
    average_profit = (average_sell - average_buy) / average_buy
    average_profit = (average_profit * 100).round(2)

    # 計算勝率 (盈利交易比例)
    winning_trades = (closed_trades["profit_pct"] > 0).sum()
    total_closed_trades = len(closed_trades)
    win_rate = (winning_trades / total_closed_trades * 100).round(2)
    max_profit =  closed_trades["profit_pct"].max().round(2)
    min_profit =  closed_trades["profit_pct"].min().round(2)

    print(f"有效交易次數: {total_closed_trades}")
    print(f"平均收益率: {average_profit}%")
    print(f"最大盈利/最小虧損: {max_profit}%")
    print(f"最大虧損/最小盈利: {min_profit}%")
    print(f"勝率: {win_rate}%")

    return trades_df

