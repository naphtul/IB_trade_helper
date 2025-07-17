import os

from playwright.sync_api import sync_playwright, expect


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"


def parse_suggestions(suggestions: dict) -> dict:
    """
    Parses the raw suggestions API response and returns a dictionary
    mapping symbols to their details.

    Args:
        suggestions (dict): The raw suggestions API response.

    Returns:
        dict: A dictionary where each key is a symbol and the value is a dict
              containing 'name', 'rating', and 'rating_id'.
    """
    parsed_suggestions = {}
    for suggestion in suggestions.get("data", {}).get("data", {}).get("data", []):
        symbol = suggestion.get("symbol", "")
        parsed_suggestions[symbol] = {
            "name": suggestion.get("name"),
            "rating": suggestion.get("ratingName"),
            "rating_id": suggestion.get("pgrRating"),
        }
    return parsed_suggestions


def get_watchlist() -> dict:
    """
    Logs into Chaikin Analytics using credentials from environment variables,
    intercepts the suggestions API response, and returns parsed suggestions.

    Returns:
        dict: Parsed suggestions data as returned by `parse_suggestions`.
    """
    # Validate that the required environment variables are set
    if not os.environ.get("CHAIKIN_EMAIL") or not os.environ.get("CHAIKIN_PASSWORD"):
        raise ValueError("Please set CHAIKIN_EMAIL and CHAIKIN_PASSWORD environment variables.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        suggestions_response = {}

        def handle_response(response):
            """
            Intercepts network responses in Playwright and stores the JSON data
            from the suggestions API endpoint in the suggestions_response dictionary.

            Args:
                response: The Playwright response object.

            Side Effects:
                Updates suggestions_response["data"] with the parsed JSON response
                if the response URL matches the suggestions API.
            """
            if "api/suggestions" in response.url:
                suggestions_response["data"] = response.json()

        page.on("response", handle_response)
        page.goto("https://members.chaikinanalytics.com/my-chaikin")
        page.get_by_role("textbox", name="email").fill(os.environ.get("CHAIKIN_EMAIL", ""))
        page.get_by_role("textbox", name="password").fill(os.environ.get("CHAIKIN_PASSWORD", ""))
        page.get_by_role("button", name="Log into Chaikin Analytics").click()
        expect(page.get_by_role("heading", name="My Chaikin")).to_be_visible(timeout=10000)

        context.close()
        browser.close()
        return parse_suggestions(suggestions_response)


if __name__ == "__main__":
    print(get_watchlist())
