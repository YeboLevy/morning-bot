# ============================================================
# morning_briefing.py — A Morning Briefing Bot with LIVE DATA
#
# BOT PATTERN: A bot is a program that runs automatically,
# gathers information from multiple sources, and presents
# a useful summary — without you having to do anything.
#
# This bot follows three clear steps every time it runs:
#
#   GATHER  → Fetch LIVE data from APIs (weather, news, currency)
#   PROCESS → Transform raw data into useful summaries
#   PRESENT → Format everything into a beautiful report
#
# APIs used:
#   • Open-Meteo API — Free weather data (no key needed)
#   • NewsAPI — Top headlines (requires API key)
#   • ExchangeRate-API — Currency rates (no key needed)
#
# Run it each morning with: python morning_briefing.py
# ============================================================

import os
import json
import requests  # For making HTTP API calls
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from notifier import Notifier  # For desktop/email notifications

# ── Load .env so we can use variables like USER_NAME and API keys ──
# python-dotenv reads the .env file and injects its key=value
# pairs into the environment so os.getenv() can find them.
load_dotenv()

# ============================================================
# CONFIGURATION
# API endpoints and local settings
# ============================================================

# API endpoints (all free to use!)
WEATHER_API_URL  = "https://api.open-meteo.com/v1/forecast"
NEWS_API_URL     = "https://newsapi.org/v2/top-headlines"
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# Johannesburg coordinates for weather API
JHB_LATITUDE     = -26.2041
JHB_LONGITUDE    = 28.0473

# Date and file paths
TODAY            = datetime.now().date()
TODAY_STR        = TODAY.strftime("%Y-%m-%d")
REPORT_FILE      = Path(__file__).parent / f"morning_briefing_{TODAY_STR}.txt"

# Request timeout for all API calls (seconds)
API_TIMEOUT      = 10

# ============================================================
# STEP 1 — GATHER
# Each gather_* function fetches LIVE data from an API and returns:
#   (data, error_message)
# If the API fails or network is down, data is empty and
# error_message explains what went wrong — so the rest of
# the bot keeps running instead of crashing.
# ============================================================

def gather_weather():
    """
    GATHER: Fetch LIVE weather data from Open-Meteo API.

    Open-Meteo is a free weather API that needs NO API KEY!
    We request:
      • Current temperature and weather condition
      • Hourly forecasts for today (to find best running time)
      • Wind speed, precipitation probability

    API Docs: https://open-meteo.com/en/docs

    Returns: (weather_data_dict, error_message)
    """
    try:
        # Build API request parameters
        params = {
            "latitude":  JHB_LATITUDE,
            "longitude": JHB_LONGITUDE,
            "current": [
                "temperature_2m",           # Current temp in °C
                "weather_code",             # WMO weather code (0=clear, 1-3=clouds, etc.)
                "wind_speed_10m",           # Wind speed
            ],
            "hourly": [
                "temperature_2m",           # Hourly temps for today
                "precipitation_probability", # Rain chance each hour
                "wind_speed_10m",           # Wind speed each hour
            ],
            "timezone": "Africa/Johannesburg",
            "forecast_days": 1,             # Only need today
        }

        # Make the HTTP GET request with a 10-second timeout
        response = requests.get(WEATHER_API_URL, params=params, timeout=API_TIMEOUT)

        # Raise an exception if the status code indicates an error (404, 500, etc.)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        return data, None

    except requests.exceptions.Timeout:
        return {}, "Weather API timed out (slow network)"
    except requests.exceptions.ConnectionError:
        return {}, "Could not connect to weather API (check internet)"
    except requests.exceptions.HTTPError as e:
        return {}, f"Weather API error: {e}"
    except Exception as e:
        return {}, f"Unexpected weather error: {e}"


