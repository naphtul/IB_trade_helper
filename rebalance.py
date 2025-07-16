from chaikin import get_suggestions


def rebalance_suggestions(suggestions: dict) -> dict:
    # TODO: Move #1 to another file
    # TODO: rename suggestions to something better
    # TODO: add docstring
    # TODO: accept optional weighting rates
    # Step 1: Filter out 'U' and rating_id < 5
    filtered = {sym: rating_id["rating_id"] for sym, rating_id in suggestions.items()
                if sym != "U" and rating_id["rating_id"] >= 5}

    # Step 2: Group by rating_id
    groups = {}
    for sym, rating_id in filtered.items():
        groups.setdefault(rating_id, []).append(sym)

    # Step 3: Assign base percentages (double per rating)
    rating_ids = sorted(groups.keys())
    base = 1.0
    rating_weights = {}
    for i, rid in enumerate(rating_ids):
        rating_weights[rid] = base * (2 ** (rid - min(rating_ids)))

    # Step 4: Calculate total weight
    total_weight = sum(rating_weights[rid] * len(groups[rid]) for rid in rating_ids)

    # Step 5: Normalize to 99.9%
    scale = 99.9 / total_weight

    # Step 6: Assign percentages
    result = {}
    for rid in rating_ids:
        per_symbol = rating_weights[rid] * scale
        for sym in groups[rid]:
            result[sym] = round(per_symbol, 4)

    # Step 7: Adjust to not exceed 99.9%
    total = sum(result.values())
    if total > 99.9:
        # Reduce the smallest allocation(s) to fit
        excess = total - 99.9
        max_sym = min(result, key=result.get)
        result[max_sym] = round(result[max_sym] - excess, 4)

    return result


if __name__ == "__main__":
    print(rebalance_suggestions(get_suggestions()))
