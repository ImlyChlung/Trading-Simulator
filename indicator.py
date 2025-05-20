import pandas as pd
import numpy as np

#pct change 漲跌百分點
def pct_change(close_prices):
    pct_change = close_prices.pct_change()*100
    pct_change = pct_change.bfill()
    return pct_change.to_frame(name='Pct_Change')

#SMA 簡單移動平均線
def SMA(close_prices, extended_price, window_list):
    SMA = pd.DataFrame(index=close_prices.index)
    for window in window_list:
        SMA[f'SMA_{window}'] = extended_price.rolling(window).mean()
    return SMA.dropna()

#RSI 相對強弱指標
def RSI(close_prices, extended_prices, window_list):
    RSI = pd.DataFrame(index=extended_prices.index)
    for window in window_list:
        delta = extended_prices.diff(1).bfill()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # EMA計算（注意alpha需為單一數值）
        avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()

        # 計算RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # 將結果存入特徵DataFrame
        RSI[f'RSI_{window}'] = rsi
    return RSI.loc[close_prices.index[0]:close_prices.index[-1]].dropna()

#MACD
def MACD(close_prices, extended_prices, fast_period=12, slow_period=26, signal_period=9):
    # 計算短期與長期 EMA
    ema_fast = extended_prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = extended_prices.ewm(span=slow_period, adjust=False).mean()

    # DIF 為兩條 EMA 的差距
    DIF = ema_fast - ema_slow

    # DEA 為 DIF 的 signal_period 日 EMA (訊號線)
    DEA = DIF.ewm(span=signal_period, adjust=False).mean()

    # MACD: 2 * (DIF - DEA)
    MACD_val = 2 * (DIF - DEA)

    # 建立結果 DataFrame，保持原 Series 的日期索引
    MACD = pd.DataFrame({
        'MACD': MACD_val,
        'DIF': DIF,
        'DEA': DEA,
    }, index=extended_prices.index)

    MACD = MACD.loc[close_prices.index[0]:close_prices.index[-1]]

    return MACD

#KDJ
def KDJ(extended_full_data, close_prices, n=9, m=3):
    high = extended_full_data['High']
    low = extended_full_data['Low']
    close = extended_full_data['Close']

    min_low = low.rolling(n).min()
    max_high = high.rolling(n).max()

    rsv = (close - min_low) / (max_high - min_low) * 100
    rsv = rsv.fillna(0)
    rsv.replace([np.inf, -np.inf], 100, inplace=True)

    # 初始化 K 和 D 為 NaN
    K = pd.Series(np.nan, index=extended_full_data.index)
    D = pd.Series(np.nan, index=extended_full_data.index)

    alpha = 1 / m
    k_prev, d_prev = 50.0, 50.0

    for i in range(len(rsv)):
        current_rsv = rsv.iloc[i]  # 使用 .iloc 獲取值

        if pd.isna(current_rsv):
            K.iloc[i] = np.nan  # 使用 .iloc 設置值
            D.iloc[i] = np.nan
        else:
            k = (1-alpha) * k_prev + alpha * current_rsv
            d = (1-alpha) * d_prev + alpha * k

            K.iloc[i] = k  # 使用 .iloc 設置值
            D.iloc[i] = d

            k_prev, d_prev = k, d

    J = 3 * K - 2 * D

    KDJ = pd.DataFrame({
        'K': K,
        'D': D,
        'J': J
    }, index=extended_full_data.index)

    KDJ = KDJ.loc[close_prices.index[0]:close_prices.index[-1]]

    return KDJ

#BOLL
def BOLL(close_prices, extended_prices, window=20, k=2):
    """
    計算布林通道
    :param close_series: 收盤價序列 (pd.Series)
    :param window: 移動平均窗口 (默認20日)
    :param k: 標準差倍數 (默認2)
    :return: DataFrame，包含中軌、上軌、下軌
    """
    # 計算中軌（20日SMA）
    middle_band = extended_prices.rolling(window=window).mean()

    # 計算標準差
    std = extended_prices.rolling(window=window).std(ddof=0)  # ddof=0 表示總體標準差

    # 計算上軌和下軌
    upper_band = middle_band + k * std
    lower_band = middle_band - k * std

    # 構建DataFrame
    BOLL = pd.DataFrame({
        'BOLL_Middle': middle_band,
        'BOLL_Upper': upper_band,
        'BOLL_Lower': lower_band
    }, index=extended_prices.index)

    BOLL = BOLL.loc[close_prices.index[0]:close_prices.index[-1]]

    return BOLL