def gather_news():
    """
    GATHER: Fetch top headlines from NewsAPI.

    NewsAPI provides breaking news from 80,000+ sources.
    Requires an API key (get free at: https://newsapi.org)

    We fetch:
      • Top 3 technology headlines (worldwide)
      • Top 3 business headlines for South Africa

    API Docs: https://newsapi.org/docs/endpoints/top-headlines

    Returns: (news_dict, error_message)
    """
    # Read API key from environment variable
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return {}, "NEWS_API_KEY not found in .env file"

    try:
        # Fetch technology news (worldwide, English)
        tech_params = {
            "apiKey":   api_key,
            "category": "technology",
            "language": "en",
            "pageSize": 3,              # Only top 3 articles
        }
        tech_response = requests.get(NEWS_API_URL, params=tech_params, timeout=API_TIMEOUT)
        tech_response.raise_for_status()
        tech_data = tech_response.json()

        # Fetch business news for South Africa
        biz_params = {
            "apiKey":   api_key,
            "category": "business",
            "country":  "za",           # ISO code for South Africa
            "pageSize": 3,
        }
        biz_response = requests.get(NEWS_API_URL, params=biz_params, timeout=API_TIMEOUT)
        biz_response.raise_for_status()
        biz_data = biz_response.json()

        return {
            "tech": tech_data.get("articles", []),
            "business": biz_data.get("articles", []),
        }, None

    except requests.exceptions.Timeout:
        return {}, "News API timed out"
    except requests.exceptions.ConnectionError:
        return {}, "Could not connect to News API"
    except requests.exceptions.HTTPError as e:
        # Check if it's an auth error (401) or quota exceeded (429)
        if e.response.status_code == 401:
            return {}, "Invalid NEWS_API_KEY (check your .env file)"
        elif e.response.status_code == 429:
            return {}, "News API quota exceeded (upgrade at newsapi.org)"
        else:
            return {}, f"News API error: {e}"
    except Exception as e:
        return {}, f"Unexpected news error: {e}"


