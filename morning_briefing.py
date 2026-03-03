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
#   • CoinGecko API — Cryptocurrency prices (no key needed)
#
# Run it each morning with: python morning_briefing.py
# ============================================================

import os
import json
import requests  # For making HTTP API calls
import smtplib  # For sending emails
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

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
CRYPTO_API_URL   = "https://api.coingecko.com/api/v3/simple/price"

# Johannesburg coordinates for weather API
JHB_LATITUDE     = -26.2041
JHB_LONGITUDE    = 28.0473

# Date and file paths
TODAY            = datetime.now().date()
TODAY_STR        = TODAY.strftime("%Y-%m-%d")
REPORT_FILE      = Path(__file__).parent / f"morning_briefing_{TODAY_STR}.txt"

# Daily photo and riddle data files
LOCATIONS_FILE   = Path(__file__).parent / "exotic_locations.json"
RIDDLES_FILE     = Path(__file__).parent / "riddles.json"
STATE_FILE       = Path(__file__).parent / "daily_state.json"

# Request timeout for all API calls (seconds)
API_TIMEOUT      = 10

# ============================================================
# DAILY CONTENT MANAGEMENT
# Load and rotate daily photo locations and riddles
# ============================================================

def load_daily_content():
    """
    Load today's exotic location photo and riddle.

    This function:
    1. Loads the exotic locations and riddles from JSON files
    2. Reads the current state (which location/riddle we're on)
    3. Returns today's location and riddle
    4. Saves yesterday's riddle answer for tomorrow
    5. Increments counters for next day

    Returns: (location_dict, riddle_dict, yesterday_riddle, yesterday_answer)
    """
    try:
        # Load locations and riddles
        with open(LOCATIONS_FILE, 'r') as f:
            locations = json.load(f)

        with open(RIDDLES_FILE, 'r') as f:
            riddles = json.load(f)

        # Load current state
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        else:
            # Initialize state if file doesn't exist
            state = {
                "location_index": 0,
                "riddle_index": 0,
                "yesterday_riddle": None,
                "yesterday_answer": None,
                "last_updated": None
            }

        # Check if we need to update (new day)
        last_updated = state.get("last_updated")
        should_update = last_updated != TODAY_STR

        if should_update:
            # Get current indices
            loc_idx = state.get("location_index", 0)
            riddle_idx = state.get("riddle_index", 0)

            # Get today's content
            today_location = locations[loc_idx % len(locations)]
            today_riddle = riddles[riddle_idx % len(riddles)]

            # Save yesterday's riddle and answer for tomorrow
            yesterday_riddle = state.get("yesterday_riddle")
            yesterday_answer = state.get("yesterday_answer")

            # Update state for next day
            state["location_index"] = (loc_idx + 1) % len(locations)
            state["riddle_index"] = (riddle_idx + 1) % len(riddles)
            state["yesterday_riddle"] = today_riddle["riddle"]
            state["yesterday_answer"] = today_riddle["answer"]
            state["last_updated"] = TODAY_STR

            # Save updated state
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)

            return today_location, today_riddle, yesterday_riddle, yesterday_answer
        else:
            # Same day - return current content without updating
            loc_idx = (state.get("location_index", 1) - 1) % len(locations)
            riddle_idx = (state.get("riddle_index", 1) - 1) % len(riddles)

            today_location = locations[loc_idx]
            today_riddle = riddles[riddle_idx]
            yesterday_riddle = state.get("yesterday_riddle")
            yesterday_answer = state.get("yesterday_answer")

            return today_location, today_riddle, yesterday_riddle, yesterday_answer

    except Exception as e:
        print(f"[!] Could not load daily content: {e}")
        return None, None, None, None

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
      • Top 5 world news headlines

    API Docs: https://newsapi.org/docs/endpoints/top-headlines

    Returns: (news_dict, error_message)
    """
    # Read API key from environment variable
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return {}, "NEWS_API_KEY not found in .env file"

    try:
        # Fetch world news (English)
        world_params = {
            "apiKey":   api_key,
            "category": "general",      # General/world news
            "language": "en",
            "pageSize": 5,              # Top 5 articles
        }
        world_response = requests.get(NEWS_API_URL, params=world_params, timeout=API_TIMEOUT)
        world_response.raise_for_status()
        world_data = world_response.json()

        return {
            "world": world_data.get("articles", []),
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


def gather_crypto():
    """
    GATHER: Fetch LIVE cryptocurrency prices from CoinGecko API.

    CoinGecko is a free crypto data API that needs NO API KEY!
    We request:
      • Bitcoin (BTC) and Ethereum (ETH) prices
      • Prices in both USD and ZAR
      • 24-hour price change percentage

    API Docs: https://www.coingecko.com/en/api/documentation

    Returns: (crypto_data_dict, error_message)
    """
    try:
        # Build API request parameters
        # ids: which cryptocurrencies to fetch
        # vs_currencies: which fiat currencies to show prices in
        # include_24hr_change: include the percentage change over last 24 hours
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd,zar",
            "include_24hr_change": "true",
        }

        # Make the HTTP GET request
        response = requests.get(CRYPTO_API_URL, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()

        # Parse JSON response
        # Response format:
        # {
        #   "bitcoin": {
        #     "usd": 67234.50,
        #     "zar": 1243567,
        #     "usd_24h_change": 2.3,
        #     "zar_24h_change": 2.3
        #   },
        #   "ethereum": { ... }
        # }
        data = response.json()

        return data, None

    except requests.exceptions.Timeout:
        return {}, "Crypto API timed out (slow network)"
    except requests.exceptions.ConnectionError:
        return {}, "Could not connect to crypto API (check internet)"
    except requests.exceptions.HTTPError as e:
        return {}, f"Crypto API error: {e}"
    except Exception as e:
        return {}, f"Unexpected crypto error: {e}"


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

    world_articles = []
    for article in news_data.get("world", [])[:5]:
        world_articles.append({
            "title": article.get("title", "No title"),
            "source": article.get("source", {}).get("name", "Unknown"),
        })

    return {
        "world": world_articles,
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


def process_crypto(crypto_data):
    """
    PROCESS: Extract and format cryptocurrency price data.

    Takes raw CoinGecko API response and extracts:
      • Current prices in USD and ZAR
      • 24-hour change percentages
      • Up/down indicators and color emojis

    Returns formatted data ready for presentation.
    """
    if not crypto_data:
        return None

    try:
        # Extract Bitcoin data
        btc = crypto_data.get("bitcoin", {})
        btc_usd = btc.get("usd", 0)
        btc_zar = btc.get("zar", 0)
        btc_change = btc.get("usd_24h_change", 0)

        # Determine if Bitcoin is up or down
        btc_direction = "↑" if btc_change >= 0 else "↓"
        btc_color = "🟢" if btc_change >= 0 else "🔴"

        # Extract Ethereum data
        eth = crypto_data.get("ethereum", {})
        eth_usd = eth.get("usd", 0)
        eth_zar = eth.get("zar", 0)
        eth_change = eth.get("usd_24h_change", 0)

        # Determine if Ethereum is up or down
        eth_direction = "↑" if eth_change >= 0 else "↓"
        eth_color = "🟢" if eth_change >= 0 else "🔴"

        return {
            "bitcoin": {
                "usd": btc_usd,
                "zar": btc_zar,
                "change": btc_change,
                "direction": btc_direction,
                "color": btc_color,
            },
            "ethereum": {
                "usd": eth_usd,
                "zar": eth_zar,
                "change": eth_change,
                "direction": eth_direction,
                "color": eth_color,
            },
        }

    except (KeyError, ValueError):
        return None


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
    """PRESENT: Top world news headlines."""
    lines = ["--- WORLD NEWS " + "-" * 45, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not summary:
        lines += ["  No news available.", ""]
        return "\n".join(lines)

    # World news
    if summary.get("world"):
        for i, article in enumerate(summary["world"], 1):
            lines.append(f"  {i}. {article['title']}")
            lines.append(f"     — {article['source']}")
            lines.append("")
    else:
        lines.append("  No world news available.")
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


def present_crypto(summary, error):
    """PRESENT: Live cryptocurrency prices with 24h change indicators."""
    lines = ["--- CRYPTO MARKETS " + "-" * 41, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not summary:
        lines += ["  No crypto data available.", ""]
        return "\n".join(lines)

    # Bitcoin section
    btc = summary.get("bitcoin", {})
    if btc:
        lines.append("  🪙 Bitcoin (BTC)")
        lines.append(f"     USD: ${btc['usd']:,.2f}  {btc['color']} {btc['direction']} {abs(btc['change']):.1f}%")
        lines.append(f"     ZAR: R{btc['zar']:,.0f}  {btc['color']} {btc['direction']} {abs(btc['change']):.1f}%")
        lines.append("")

    # Ethereum section
    eth = summary.get("ethereum", {})
    if eth:
        lines.append("  💎 Ethereum (ETH)")
        lines.append(f"     USD: ${eth['usd']:,.2f}  {eth['color']} {eth['direction']} {abs(eth['change']):.1f}%")
        lines.append(f"     ZAR: R{eth['zar']:,.0f}  {eth['color']} {eth['direction']} {abs(eth['change']):.1f}%")
        lines.append("")

    return "\n".join(lines)


def present_daily_photo(location):
    """PRESENT: Daily exotic location photo."""
    lines = ["--- PHOTO OF THE DAY " + "-" * 39, ""]

    if not location:
        lines += ["  No photo available today.", ""]
        return "\n".join(lines)

    lines.append(f"  🌍 {location['name']}")
    lines.append(f"  {location['description']}")
    lines.append("")
    lines.append(f"  📸 Photo: {location['photo_url']}")
    lines.append("")

    return "\n".join(lines)


def present_daily_riddle(riddle, yesterday_riddle, yesterday_answer):
    """PRESENT: Daily riddle and yesterday's riddle with answer."""
    lines = ["--- DAILY RIDDLE " + "-" * 43, ""]

    if not riddle:
        lines += ["  No riddle available today.", ""]
        return "\n".join(lines)

    # Show today's riddle
    lines.append("  🧩 TODAY'S RIDDLE:")
    lines.append(f"  {riddle['riddle']}")
    lines.append("")

    # Show yesterday's riddle and answer (if available)
    if yesterday_riddle and yesterday_answer:
        lines.append("  💡 YESTERDAY'S RIDDLE:")
        lines.append(f"  {yesterday_riddle}")
        lines.append("")
        lines.append("  ✅ ANSWER:")
        lines.append(f"  {yesterday_answer}")
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
# EMAIL SENDING
# Send the briefing via email
# ============================================================

