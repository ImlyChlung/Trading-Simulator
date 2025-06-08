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

def analyze_buy_signals(signals, window=20):
    """
    分析買入信號後的價格表現，新增HPR、年化收益率和最大回撤計算
    參數:
        signals: 包含買賣信號的 DataFrame，必須包含 'Close' 欄位和 'buy_signal' 欄位
        window: 分析窗口期 (交易日數)
    返回:
        包含完整分析結果的 DataFrame（僅包含有完整數據的交易）
    """
    # 獲取所有買入信號日期
    buy_signals = signals[signals['buy_signal'] == 1].index

    buy_report = []
    skipped_count = 0  # 記錄因數據不足而跳過的交易

    for buy_date in buy_signals:
        buy_price = signals.loc[buy_date, 'Close']

        # 獲取買入日期後的數據
        post_buy_data = signals.loc[buy_date:]

        # 檢查是否有足夠的數據（買入日+之後的window天）
        if len(post_buy_data) < window + 1:  # +1 是因為包括買入當天
            skipped_count += 1
            continue  # 數據不足，跳過此交易

        # 排除買入當天，從第二天開始計算
        post_buy_window = post_buy_data.iloc[1:window + 1]

        # 結束日價格
        end_price = post_buy_window['Close'].iloc[-1]  # 窗口結束日價格

        # 計算最大回撤 (MDD)
        rolling_max = post_buy_window['Close'].cummax()
        drawdowns = (rolling_max - post_buy_window['Close']) / rolling_max
        mdd = drawdowns.max()  # 最大回撤值

        # 計算持有期收益率 (HPR)
        hpr = (end_price - buy_price) / buy_price

        # 計算年化收益率 (假設252個交易日/年)
        holding_days = len(post_buy_window)
        annualized_return = (1 + hpr) ** (252 / holding_days) - 1

        buy_report.append({
            'buy_date': buy_date,
            'buy_price': buy_price,
            'end_price': end_price,
            'HPR': round(hpr * 100, 2),  # 轉換為百分比
            'Annualized_Return': round(annualized_return * 100, 2),
            'MDD': round(mdd * 100, 2)  # 轉換為百分比
        })

    # 創建結果DataFrame
    buy_report_df = pd.DataFrame(buy_report)

    # 保存結果到CSV（如果沒有交易則不保存）
    if not buy_report_df.empty:
        buy_report_df.to_csv("buy_report.csv", index=False)

    # 打印統計摘要
    buy_count = len(buy_report_df)

    if buy_count == 0:
        print(f"\n模擬買入後持有{window}日績效分析:")
        print("=" * 50)
        print(f"總買入信號: {len(buy_signals)}")
        print(f"因數據不足跳過: {skipped_count}次")
        print("警告: 沒有足夠數據的完整交易可分析!")
        return None

    positive_hpr = (buy_report_df['HPR'] > 0).sum()
    positive_annualized = (buy_report_df['Annualized_Return'] > 0).sum()
    mdd_over_5 = (buy_report_df['MDD'] > 5).sum()

    print(f"\n模擬買入後持有{window}日績效分析:")
    print("=" * 50)
    print(f"總買入信號: {len(buy_signals)}")
    print(f"完整交易數: {buy_count}")
    print(f"因數據不足跳過: {skipped_count}次")
    print(f"正收益比例(HPR > 0): {positive_hpr}次 ({positive_hpr / buy_count:.1%})")
    print(f"年化收益為正比例: {positive_annualized}次 ({positive_annualized / buy_count:.1%})")
    print(f"最大回撤>5%的比例: {mdd_over_5}次 ({mdd_over_5 / buy_count:.1%})")

    # 績效統計（全面風險效益評估）
    total_trades = len(buy_report_df)

    # 1. 基礎勝率統計
    win_trades = buy_report_df[buy_report_df['HPR'] > 0]
    loss_trades = buy_report_df[buy_report_df['HPR'] <= 0]

    win_count = len(win_trades)
    loss_count = len(loss_trades)
    win_rate = win_count / total_trades

    # 2. 完整收益率統計（包含虧損）
    avg_hpr_all = buy_report_df['HPR'].mean()  # 所有交易平均HPR
    avg_hpr_win = win_trades['HPR'].mean() if win_count > 0 else 0
    avg_hpr_loss = loss_trades['HPR'].mean() if loss_count > 0 else 0

    # 3. 風險指標
    max_single_loss = buy_report_df['HPR'].min()  # 單次最大虧損
    avg_mdd = buy_report_df['MDD'].mean()  # 平均最大回撤
    max_mdd = buy_report_df['MDD'].max()  # 最大回撤值

    # 4. 風險報酬比
    if loss_count > 0 and avg_hpr_loss < 0:  # 確保有虧損交易且平均虧損為負
        risk_reward_ratio = abs(avg_hpr_win / avg_hpr_loss)  # 盈虧比
    else:
        risk_reward_ratio = float('inf')

    # 5. 年化收益統計
    annualized_all = buy_report_df['Annualized_Return'].mean()
    annualized_win = win_trades['Annualized_Return'].mean() if win_count > 0 else 0
    annualized_loss = loss_trades['Annualized_Return'].mean() if loss_count > 0 else 0

    # 輸出全面績效報告
    print("\n收益率分析:")
    print(f"平均HPR(所有交易): {avg_hpr_all:.2f}%")
    print(f"平均HPR(獲利交易): {avg_hpr_win:.2f}%")
    print(f"平均HPR(虧損交易): {avg_hpr_loss:.2f}%")
    print(f"單次最大虧損: {max_single_loss:.2f}%")
    print("\n風險分析:")
    print(f"平均最大回檔(MDD): {avg_mdd:.2f}%")
    print(f"單次最大回檔: {max_mdd:.2f}%")
    print("\n年化表現:")
    print(f"平均年化收益(所有): {annualized_all:.2f}%")
    print(f"平均年化收益(利潤): {annualized_win:.2f}%")
    print(f"平均年化收益(虧損): {annualized_loss:.2f}%")
    print(f"風險報酬比: {risk_reward_ratio:.2f}:1")

    # 計算預期收益
    expectancy = (win_rate * avg_hpr_win) + ((1 - win_rate) * avg_hpr_loss)
    print(f"\n策略預期收益率: {expectancy:.2f}%")

    return buy_report_df
