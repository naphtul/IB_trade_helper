import os
import json
from typing import Dict, Any

from playwright.sync_api import sync_playwright, expect, Response
import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"


def parse_suggestions(suggestions: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
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
    for suggestion in suggestions.get("data", {}).get("data", []):
        symbol = suggestion.get("symbol", "")
        if symbol == "SPY":
            continue
        parsed_suggestions[symbol] = {
            "name": suggestion.get("name"),
            "rating": suggestion.get("ratingName"),
            "rating_id": suggestion.get("pgrRating"),
        }
    return parsed_suggestions


def get_watchlist() -> Dict[str, Dict[str, Any]]:
    """
    Logs into Chaikin Analytics using credentials from environment variables,
    intercepts the suggestions API response, and returns parsed suggestions.

    Returns:
        dict: Parsed suggestions data as returned by `parse_suggestions`.
    """
    # Validate that the required environment variables are set
    if not os.environ.get("CHAIKIN_EMAIL") or not os.environ.get("CHAIKIN_PASSWORD"):
        raise ValueError("Please set CHAIKIN_EMAIL and CHAIKIN_PASSWORD environment variables.")

    WATCHLIST_URL = "https://members.chaikinanalytics.com/my-chaikin/lists/health-check/my-stocks?listId=2370927&listType=User"
    WATCHLIST_API = "api/chaikinlist/mylists/watchlist?listId=2370927"
    SUGGESTIONS_API = "api/suggestions"
    SUGGESTIONS_API_FULL = "https://members-backend.chaikinanalytics.com/api/suggestions"

    with (sync_playwright() as playwright):
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        relevant_watchlist_responses = []
        suggestions_headers = {}
        suggestions_cookies = None
        suggestions_api_key = None
        suggestions_jwttoken = None
        suggestions_uuid = None
        suggestions_x_session_id = None
        suggestions_x_app_id = None
        suggestions_jsessionid = None
        suggestions_headers_found = False

        def handle_response(response: Response) -> None:
            nonlocal suggestions_headers_found
            url = response.url
            if WATCHLIST_API in url:
                data = response.json()
                relevant_watchlist_responses.append(data)
            elif SUGGESTIONS_API in url and not suggestions_headers_found:
                req = response.request
                # Extract headers needed for the proactive request
                headers = req.headers.copy()
                # Save relevant headers
                suggestions_headers['x-api-key'] = headers.get('x-api-key')
                suggestions_headers['jwttoken'] = headers.get('jwttoken')
                suggestions_headers['uuid'] = headers.get('uuid')
                suggestions_headers['x-session-id'] = headers.get('x-session-id')
                suggestions_headers['x-app-id'] = headers.get('x-app-id')
                suggestions_headers['jsessionid'] = headers.get('jsessionid')
                suggestions_headers['content-type'] = headers.get('content-type', 'application/json')
                suggestions_headers['accept'] = headers.get('accept', 'application/json, text/plain, */*')
                suggestions_headers['accept-language'] = headers.get('accept-language', 'en-US,en;q=0.9')
                suggestions_headers['referer'] = 'https://members.chaikinanalytics.com/'
                suggestions_headers_found = True

        page.on("response", handle_response)
        page.goto(WATCHLIST_URL)
        page.get_by_role("textbox", name="email").fill(os.environ.get("CHAIKIN_EMAIL", ""))
        page.get_by_role("textbox", name="password").fill(os.environ.get("CHAIKIN_PASSWORD", ""))
        page.get_by_role("button", name="Log into Chaikin Analytics").click()
        page.wait_for_load_state("networkidle", timeout=5000)
        expect(page.get_by_role("heading", name="My Chaikin")).to_be_visible(timeout=10000)

        context.close()
        browser.close()

        if not relevant_watchlist_responses:
            raise RuntimeError("Failed to get watchlist response.")
        if not suggestions_headers_found:
            raise RuntimeError("Failed to get suggestions API headers.")

        # Get symbols from watchlist
        watchlist_symbols = relevant_watchlist_responses[0].get("data", {}).get("symbols", [])
        # Prepare payload for suggestions API
        payload = {
            "count": 500,
            "page": 1,
            "sortField": "week1ChangePct",
            "sortDirection": "desc",
            "fromDate": None,
            "toDate": None,
            "symbols": watchlist_symbols,
            "listId": None
        }
        # Clean up headers for requests
        req_headers = {k: v for k, v in suggestions_headers.items() if v}
        # Make proactive POST request to suggestions API
        resp = requests.post(
            SUGGESTIONS_API_FULL,
            headers=req_headers,
            data=json.dumps(payload),
            cookies=None  # If needed, can extract cookies from Playwright context
        )
        resp.raise_for_status()
        suggestions_response = resp.json()
        return parse_suggestions(suggestions_response)


if __name__ == "__main__":
    print(get_watchlist())
