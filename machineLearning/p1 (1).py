import calendar
import requests
import pandas as pd
from datetime import date, datetime, timedelta

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NkI0VEYiLCJqdGkiOiI2YTA5OWJjNTY5YjlkYzU5MDk1ODg1Y2MiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzc5MDE0NTk3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzkwNTUyMDB9.dO96bl3AtXlaKduwHj-sCLqwisMFI-bmgBBYSavsVy0"
INSTRUMENT = "NSE_INDEX|Nifty 50"
TIMEFRAME = "1minute"
OUTPUT_CSV = "nifty50_historical_6months.csv"
MAX_CHUNK_DAYS = 30

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}


def subtract_months(value: date, months: int) -> date:
    year = value.year
    month = value.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def fetch_candles_chunk(start_date: date, end_date: date) -> list:
    url = (
        f"https://api.upstox.com/v2/historical-candle/{INSTRUMENT}/{TIMEFRAME}/"
        f"{end_date.isoformat()}/{start_date.isoformat()}"
    )

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 401:
        raise RuntimeError(
            "Unauthorized: the access token is invalid or expired. "
            "Get a fresh token from the Upstox dashboard."
        )

    if response.status_code == 400:
        data = response.json()
        errors = data.get("errors") or []
        if any(err.get("errorCode") == "UDAPI1148" for err in errors):
            raise ValueError("Invalid date range")
        if any(err.get("errorCode") == "UDAPI1015" for err in errors):
            raise ValueError("Invalid date format or reversed dates")

    response.raise_for_status()
    data = response.json()

    if data.get("status") != "success" or "data" not in data:
        raise ValueError(f"Unexpected API response: {data}")

    candles = data["data"].get("candles")
    if candles is None:
        raise ValueError(f"No candles returned for {start_date} to {end_date}")

    return candles


def fetch_historical_data(start_date: date, end_date: date) -> list:
    all_candles = []
    current_start = start_date

    while current_start <= end_date:
        chunk_end = min(current_start + timedelta(days=MAX_CHUNK_DAYS - 1), end_date)
        while True:
            try:
                print(f"Fetching {current_start.isoformat()} to {chunk_end.isoformat()}")
                candles = fetch_candles_chunk(current_start, chunk_end)
                break
            except ValueError as exc:
                if "Invalid date range" in str(exc) and chunk_end > current_start:
                    chunk_end -= timedelta(days=1)
                    print(f"  Reducing chunk size to {current_start.isoformat()} to {chunk_end.isoformat()}")
                    continue
                raise

        all_candles.extend(candles)
        current_start = chunk_end + timedelta(days=1)

    return all_candles


def main() -> None:
    today = date.today()
    six_months_ago = subtract_months(today, 12)

    print(f"Loading data for {INSTRUMENT} from {six_months_ago} to {today}")
    candles = fetch_historical_data(six_months_ago, today)

    if not candles:
        print("No candle data was returned.")
        return

    df = pd.DataFrame(candles, columns=[
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "oi",
    ])

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved {len(df)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
