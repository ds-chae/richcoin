import pybithumb

tickers = pybithumb.get_tickers()

count = 0

for ticker in tickers:
    count+=1
    price = pybithumb.get_current_price(ticker)
    print(count, ticker, price)