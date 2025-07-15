import json

from ibapi.client import *
from ibapi.wrapper import *
import time
import threading

from models.dollar import Dollar, DollarEncoder
from orders import create_stock_contract, create_market_order
import yfinance as yf


def get_price(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    price = data['Close'].iloc[-1]
    print(f"{symbol} price: {price}")
    return price


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.positions = []
        self.positions_map = {}  # symbol: (quantity, market_value)
        self.prices = {}         # symbol: price
        self.orders = []


    def nextValidId(self, orderId):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def currentTime(self, time):
        print(time)

    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderReject}")

    def position(self, account, contract, position, avgCost):
        symbol = contract.symbol
        print(f"Account: {account}, Symbol: {symbol}, Position: {position}, AvgCost: {avgCost}")
        self.positions.append((account, symbol, position, avgCost))
        self.positions_map[symbol] = (int(position), Dollar(get_price(symbol) * int(position)))
        # self.reqMktData(1000 + hash(symbol) % 8999, contract, "", False, False, [])

    def positionEnd(self):
        print("All positions received.")
        total_market_value = sum(value[1].value for value in self.positions_map.values())
        print("Total Market Value:", Dollar(total_market_value))
        for symbol, (qty, market_value) in self.positions_map.items():
            self.positions_map[symbol] = (qty, market_value, market_value/total_market_value*100)
        print(json.dumps(self.positions_map, indent=4, cls=DollarEncoder))

    def get_my_positions(self):
        self.reqPositions()

    def get_current_price(self, symbol):
        contract = create_stock_contract(symbol)
        # self.reqMktData(1, contract, "", False, False, [])

    def tickPrice(self, reqId, tickType, price, attrib):
        # Only use tickType==4 (Last Price) or tickType==1 (Bid Price) as needed
        if tickType == 4 or tickType == 1:
            for symbol in self.positions_map:
                if reqId == 1000 + hash(symbol) % 8999:
                    self.prices[symbol] = price
                    qty = self.positions_map[symbol][0]
                    market_value = qty * price
                    self.positions_map[symbol] = (qty, market_value)
                    print(f"Symbol: {symbol}, Qty: {qty}, Price: {price}, Market Value: {market_value}")

    def rebalance_portfolio(self, desired_alloc):
        for symbol in current_alloc:
            qty, market_value, curr_pct = current_alloc[symbol]
        _, _, desired_pct = desired_alloc[symbol]
        desired_value = total_value * (desired_pct / 100)
        diff_value = desired_value - market_value
        price_per_share = market_value / qty if qty else 0
        shares_to_trade = int(diff_value / price_per_share)
        if shares_to_trade > 0:
            self.orders.append((symbol, "BUY", shares_to_trade))
        elif shares_to_trade < 0:
            self.orders.append((symbol, "SELL", abs(shares_to_trade)))

app = TestApp()
app.connect("127.0.0.1", 7496, 0)
threading.Thread(target=app.run).start()
time.sleep(1)

# for i in range(0,5):
#   print(app.nextId())
app.reqCurrentTime()
app.get_my_positions()
# Usage in your app:
# contract = create_stock_contract("SY")
# order = create_market_order("BUY", 10)
# app.placeOrder(app.nextId(), contract, order)