def send_briefing_email(report_file, report_content, location, riddle, yesterday_riddle, yesterday_answer):
    """
    Email the morning briefing with the report attached.

    PARAMETERS:
    - report_file: Path to the saved briefing file
    - report_content: The formatted report text
    - location: Today's exotic location dict
    - riddle: Today's riddle dict
    - yesterday_riddle: Yesterday's riddle question
    - yesterday_answer: Yesterday's riddle answer

    EMAIL SENDING PROCESS:
    1. Read credentials from .env
    2. Create email with HTML body, embedded photo, and riddle
    3. Connect to Gmail SMTP server
    4. Send email
    5. Handle errors gracefully

    Returns True if successful, False otherwise
    """
    try:
        # Read email configuration from .env
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        email_to = os.getenv('EMAIL_TO', email_user)  # Default to sending to self

        # Check if email is configured
        if not email_user or not email_password:
            print("\n[!] Email not configured (skipping)")
            print("    To enable: Add EMAIL_USER and EMAIL_PASSWORD to .env")
            return False

        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = email_to
        msg['Subject'] = f"📰 Morning Briefing - {datetime.now().strftime('%B %d, %Y')}"

        # Create plain text version (from report content)
        plain_text = report_content

        # Build photo section HTML
        photo_html = ""
        if location:
            photo_html = f"""
            <div style="margin: 30px 0;">
                <h2 style="color: #667eea; margin-bottom: 10px;">🌍 Photo of the Day</h2>
                <h3 style="color: #333; margin: 10px 0 15px 0;">{location['name']}</h3>
                <img src="{location['photo_url']}" alt="{location['name']}" style="width: 100%; max-width: 800px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="color: #666; font-size: 15px; font-style: italic; margin-top: 10px;">{location['description']}</p>
            </div>
            """

        # Build riddle section HTML
        riddle_html = ""
        if riddle:
            yesterday_section = ""
            if yesterday_riddle and yesterday_answer:
                yesterday_section = f"""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #4caf50;">
                    <p style="margin: 0; color: #2e7d32; font-weight: bold;">💡 Yesterday's Riddle:</p>
                    <p style="margin: 10px 0; color: #1b5e20; font-size: 16px; font-style: italic;">{yesterday_riddle}</p>
                    <p style="margin: 10px 0 0 0; color: #2e7d32; font-weight: bold;">✅ Answer:</p>
                    <p style="margin: 10px 0 0 0; color: #1b5e20; font-size: 16px;">{yesterday_answer}</p>
                </div>
                """

            riddle_html = f"""
            <div style="margin: 30px 0;">
                <h2 style="color: #667eea; margin-bottom: 15px;">🧩 Daily Riddle</h2>
                <div style="background-color: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800;">
                    <p style="margin: 0; color: #e65100; font-weight: bold;">Today's Challenge:</p>
                    <p style="margin: 15px 0 0 0; color: #333; font-size: 17px; line-height: 1.6;">{riddle['riddle']}</p>
                </div>
                {yesterday_section}
            </div>
            """

        # Create HTML version (formatted)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h1 style="color: #667eea; margin-top: 0;">📰 Morning Briefing</h1>
                <p style="color: #666; font-size: 16px;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
                <hr style="border: none; border-top: 2px solid #667eea; margin: 20px 0;">

                {photo_html}

                {riddle_html}

                <h2 style="color: #667eea; margin: 30px 0 15px 0;">📊 Your Daily Briefing</h2>
                <pre style="font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.6; background-color: #f8f9fa; padding: 20px; border-radius: 5px; overflow-x: auto;">
{report_content}
                </pre>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Generated by Morning Briefing Bot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """

        # Attach both versions
        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Attach the briefing file
        if report_file.exists():
            with open(report_file, 'rb') as f:
                file_data = f.read()

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file_data)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {report_file.name}'
            )
            msg.attach(part)

        # Connect to Gmail and send
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()  # Upgrade to encrypted connection
            server.login(email_user, email_password)
            server.send_message(msg)

        print(f"\n✉️  Briefing emailed to {email_to}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("\n[!] Email authentication failed")
        print("    Get Gmail App Password: https://myaccount.google.com/apppasswords")
        return False

    except Exception as e:
        print(f"\n[!] Could not send email: {e}")
        return False


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

    # ── LOAD DAILY CONTENT ──────────────────────────────────
    # Get today's exotic location photo and riddle
    print("  [1/4] Loading daily photo and riddle…")
    daily_location, daily_riddle, yesterday_riddle, yesterday_answer = load_daily_content()

    # ── GATHER ──────────────────────────────────────────────
    # Fetch from every API. Errors are captured, not raised,
    # so a failed API call never stops the whole report.
    print("  [2/4] Gathering LIVE data from APIs…")
    raw_weather,   weather_error   = gather_weather()
    raw_news,      news_error      = gather_news()
    raw_currency,  currency_error  = gather_currency()
    raw_crypto,    crypto_error    = gather_crypto()

    # ── PROCESS ─────────────────────────────────────────────
    # Transform raw API data into summaries the presenter can use.
    print("  [3/4] Processing data…")
    weather_summary   = process_weather(raw_weather)
    news_summary      = process_news(raw_news)
    currency_summary  = process_currency(raw_currency)
    crypto_summary    = process_crypto(raw_crypto)

    # ── PRESENT ─────────────────────────────────────────────
    # Assemble each section into one big report string.
    print("  [4/4] Generating report…\n")
    report = "\n".join([
        present_header(),
        present_daily_photo(daily_location),
        present_daily_riddle(daily_riddle, yesterday_riddle, yesterday_answer),
        present_weather(weather_summary,   weather_error),
        present_news(news_summary,         news_error),
        present_currency(currency_summary, currency_error),
        present_crypto(crypto_summary,     crypto_error),
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

        # ── EMAIL ───────────────────────────────────────────────
        # Email the briefing (if email is configured)
        send_briefing_email(REPORT_FILE, report, daily_location, daily_riddle, yesterday_riddle, yesterday_answer)

    except OSError as e:
        print(f"\n[!] Could not save report file: {e}")


if __name__ == "__main__":
    main()
