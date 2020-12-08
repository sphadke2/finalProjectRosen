from math import log, exp
from statistics import mean, stdev, median
import random
f = open('AAPL.csv','r')

def monteCarloStockPrices(f):
    closing_prices = []
    
    for line in f.readlines():
        line = line.strip()
        closing_prices.append(line)
    
    del closing_prices[0]
    for j in range(len(closing_prices)):
        closing_prices[j] = float(closing_prices[j])
    f.close()
    diff_daily = []
    for j in range(1,len(closing_prices)):
        diff_daily.append(log(closing_prices[j])-log(closing_prices[j-1]))
    
    avg_daily_return = mean(diff_daily)
    std_daily_return = stdev(diff_daily)
    
    
    
    final_daily_close = closing_prices[-1]
    
    predictions = [final_daily_close]
    print(final_daily_close)
    closing_price = []
    for c in range(10000):
        final_daily_close = 122.925003
        for d in range(0,250):
            final_daily_close *=  exp(random.gauss(avg_daily_return,std_daily_return))
            predictions.append(final_daily_close)
        closing_price.append(predictions[-1])
    return closing_price

def genCallPriceBuy(closing_price):

    CallStrikes = [75,100,125,150,175,200,250,300]
   
    CallPriceStorage = []
    for strike in CallStrikes:
    
        option_contract_values = closing_price.copy()
    
        option_contract_values[:] = [max(price-strike,0) for price in closing_price]
    
        CallPriceStorage.append(mean(option_contract_values))
    
    
    
    
    CallPricesBuy = dict(zip(CallStrikes,CallPriceStorage))
    
    return CallPricesBuy

def genSellOptionPrice(closing_price):
    CallStrikes = [75,100,125,150,175,200,250,300]
    
    sellCallPriceStorage = []
    for element in CallStrikes:
        final_stock_price = random.choice(closing_price)
        final_option_value = max(final_stock_price - element,0)
        sellCallPriceStorage.append(final_option_value)
    CallPricesSell = dict(zip(CallStrikes,sellCallPriceStorage))
    return CallPricesSell
    
def main():

    closing_price = monteCarloStockPrices(f)
    
    print(genCallPriceBuy(closing_price))
    
    print(genSellOptionPrice(closing_price))

main()