import threading
from typing import Dict, Any

from chaikin import get_watchlist
from orders import create_stock_contract, create_market_order
from rebalance import rebalance_portfolio
from tws_api import create_and_connect_app, disconnect_app


def main() -> None:
    """
    Main function that orchestrates the portfolio rebalancing process.

    This function:
    1. Connects to Interactive Brokers TWS
    2. Retrieves the watchlist from Chaikin Analytics
    3. Gets current positions from IB
    4. Calculates and executes rebalancing orders
    5. Waits for order completion
    6. Disconnects from TWS

    The function uses threading events to coordinate asynchronous operations
    and ensures proper cleanup in case of errors.
    """
    # Create events to signal completion
    positions_received = threading.Event()
    orders_placed = threading.Event()

    # Create and connect to IB TWS
    app = create_and_connect_app()

    def on_positions_received(_positions_map: Dict[str, Any]) -> None:
        """
        Callback function executed when all positions are received from TWS.

        Args:
            _positions_map : The positions map (unused in this callback)

        This function:
        1. Calculates the desired portfolio allocation
        2. Creates rebalancing orders
        3. Executes the orders through TWS
        4. Sets the orders_placed event when complete
        """
        try:
            # Calculate rebalance
            desired_portfolio = rebalance_portfolio(watchlist)

            # Create rebalance orders
            orders = app.create_rebalance_orders(desired_portfolio)

            # Print results
            print("Rebalance Orders:", orders)

            app.set_order_count(len(orders))

            # Execute orders
            for symbol, action, shares in orders:
                print(f"Executing Order: {action} {shares} shares of {symbol}")
                contract = create_stock_contract(symbol)
                order = create_market_order(action, shares)
                app.placeOrder(app.nextId(), contract, order)
            orders_placed.set()

        except Exception as e1:
            print(f"Error in callback: {e1}")
        finally:
            positions_received.set()

    try:
        # Get the watchlist from Chaikin Analytics
        watchlist: Dict[str, Dict[str, Any]] = get_watchlist()

        # Filter watchlist
        watchlist = {sym: details for sym, details in watchlist.items() if details['rating_id'] >= 5 and sym not in ['U', 'AVGO']}

        # Get current positions with callback
        app.get_my_positions(callback=on_positions_received)

        # Wait for callback to complete (timeout after 30 seconds)
        positions_received.wait(timeout=30)

        if positions_received.wait(timeout=30) and orders_placed.wait(timeout=30):
            app.orders_completed.wait(timeout=60)  # Wait for orders to complete

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Cleanup
        disconnect_app(app)


if __name__ == "__main__":
    main()
