import sys
import json

from logger import *
from angelib import *
from tradelib import *

import gvarlist

# initialize bot for trading account
def initialize_bot():
    filename = 'instrument_list.json'
    try:
        with open(filename) as f:
            gvarlist.instrument_list = json.load(f)
    except FileNotFoundError:
        instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        response = urllib.request.urlopen(instrument_url)
        gvarlist.instrument_list = json.loads(response.read())
        with open(filename, "w") as f:
            f.write(json.dumps(gvarlist.instrument_list))
    except Exception as err:
        template = "An exception of type {0} occurred. error message:{1!r}"
        message = template.format(type(err).__name__, err.args)
        lg.error(message)

    lg.info('Trading Bot initialized')
def main():

    # initialize the logger (imported from logger)
    initialize_logger()

    # initialize bot
    initialize_bot()

    login()

    ticker = "GOLDPETAL24FEBFUT"
    obj = Trader(ticker)
    success = obj.run()

    logout()

    if not success:
        lg.info('Trading was not successful, locking asset')
    else:
        lg.info('Trading was successful!')

    lg.info('Trading Bot finished ... ')

if __name__ == '__main__':
    main()
