
import pybithumb
import time
from datetime import datetime

all = pybithumb.get_current_price("ALL")
sort_all = sorted(all.items(), key = lambda x : float(x[1]['fluctate_rate_24H']), reverse=True)

cycle_time = 10 # 10 seconds delay
loop_time = 120 # repetition count
ascent = 0.5 # % rate

sec = 0
prev_ticker = ''
prev_rate = 0
prev_dict = { 'ticker' : 0 }

for ticker, data in sort_all :
    prev_dict[ticker] = data['fluctate_rate_24H']

while sec < loop_time :
    all = pybithumb.get_current_price("ALL")
    sort_all = sorted(all.items(), key = lambda x : float(x[1]['fluctate_rate_24H']), reverse=True)

    for ticker, data in sort_all :
        diff = float(data['fluctate_rate_24H']) - float(prev_dict[ticker])
        if diff >= ascent :
            print(datetime.now(), ticker, data['closing_price'], data['fluctate_rate_24H'], float(prev_dict[ticker]), '%.2f' % diff )

        prev_dict[ticker] = data['fluctate_rate_24H']

    time.sleep(cycle_time)
    sec += 1
