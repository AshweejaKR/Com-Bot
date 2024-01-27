from logger import *
import time
from angelib import *

# global variables here
import gvarlist

class Trader():
    def __init__(self, ticker):
        self.ticker = ticker
        self.trend = "NA"
        self.entryPrice = 0.0
        self.takeProfit = 0.0
        self.stopLoss = 0.0
        self.sharesQty = 0

        lg.info('Trade is initialized with ticker %s ...!!' % (self.ticker))

        file = self.ticker + ".txt"
        try:
            with open(file) as f:
                data = f.readlines()
                self.trend = data[0].strip('\n')
        except FileNotFoundError:
            self.init_trade()
        except Exception as err:
            template = "An exception of type {0} occurred. error message:{1!r}"
            message = template.format(type(err).__name__, err.args)
            lg.error(message)

    def init_trade(self):
        stock_data = hist_data(self.ticker, "MCX")
        high_price = max(stock_data.iloc[-2]['high'], stock_data.iloc[-3]['high'])
        self.high_price = high_price
        low_price = min(stock_data.iloc[-2]['low'], stock_data.iloc[-3]['low'])
        self.low_price = low_price

        while True:
            lg.info('Running trade for %s ... !' % (self.ticker))

            cur_time = dt.datetime.now(pytz.timezone("Asia/Kolkata")).time()

            if(cur_time < gvarlist.startTime or cur_time > gvarlist.endTime):
                lg.info('Market is closed. \n')
                sys.exit()
                # break

            cur_price = get_current_price(self.ticker)
            lg.info('Current price for %s is %f' % (self.ticker, cur_price))

            if (cur_price > self.high_price):
                lg.info('LONG trend confirmed for %s \n' % self.ticker)
                self.trend = 'LONG'
                break
            elif (cur_price < self.low_price):
                lg.info('SHORT trend confirmed for %s \n' % self.ticker)
                self.trend = 'SHORT'
                break
            else:
                lg.info('Trend is NOT confirmed for %s !!!\n' % (self.ticker))
        
        self.set_takeprofit(cur_price)
        self.set_stoploss(cur_price)

        # decide the total amount to invest
        self.sharesQty = get_shares_amount(cur_price)
        success = submit_order(self.ticker, self.sharesQty, "LONG")

        if(success):
            print("Add the position to list")
        else:
            print("Exit the trade")


    def run(self):
        while True:
            # time.sleep(1)
            lg.info('2: Running trade for %s ... !' % (self.ticker))

            cur_time = dt.datetime.now(pytz.timezone("Asia/Kolkata")).time()
            if(cur_time < gvarlist.startTime or cur_time > gvarlist.endTime):
                lg.info('Market is closed. ')
                sys.exit()

            cur_price = get_current_price(self.ticker)
            lg.info('Current price for %s is %f ' % (self.ticker, cur_price))

    def set_takeprofit(self, entryPrice):
        if self.trend == 'LONG':
            self.takeProfit = entryPrice + (entryPrice * gvarlist.takeProfitMargin)
            lg.info('Take profit set for LONG at %.2f' % self.takeProfit)
        elif self.trend == 'SHORT':
            self.takeProfit = entryPrice - (entryPrice * gvarlist.takeProfitMargin)
            lg.info('Take profit set for SHORT at %.2f' % self.takeProfit)
        else:
            lg.error("Trend is Not Valid")
            raise ValueError
        
    def set_stoploss(self, entryPrice):
        if self.trend == 'LONG':
            self.stopLoss = entryPrice - (entryPrice * gvarlist.stopLossMargin)
            lg.info('Stop loss set for LONG at %.2f' % self.stopLoss)
        elif self.trend == 'SHORT':
            self.stopLoss = entryPrice + (entryPrice * gvarlist.stopLossMargin)
            lg.info('Stop loss set for SHORT at %.2f' % self.stopLoss)
        else:
            lg.error("Trend is Not Valid")
            raise ValueError
        
    def trail_SL(self):
        pass
    