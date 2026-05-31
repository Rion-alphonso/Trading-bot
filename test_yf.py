import yfinance as yf
print("Testing yfinance for 5m history...")
data = yf.download("GC=F", interval="5m", period="max")
print(f"yfinance 5m data rows: {len(data)}")
if len(data) > 0:
    print(f"Oldest: {data.index[0]}")
