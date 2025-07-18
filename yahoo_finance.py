from typing import Dict, Any

import yfinance as yf


def get_price(symbol: str) -> float:
    """
    Get the current market price for a given stock symbol using Yahoo Finance.
    If market is closed, returns the last available price.

    Args:
        symbol (str): The stock symbol to look up

    Returns:
        float: The current market price for the stock
    """
    ticker = yf.Ticker(symbol)

    # Get real-time price information
    current_data: Dict[str, Any] = ticker.info
    price = current_data.get('regularMarketPrice', 0.0)

    if price == 0.0:  # Fallback to last closing price if real-time price is not available
        data = ticker.history(period="1d")
        price = data['Close'].iloc[-1]

    return price
