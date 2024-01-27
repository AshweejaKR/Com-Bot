import urllib
from SmartApi import SmartConnect
from pyotp import TOTP
import time
import pandas as pd
import datetime as dt

from logger import *

# global variables here
import gvarlist

def login():
    try:
        key_secret = open("key.txt", "r").read().split()
        gvarlist.client_id = key_secret[2]

        gvarlist.api = SmartConnect(api_key = key_secret[0])
        data = gvarlist.api.generateSession(gvarlist.client_id, key_secret[3], TOTP(key_secret[4]).now())
        lg.debug('data: %s ' % data)
        if(data['status'] and data['message'] == 'SUCCESS'):
            lg.info('Login success ... !')
        else:
            lg.error('Login failed ... !')
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)
        logout()
        sys.exit()

def logout():
    try:
        data = gvarlist.api.terminateSession(gvarlist.client_id)
        lg.debug('logout: %s ' % data)
        if(data['status'] and data['message'] == 'SUCCESS'):
            lg.info('Logout success ... !')
        else:
            lg.error('Logout failed ... !')
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)
        lg.error('Logout failed ... !')

def token_lookup(ticker, exchange = "MCX"):
    try:
        for instrument in gvarlist.instrument_list:
            if instrument["symbol"] == ticker and instrument["exch_seg"] == exchange:
                return instrument["token"]
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)

def symbol_lookup(token, exchange = "MCX"):
    for instrument in gvarlist.instrument_list:
        if instrument["token"] == token and instrument["exch_seg"] == exchange:
            return instrument["symbol"][:-3]

def submit_order(ticker, sharesQty, buy_sell, exchange = 'MCX'):
    lg.info('Submitting %s Order for %s, Qty = %d ' % (buy_sell, ticker, sharesQty))
    orderID = None

    try:
        price = get_current_price(ticker)
        params = {
                    "variety" : "NORMAL",
                    "tradingsymbol" : "{}".format(ticker),
                    "symboltoken" : token_lookup(ticker),
                    "transactiontype" : buy_sell,
                    "exchange" : exchange,
                    "ordertype" : "MARKET",
                    "producttype" : "CARRYFORWARD",
                    "duration" : "DAY",
                    "quantity" : sharesQty
                    }
        
        lg.info('params: %s ' % params)
        orderID = gvarlist.api.placeOrder(params)
        lg.info('orderID: %s ' % orderID)
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)
        lg.error('%s order NOT submitted!' % buy_sell)
        logout()
        sys.exit()
    return orderID
    
def get_oder_status(orderID):
    status = 'NA'
    # For Test
    # return 'completed'
    # End test
    
    time.sleep(2)
    order_history_response = gvarlist.api.orderBook()  
    try:
        for i in order_history_response['data']:
            if(i['orderid'] == orderID):
                print(i)
                status = i['status'] # completed/rejected/open/cancelled
                break
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)
        
    return status

def hist_data(ticker, exchange = "MCX"):
    interval = 'ONE_DAY'
    duration = 10
    token = token_lookup(ticker, exchange)
    if token is None:
        lg.error("Not a VALID ticker")
        df_data = pd.DataFrame(columns = ["date", "open", "high", "low", "close", "volume"])
        return df_data
    params = {
             "exchange" : exchange,
             "symboltoken" : token,
             "interval" : interval,
             "fromdate" : (dt.date.today() - dt.timedelta(duration)).strftime('%Y-%m-%d %H:%M'),
             "todate" : dt.date.today().strftime('%Y-%m-%d %H:%M')  
             }
    data = gvarlist.api.getCandleData(params)

    df_data = pd.DataFrame(data["data"],
                           columns = ["date", "open", "high", "low", "close", "volume"])
    df_data.set_index("date", inplace = True)
    df_data.index = pd.to_datetime(df_data.index)
    df_data.index = df_data.index.tz_localize(None)
    return df_data

def get_current_price(ticker, exchange = 'MCX'):
    # For Test
    # ltp = float(input("Enter LTP\n"))
    # return ltp
    # End test
    try:
        data = gvarlist.api.ltpData(exchange = exchange, tradingsymbol = ticker, symboltoken = token_lookup(ticker))
        if(data['status'] and (data['message'] == 'SUCCESS')):
            ltp = float(data['data']['ltp'])
        else:
            template = "An ERROR occurred. error message : {0!r}"
            message = template.format(data['message'])
            lg.error(message)
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)
    return ltp

def get_shares_amount(cur_price):
    return 1
