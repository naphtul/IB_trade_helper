import csv
from datetime import datetime
from typing import Dict

from chaikin import get_watchlist


def rebalance_portfolio(watchlist: Dict[str, Dict], rating_weights_override: Dict[int, float] = None) -> Dict[str, float]:
    """Rebalances the portfolio based on the provided watchlist.

    This function takes a watchlist of symbols and their corresponding rating IDs,
    groups them by rating ID, assigns base percentages based on rating IDs, normalizes
    the total to 99.9%, and returns a dictionary with symbols and their assigned percentages.

    :param watchlist: A dictionary where keys are stock symbols and values are their rating IDs.
    :return: A dictionary where keys are stock symbols and values are their assigned percentages.
    """
    # Step 1: Group by rating_id
    groups = {}
    for sym, details in watchlist.items():
        groups.setdefault(details["rating_id"], []).append(sym)

    # Step 2: Assign base percentages (double per rating)
    rating_ids = sorted(groups.keys())
    if rating_weights_override:
        rating_weights = {rid: rating_weights_override.get(rid, 1.0) for rid in rating_ids}
    else:
        base = 1.0
        rating_weights = {}
        for i, rid in enumerate(rating_ids):
            rating_weights[rid] = base * (2 ** (rid - min(rating_ids)))

    # Step 3: Calculate total weight
    total_weight = sum(rating_weights[rid] * len(groups[rid]) for rid in rating_ids)

    # Step 4: Normalize to 99.9%
    try:
        scale = 99.9 / total_weight
    except ZeroDivisionError:
        print(watchlist)
        raise ValueError("No valid ratings found to rebalance.")

    # Step 5: Assign percentages
    result = {}
    for rid in rating_ids:
        per_symbol = rating_weights[rid] * scale
        for sym in groups[rid]:
            result[sym] = round(per_symbol, 4)

    # Step 6: Adjust to not exceed 99.9%
    total = sum(result.values())
    if total > 99.9:
        # Reduce the smallest allocation(s) to fit
        excess = total - 99.9
        max_sym = min(result, key=result.get)
        result[max_sym] = round(result[max_sym] - excess, 4)

    return result


def download_rebalance_csv(portfolio: dict, suffix: str = "rebal") -> None:
    """Downloads the rebalanced portfolio to a CSV file.

    This function generates a CSV file with the current date and a specified suffix,
    containing the rebalanced portfolio data in a specific format.

    :param portfolio: A dictionary where keys are stock symbols and values are their assigned percentages.
    :param suffix: A string suffix to append to the filename for the CSV export.
    """
    today = datetime.now().strftime("%Y%m%d")
    filename = f"{today} {suffix}.csv"
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["CSVEXPORT"])  # First row
        for symbol, percent in portfolio.items():
            row = [
                "DES",           # Column A
                symbol,          # Column B
                "STK",           # Column C
                "SMART/AMEX",    # Column D
                "", "", "", "", "",  # Columns E to I (empty)
                percent          # Column J
            ]
            writer.writerow(row)


if __name__ == "__main__":
    my_portfolio = rebalance_portfolio(get_watchlist())
    print(my_portfolio)
    download_rebalance_csv(my_portfolio)
    print(f"Saved rebalance portfolio to CSV file.")
