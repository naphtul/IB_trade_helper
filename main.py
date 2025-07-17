from chaikin import get_watchlist
from rebalance import rebalance_portfolio, download_rebalance_csv


if __name__ == "__main__":
    # Get the watchlist from Chaikin Analytics
    watchlist = get_watchlist()

    # Filter watchlist to include only symbols with rating_id >= 5 and not 'U'
    watchlist = {sym: details for sym, details in watchlist.items() if details['rating_id'] >= 5 and sym != 'U'}

    # Rebalance the portfolio based on the watchlist
    my_portfolio = rebalance_portfolio(watchlist)

    # Print the rebalanced portfolio
    print(my_portfolio)

    # Download the rebalanced portfolio to a CSV file
    download_rebalance_csv(my_portfolio)

    print("Saved rebalance portfolio to CSV file.")
