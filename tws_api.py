import threading
import time
from typing import Dict, List, Any, Optional, Callable, Tuple

from ibapi.client import *
from ibapi.wrapper import *

from yahoo_finance import get_price


class IBApp(EClient, EWrapper):
    """
    Interactive Brokers API application class that handles the connection to TWS/IB Gateway
    and implements the necessary callback methods for position and order management.

    This class combines EClient for sending requests and EWrapper for handling responses
    from the IB API.
    """

    def __init__(self):
        """
        Initialize the IBApp with necessary tracking variables for positions,
        orders, and market values.
        """
        EClient.__init__(self, self)
        self.orderId: Optional[int] = None
        self.positions_map: Dict[str, Tuple[int, float, float, float]] = {}  # symbol: (quantity, price, market_value, allocation%)
        self.orders: List[Tuple[str, str, int]] = []  # List of (symbol, action, shares)
        self.total_market_value: float = 0
        self.position_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.orders_completed: threading.Event = threading.Event()
        self.order_count: int = 0
        self.completed_orders: int = 0

    def nextValidId(self, order_id: int) -> None:
        """
        Callback that receives the next valid order ID from TWS.
        This is called automatically when the connection is established.

        Args:
            order_id (int): The next valid order ID from TWS
        """
        self.orderId = order_id - 1  # Subtract 1 since nextId will increment it

    def nextId(self) -> int:
        """
        Increment and return the next valid order ID.

        Returns:
            int: The next order ID to use

        Raises:
            RuntimeError: If orderId is None (connection not established)
        """
        if self.orderId is None:
            raise RuntimeError("Order ID not initialized. Connection to TWS may not be established.")
        self.orderId += 1
        return self.orderId

    def error(self, req_id: int, error_code: int, error_string: str, advanced_order_reject: str = "") -> None:
        """
        Error callback method that is called when an error occurs.

        Args:
            req_id (int): The request ID associated with the error
            error_code (int): The error code
            error_string (str): The error description
            advanced_order_reject (str, optional): Advanced order rejection reason
        """
        print(
            f"reqId: {req_id}, errorCode: {error_code}, errorString: {error_string}, orderReject: {advanced_order_reject}")

    def position(self, account: str, contract: Contract, position: float, _avg_cost: float) -> None:
        """
        Position callback method that is called with the current position for a contract.

        Args:
            account (str): The account name
            contract (Contract): The contract object
            position (float): The position size
            _avg_cost (float): The average cost of the position
        """
        symbol = contract.symbol
        price = get_price(symbol)
        market_value = price * int(position)
        # Initialize with 0% allocation - will be updated in positionEnd
        self.positions_map[symbol] = (int(position), price, market_value, 0.0)

    def positionEnd(self) -> None:
        """
        Called when all position data has been received. This method calculates the
        total market value of all positions and the allocation percentage for each
        position. It also triggers the position callback if it has been set.
        """
        self.total_market_value = sum(value[2] for value in self.positions_map.values())
        print("Total Market Value:", self.total_market_value)
        for symbol, (position, price, market_value) in self.positions_map.items():
            self.positions_map[symbol] = (position, price, market_value, market_value / self.total_market_value * 100)
            print(
                f"Symbol: {symbol}, Position: {position}, Current Price: {price}, Market Value: {price * int(position):.2f}, Allocation: {market_value / self.total_market_value * 100:.2f}%")
        if self.position_callback:
            self.position_callback(self.positions_map)

    def get_my_positions(self, callback: Optional[Callable[[dict], None]] = None) -> None:
        """
        Request the current positions for the account. The results will be sent to
        the position callback method.

        Args:
            callback (callable, optional): A callback method that will be called with
                                            the positions data
        """
        self.position_callback = callback
        self.reqPositions()

    def create_rebalance_orders(self, desired_alloc: Dict[str, float]) -> List[Tuple[str, str, int]]:
        """
        Create rebalance orders based on the difference between current and desired
        allocation percentages.

        Args:
            desired_alloc (dict): A dictionary with symbols as keys and desired
                                  allocation percentages as values

        Returns:
            List: A list of orders to be executed for rebalancing
        """
        # Get current allocations
        current_alloc = self.positions_map

        # Generate orders based on the difference
        self.orders = []
        for symbol, desired_pct in desired_alloc.items():
            desired_value = self.total_market_value * (desired_pct / 100)

            # Get current position details
            curr_qty, curr_market_value = 0, 0
            if symbol in current_alloc:
                curr_qty, curr_market_value = current_alloc[symbol][0], current_alloc[symbol][2]

            # Calculate difference and required shares
            value_difference = desired_value - curr_market_value
            price = self.positions_map[symbol][1]
            shares_to_trade = int(value_difference / price)

            # Generate buy/sell order if needed
            if shares_to_trade > 0:
                self.orders.append((symbol, "BUY", shares_to_trade))
            elif shares_to_trade < 0:
                self.orders.append((symbol, "SELL", abs(shares_to_trade)))

        return self.orders

    def orderStatus(self, order_id: int, status: str, filled: float, remaining: float,
                   _avg_fill_price: float, _perm_id: str, _parent_id: str, _last_fill_price: float,
                   _client_id: int, _why_held: str, _mkt_cap_price: float) -> None:
        """
        Order status callback method that is called with the current status of an order.

        Args:
            order_id (int): The order ID
            status (str): The order status
            filled (float): The quantity filled
            remaining (float): The quantity remaining
            _avg_fill_price (float): The average fill price
            _perm_id (str): The permanent ID of the order
            _parent_id (str): The parent ID of the order (if it's a child order)
            _last_fill_price (float): The last fill price
            _client_id (int): The client ID
            _why_held (str): The reason the order is held in the market
            _mkt_cap_price (float): The market cap price
        """
        print(f"Order {order_id} status: {status}, filled: {filled}")
        if status in ["Filled", "Cancelled", "Inactive"]:
            self.completed_orders += 1
            if self.completed_orders >= self.order_count:
                self.orders_completed.set()

    def set_order_count(self, count: int) -> None:
        """
        Set the expected number of orders to be completed. This is used to synchronize
        the order processing.

        Args:
            count (int): The number of orders expected
        """
        self.order_count = count
        self.completed_orders = 0
        self.orders_completed.clear()


def create_and_connect_app() -> IBApp:
    """
    Creates and connects a new IBApp instance to TWS/IB Gateway.

    Returns:
        IBApp: A connected IBApp instance ready for trading

    Raises:
        RuntimeError: If connection fails or order ID is not initialized
    """
    app = IBApp()
    app.connect("127.0.0.1", 7496, 0)

    # Start the client thread
    api_thread = threading.Thread(target=app.run)
    api_thread.start()

    # Wait for connection and orderId initialization
    timeout = 5  # seconds
    start_time = time.time()
    while app.orderId is None:
        time.sleep(0.1)
        if time.time() - start_time > timeout:
            app.disconnect()
            raise RuntimeError("Failed to connect to TWS or receive initial order ID")

    return app


def disconnect_app(app: IBApp) -> None:
    """
    Safely disconnects an IBApp instance from TWS/IB Gateway.

    Args:
        app (IBApp): The IBApp instance to disconnect
    """
    app.disconnect()
