import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv("data.csv")

#        [Date, Buy, Balance, Position]
equity = [(data.index[0],1,10_000,1)]

def sma(data, t):
    return data.shift(1).rolling(t).mean()

Fast = 20
Slow = 50
Long = 200
data["SMA_fast"] = sma(data["Close"],Fast)
data["SMA_slow"] = sma(data["Close"],Slow)
data["SMA_long"] = sma(data["Close"],Long)

data["bull"] = data["SMA_fast"] > data["SMA_slow"]

for x in range(2,len(data)):

    current = data[:x]
    buy = 0
    position = equity[-1][3]
    balance = equity[-1][2]
    
    if current["bull"].iloc[-1] and (not current["bull"].iloc[-2]) and current["Open"].iloc[-1] > current["SMA_long"].iloc[-1]: # Buy
        buy = 1
        position = balance // current["Open"].iloc[-1]
        # position = 1
        balance -= current["Open"].iloc[-1] * position

    if not current["bull"].iloc[-1] and current["bull"].iloc[-2]: # Sell
        buy = -1
        balance += current["Open"].iloc[-1] * position
        position = 0

    equity.append((current.index[-1], buy, balance, position))

equity = pd.DataFrame(equity,columns=["Date","buy","balance","position"])

equity = equity.set_index("Date")

data = data.join(equity)

print(equity)

data["value"] = (data["position"] * data["Close"]) + data["balance"]

data["log_return"] = np.log((data["Close"] / data["Close"].shift(1)))
data["value_log_return"] = np.log((data["value"] / data["value"].shift(1)))

data["value_log_return"]

data[["log_return","value_log_return"]].cumsum().plot()

plt.show()

