from ibapi.contract import Contract
from ibapi.order import Order

def create_stock_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    return contract

def create_market_order(action, quantity):
    order = Order()
    order.action = action  # "BUY" or "SELL"
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order

