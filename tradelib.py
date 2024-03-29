from logger import *
import time
from angelib import *

# global variables here
import gvarlist

class Trader():
    def __init__(self, ticker):
        self.ticker = ticker
        self.trend = "NA"
        self.buy_sell = None
        self.entryPrice = 0.0
        self.takeProfit = 0.0
        self.stopLoss = 0.0
        self.sharesQty = 0

        lg.info('Trade is initialized with ticker %s ...!!' % (self.ticker))

        self.file = self.ticker + ".txt"
        try:
            with open(self.file) as f:
                data = f.readlines()
                self.trend = data[0].strip('\n')
                self.sharesQty = int(data[1])
                self.takeProfit = float(data[2])
                self.stopLoss = float(data[3])

                lg.debug('trend for %s : %s' % (self.ticker, self.trend))
                lg.debug('sharesQty for %s : %s' % (self.ticker, self.sharesQty))
                lg.debug('takeProfit for %s : %s' % (self.ticker, self.takeProfit))
                lg.debug('stopLoss for %s : %s' % (self.ticker, self.stopLoss))
        except FileNotFoundError:
            self.init_trade()
        except Exception as err:
            template = "An exception of type {0} occurred. error message:{1!r}"
            message = template.format(type(err).__name__, err.args)
            lg.error(message)

    def init_trade(self):
        stock_data = hist_data(self.ticker, "MCX")
        high_price = max(stock_data.iloc[-2]['high'], stock_data.iloc[-3]['high'])
        # self.high_price = 199 # For Test
        self.high_price = high_price
        lg.debug('high_price for %s = %f ' % (self.ticker, self.high_price))
        low_price = min(stock_data.iloc[-2]['low'], stock_data.iloc[-3]['low'])
        # self.low_price = 101 # For Test
        self.low_price = low_price
        lg.debug('low_price for %s = %f ' % (self.ticker, self.low_price))

        while True:
            lg.info('Running trade for %s ... !' % (self.ticker))

            cur_time = dt.datetime.now(pytz.timezone("Asia/Kolkata")).time()

            if(cur_time < gvarlist.startTime or cur_time > gvarlist.endTime):
                lg.info('Market is closed. \n')
                logout()
                sys.exit()
                # break

            cur_price = get_current_price(self.ticker)
            lg.info('Current price for %s is %f' % (self.ticker, cur_price))

            if (cur_price > self.high_price):
                lg.info('LONG trend confirmed for %s \n' % self.ticker)
                self.trend = 'LONG'
                self.buy_sell = 'BUY'
                break
            elif (cur_price < self.low_price):
                lg.info('SHORT trend confirmed for %s \n' % self.ticker)
                self.trend = 'SHORT'
                self.buy_sell = 'SELL'
                break
            else:
                lg.info('Trend is NOT confirmed for %s !!!\n' % (self.ticker))
        
        self.set_takeprofit(cur_price)
        self.set_stoploss(cur_price)

        # decide the total amount to invest
        self.sharesQty = get_shares_amount(cur_price)
        orderID = submit_order(self.ticker, self.sharesQty, self.buy_sell)

        success = False
        count = 0
        while (get_oder_status(orderID) == 'open'):
            lg.info('%s: order in open for %s, waiting ... %d ' % (self.buy_sell, self.ticker, count))
            count = count + 1
        
        status = get_oder_status(orderID)
        lg.info('%s Order status for %s : %s ' % (self.buy_sell, self.ticker, status))
        if(status == 'completed'):
            success = True

        if(success):
            with open(self.file, "w") as f:
                f.write(self.trend)
                f.write("\n")
                f.write(str(self.sharesQty))
                f.write("\n")
                f.write(str(self.takeProfit))
                f.write("\n")
                f.write(str(self.stopLoss))
                f.write("\n")
                f.flush()
                f.close()
        else:
            lg.error('%s Order Not success for %s, Exit the trade, (status = %s)' % (self.buy_sell, self.ticker, status))
            logout()
            sys.exit()

    def run(self):
        while True:
            # time.sleep(1)
            lg.info('2: Running trade for %s ... !' % (self.ticker))

            cur_time = dt.datetime.now(pytz.timezone("Asia/Kolkata")).time()
            if(cur_time < gvarlist.startTime or cur_time > gvarlist.endTime):
                lg.info('Market is closed. ')
                logout()
                sys.exit()

            cur_price = get_current_price(self.ticker)
            lg.info('Current price for %s is %f ' % (self.ticker, cur_price))

            if(self.trend == 'LONG'):
                if(self.takeProfit < cur_price):
                    self.trail_SL(cur_price)

                if(self.stopLoss > cur_price):
                    self.trend = 'NA'
                    self.buy_sell = 'SELL'
                    break

            elif(self.trend == 'SHORT'):
                if(self.takeProfit > cur_price):
                    self.trail_SL(cur_price)

                if(self.stopLoss < cur_price):
                    self.trend = 'NA'
                    self.buy_sell = 'BUY'
                    break
            
            else:
                lg.error("Trend is Not Valid")
                raise ValueError

            lg.debug('trend for %s : %s' % (self.ticker, self.trend))
            lg.debug('sharesQty for %s : %s' % (self.ticker, self.sharesQty))
            lg.debug('takeProfit for %s : %s' % (self.ticker, self.takeProfit))
            lg.debug('stopLoss for %s : %s' % (self.ticker, self.stopLoss))

        orderID = submit_order(self.ticker, self.sharesQty, self.buy_sell)

        success = False
        count = 0

        while (get_oder_status(orderID) == 'open'):
            lg.info('%s: order in open for %s, waiting ... %d ' % (self.buy_sell, self.ticker, count))
            count = count + 1
            
        status = get_oder_status(orderID)  
        lg.info('%s Order status for %s : %s ' % (self.buy_sell, self.ticker, status))
        if(status == 'completed'):
            success = True

        if os.path.isfile(self.file):
            os.remove(self.file)
        else:
            lg.error("Error: %s file not found" % self.file)
            success = False
        return success

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
        
    def trail_SL(self, cur_price):
        if(self.trend == 'LONG'):
            temp = self.takeProfit - self.stopLoss
            self.takeProfit = self.takeProfit + temp / 1.5
            self.stopLoss = self.stopLoss + temp / 1.5
        elif(self.trend == 'SHORT'):
            temp = self.stopLoss - self.takeProfit
            self.takeProfit = self.takeProfit - temp / 1.5
            self.stopLoss = self.stopLoss - temp / 1.5
        else:
            lg.error("Trend is Not Valid")
            raise ValueError
    