def gather_currency():
    """
    GATHER: Fetch live currency exchange rates.

    ExchangeRate-API provides free currency data with NO API KEY needed!
    We fetch the latest USD rates and extract ZAR conversions.

    Currencies we track:
      • USD to ZAR (US Dollar → South African Rand)
      • EUR to ZAR (Euro → Rand)
      • GBP to ZAR (British Pound → Rand)

    API Docs: https://www.exchangerate-api.com

    Returns: (rates_dict, error_message)
    """
    try:
        # Fetch latest rates with USD as base currency
        response = requests.get(CURRENCY_API_URL, timeout=API_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        # Extract the rates we care about
        # rates["ZAR"] = how many ZAR for 1 USD
        # rates["EUR"] = how many EUR for 1 USD
        # To get EUR→ZAR, we calculate: ZAR / EUR
        rates = data.get("rates", {})

        usd_to_zar = rates.get("ZAR", 0)
        eur_to_zar = usd_to_zar / rates.get("EUR", 1) if rates.get("EUR") else 0
        gbp_to_zar = usd_to_zar / rates.get("GBP", 1) if rates.get("GBP") else 0

        return {
            "USD_ZAR": usd_to_zar,
            "EUR_ZAR": eur_to_zar,
            "GBP_ZAR": gbp_to_zar,
            "last_updated": data.get("date", "unknown"),
        }, None

    except requests.exceptions.Timeout:
        return {}, "Currency API timed out"
    except requests.exceptions.ConnectionError:
        return {}, "Could not connect to currency API"
    except requests.exceptions.HTTPError as e:
        return {}, f"Currency API error: {e}"
    except Exception as e:
        return {}, f"Unexpected currency error: {e}"


# ============================================================
# STEP 2 — PROCESS
# Each process_* function takes raw API data and computes
# something useful from it: summaries, best times, formatting.
# Pure calculation — no API calls, no printing here.
# ============================================================

def process_weather(weather_data):
    """
    PROCESS: Analyze weather data and find best running time.

    Running criteria (good conditions):
      • Temperature: 10-25°C (50-77°F)
      • Low wind speed: < 20 km/h
      • Low rain chance: < 30%

    Returns summary with current conditions and best running hour.
    """
    if not weather_data:
        return None

    try:
        current = weather_data.get("current", {})
        hourly = weather_data.get("hourly", {})

        # Current weather
        temp_now = current.get("temperature_2m", 0)
        wind_now = current.get("wind_speed_10m", 0)
        weather_code = current.get("weather_code", 0)

        # Decode WMO weather code into readable condition
        # 0 = Clear, 1-3 = Partly cloudy, 45-48 = Fog, 51-67 = Rain, 71-86 = Snow, 95-99 = Thunderstorm
        if weather_code == 0:
            condition = "Clear skies"
        elif weather_code <= 3:
            condition = "Partly cloudy"
        elif weather_code <= 48:
            condition = "Foggy"
        elif weather_code <= 67:
            condition = "Rainy"
        elif weather_code <= 86:
            condition = "Snowy"
        else:
            condition = "Stormy"

        # Find best running time (check 6 AM - 8 PM)
        best_hour = None
        best_score = -1

        hours = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        rain_probs = hourly.get("precipitation_probability", [])
        winds = hourly.get("wind_speed_10m", [])

        for i, hour_str in enumerate(hours):
            hour = int(hour_str.split("T")[1].split(":")[0])  # Extract hour from ISO time

            # Only consider daytime hours (6 AM - 8 PM)
            if hour < 6 or hour >= 20:
                continue

            temp = temps[i]
            rain = rain_probs[i]
            wind = winds[i]

            # Score this hour (higher = better)
            score = 0
            if 10 <= temp <= 25:  # Ideal temp
                score += 3
            elif 8 <= temp <= 28:  # Acceptable
                score += 1

            if rain < 30:  # Low rain chance
                score += 2
            if wind < 20:  # Low wind
                score += 1

            if score > best_score:
                best_score = score
                best_hour = hour

        # Determine if it's good running weather
        if best_score >= 4:
            running_advice = f"Great running weather! Best time: {best_hour}:00"
        elif best_score >= 2:
            running_advice = f"Decent conditions. Try {best_hour}:00 if you can"
        else:
            running_advice = "Not ideal for running today (weather)"

        return {
            "temperature": temp_now,
            "condition": condition,
            "wind_speed": wind_now,
            "best_running_time": running_advice,
        }

    except (KeyError, IndexError, ValueError):
        return None


def process_news(news_data):
    """PROCESS: Extract article titles and sources from news data."""
    if not news_data:
        return None

    tech_articles = []
    for article in news_data.get("tech", [])[:3]:
        tech_articles.append({
            "title": article.get("title", "No title"),
            "source": article.get("source", {}).get("name", "Unknown"),
        })

    biz_articles = []
    for article in news_data.get("business", [])[:3]:
        biz_articles.append({
            "title": article.get("title", "No title"),
            "source": article.get("source", {}).get("name", "Unknown"),
        })

    return {
        "tech": tech_articles,
        "business": biz_articles,
    }


def process_currency(rates_data):
    """PROCESS: Format currency rates for display."""
    if not rates_data:
        return None

    return {
        "USD_ZAR": rates_data.get("USD_ZAR", 0),
        "EUR_ZAR": rates_data.get("EUR_ZAR", 0),
        "GBP_ZAR": rates_data.get("GBP_ZAR", 0),
        "last_updated": rates_data.get("last_updated", "unknown"),
    }


# ============================================================
# STEP 3 — PRESENT
# Each present_* function turns processed data into a block
# of formatted text. If there was a gathering error, it shows
# a friendly error note instead of crashing.
# All present_* functions return a plain string.
# ============================================================

def _greeting():
    """Return 'Good morning', 'afternoon', or 'evening' based on the hour."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def present_header():
    """PRESENT: Top banner with date and personalised greeting."""
    name          = os.getenv("USER_NAME", "Friend")
    date_long     = datetime.now().strftime("%A, %B %d, %Y")

    return "\n".join([
        "=" * 60,
        f"  MORNING BRIEFING  —  {date_long}",
        "=" * 60,
        f"  {_greeting()}, {name}! Here's what's happening today.",
        "=" * 60,
        "",
    ])


def present_weather(summary, error):
    """PRESENT: Current weather and best running time."""
    lines = ["--- WEATHER IN JOHANNESBURG " + "-" * 32, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not summary:
        lines += ["  No weather data available.", ""]
        return "\n".join(lines)

    lines.append(f"  Current:      {summary['temperature']:.1f}°C — {summary['condition']}")
    lines.append(f"  Wind:         {summary['wind_speed']:.1f} km/h")
    lines.append("")
    lines.append(f"  🏃 {summary['best_running_time']}")
    lines.append("")

    return "\n".join(lines)


def present_news(summary, error):
    """PRESENT: Top headlines from tech and business."""
    lines = ["--- NEWS HEADLINES " + "-" * 41, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not summary:
        lines += ["  No news available.", ""]
        return "\n".join(lines)

    # Technology news
    lines.append("  TECHNOLOGY:")
    if summary.get("tech"):
        for i, article in enumerate(summary["tech"], 1):
            lines.append(f"  {i}. {article['title']}")
            lines.append(f"     — {article['source']}")
            lines.append("")
    else:
        lines.append("     No tech news available.")
        lines.append("")

    # Business news
    lines.append("  BUSINESS (South Africa):")
    if summary.get("business"):
        for i, article in enumerate(summary["business"], 1):
            lines.append(f"  {i}. {article['title']}")
            lines.append(f"     — {article['source']}")
            lines.append("")
    else:
        lines.append("     No business news available.")
        lines.append("")

    return "\n".join(lines)


def present_currency(summary, error):
    """PRESENT: Live currency exchange rates."""
    lines = ["--- CURRENCY RATES " + "-" * 41, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not summary:
        lines += ["  No currency data available.", ""]
        return "\n".join(lines)

    lines.append(f"  1 USD  =  R {summary['USD_ZAR']:.2f}")
    lines.append(f"  1 EUR  =  R {summary['EUR_ZAR']:.2f}")
    lines.append(f"  1 GBP  =  R {summary['GBP_ZAR']:.2f}")
    lines.append("")
    lines.append(f"  Last updated: {summary['last_updated']}")
    lines.append("")

    return "\n".join(lines)


def present_footer():
    """PRESENT: Closing banner with timestamp."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join([
        "=" * 60,
        f"  Generated at {generated_at}",
        "  Have a productive day!",
        "=" * 60,
    ])


