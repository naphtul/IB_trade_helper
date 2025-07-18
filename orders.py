from ibapi.contract import Contract
from ibapi.order import Order


def create_stock_contract(symbol: str) -> Contract:
    """
    Creates an Interactive Brokers contract object for a stock.

    Args:
        symbol (str): The stock symbol/ticker

    Returns:
        Contract: An IB contract object configured for US stock trading
    """
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    return contract


def create_market_order(action: str, quantity: int) -> Order:
    """
    Creates an Interactive Brokers market order.

    Args:
        action (str): The order action ("BUY" or "SELL")
        quantity (int): The number of shares to buy or sell

    Returns:
        Order: An IB order object configured as a market order
    """
    order = Order()
    order.action = action  # "BUY" or "SELL"
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order
