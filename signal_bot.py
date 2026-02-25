import yfinance as yf
import pandas as pd
import ta
import requests

# ==============================
# CONFIG
# ==============================

BOT_TOKEN = "8357827042:AAFGb-06v2etedyRky3kg-kYYmqkq1QEzsY"
CHAT_ID = "7225721600"

capital_inr = 10000
risk_percent = 0.75
risk_inr = capital_inr * (risk_percent / 100)

symbols = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD"
}

don_length = 20
ema_length = 100
atr_length = 14
atr_multiplier = 2.0

# ==============================
# TELEGRAM FUNCTION
# ==============================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# ==============================
# SIGNAL LOGIC
# ==============================

def check_symbol(name, ticker):

    data = yf.download(ticker, interval="4h", period="120d")

    # Fix multi-index issue from yfinance
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna()

    # Indicators
    data["EMA"] = ta.trend.ema_indicator(data["Close"], window=ema_length)
    data["ATR"] = ta.volatility.average_true_range(
        data["High"], data["Low"], data["Close"], window=atr_length
    )

    data["DonHigh"] = data["High"].rolling(don_length).max()
    data["DonLow"] = data["Low"].rolling(don_length).min()

    data = data.dropna()

    last = data.iloc[-1]
    prev = data.iloc[-2]

    close = float(last["Close"])
    ema = float(last["EMA"])
    atr = float(last["ATR"])

    don_high = float(prev["DonHigh"])
    don_low = float(prev["DonLow"])

    stop_distance = atr * atr_multiplier
    position_size = risk_inr / stop_distance

    # LONG CONDITION
    if close > don_high and close > ema:
        entry = close
        stop = entry - stop_distance
        tp = entry + (2 * stop_distance)

        return f"""
🚀 {name} LONG SIGNAL (4H)

Entry: {round(entry,2)}
Stop: {round(stop,2)}
TP1 (2R): {round(tp,2)}

Risk: ₹{risk_inr}
Position Size (USDT): {round(position_size,3)}
"""

    # SHORT CONDITION
    elif close < don_low and close < ema:
        entry = close
        stop = entry + stop_distance
        tp = entry - (2 * stop_distance)

        return f"""
🔻 {name} SHORT SIGNAL (4H)

Entry: {round(entry,2)}
Stop: {round(stop,2)}
TP1 (2R): {round(tp,2)}

Risk: ₹{risk_inr}
Position Size (USDT): {round(position_size,3)}
"""

    return None

# ==============================
# RUN CHECK
# ==============================

all_messages = []

for name, ticker in symbols.items():
    signal = check_symbol(name, ticker)
    if signal:
        all_messages.append(signal)

if all_messages:
    final_message = "\n".join(all_messages)
    send_telegram(final_message)
    print("Signals sent to Telegram.")
else:
    print("No signals at this time.")