# ============================================================
# MAIN — Orchestrate the three-step bot pattern
#
#   GATHER   → Fetch LIVE data from APIs (may fail gracefully)
#   PROCESS  → Compute summaries from raw API data
#   PRESENT  → Format summaries into a human-readable report
#   SAVE     → Write report to a dated .txt file
# ============================================================

def main():
    print("Starting Morning Briefing Bot with LIVE DATA…\n")

    # ── GATHER ──────────────────────────────────────────────
    # Fetch from every API. Errors are captured, not raised,
    # so a failed API call never stops the whole report.
    print("  [1/3] Gathering LIVE data from APIs…")
    raw_weather,   weather_error   = gather_weather()
    raw_news,      news_error      = gather_news()
    raw_currency,  currency_error  = gather_currency()

    # ── PROCESS ─────────────────────────────────────────────
    # Transform raw API data into summaries the presenter can use.
    print("  [2/3] Processing data…")
    weather_summary   = process_weather(raw_weather)
    news_summary      = process_news(raw_news)
    currency_summary  = process_currency(raw_currency)

    # ── PRESENT ─────────────────────────────────────────────
    # Assemble each section into one big report string.
    print("  [3/3] Generating report…\n")
    report = "\n".join([
        present_header(),
        present_weather(weather_summary,   weather_error),
        present_news(news_summary,         news_error),
        present_currency(currency_summary, currency_error),
        present_footer(),
    ])

    # Print to terminal
    print(report)

    # ── SAVE ────────────────────────────────────────────────
    # Write the same report to a dated text file.
    try:
        with open(REPORT_FILE, "w") as f:
            f.write(report)
        print(f"\n✓ Report saved → {REPORT_FILE}")

        # ── NOTIFY ──────────────────────────────────────────────
        # Send desktop notification that briefing is ready
        try:
            notifier = Notifier()
            notifier.send(
                title="📰 Morning Briefing Ready",
                message="Your daily briefing has been generated with live weather, news, and currency rates",
                method="desktop",
                urgency="info"
            )
        except Exception as notify_error:
            # If notification fails, don't crash the bot
            print(f"[!] Could not send notification: {notify_error}")

    except OSError as e:
        print(f"\n[!] Could not save report file: {e}")


if __name__ == "__main__":
    main()
