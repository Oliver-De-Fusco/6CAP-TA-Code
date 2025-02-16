import yfinance as yf

START = "2023-01-01"
END = "2025-01-01"
TICKER = "^GSPC"

data = yf.download(TICKER, start=START, end=END,multi_level_index=False)


data.to_csv("data.csv")

print(f"{TICKER} saved. {round(data.memory_usage(index=True).sum() * 1e-6,4)}mb")