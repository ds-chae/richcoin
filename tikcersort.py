import pybithumb

all = pybithumb.get_current_price("ALL")

sort_all = sorted(all.items(), key = lambda x : float(x[1]['fluctate_rate_24H']), reverse=True)

count = 0

for ticker, data in sort_all :
    count+=1
    print(count, ticker, data['closing_price'], data['fluctate_rate_24H'])