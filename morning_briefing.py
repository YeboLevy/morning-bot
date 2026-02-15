# ============================================================
# morning_briefing.py — A Morning Briefing Bot
#
# BOT PATTERN: A bot is a program that runs automatically,
# gathers information from multiple sources, and presents
# a useful summary — without you having to do anything.
#
# This bot follows three clear steps every time it runs:
#
#   GATHER  → Read raw data from files (expenses, meetings, journal)
#   PROCESS → Transform raw data into useful summaries
#   PRESENT → Format everything into a beautiful report
#
# Run it each morning with: python morning_briefing.py
# ============================================================

import os
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env so we can use variables like USER_NAME ────────
# python-dotenv reads the .env file and injects its key=value
# pairs into the environment so os.getenv() can find them.
load_dotenv()

# ============================================================
# CONFIGURATION
# One place to change file paths if anything moves.
# ============================================================

BASE_DIR       = Path.home() / "Desktop" / "Learning To Code"
EXPENSE_FILE   = BASE_DIR / "expense-tracker"  / "expenses.csv"
MEETINGS_FILE  = BASE_DIR / "meeting-planner"  / "meetings.json"
JOURNAL_FILE   = BASE_DIR / "daily-journal"    / "journal.json"

TODAY          = datetime.now().date()
TODAY_STR      = TODAY.strftime("%Y-%m-%d")
REPORT_FILE    = Path(__file__).parent / f"morning_briefing_{TODAY_STR}.txt"

# ============================================================
# STEP 1 — GATHER
# Each gather_* function opens one data source and returns:
#   (data, error_message)
# If the file is missing or broken, data is empty and
# error_message explains what went wrong — so the rest of
# the bot keeps running instead of crashing.
# ============================================================

def gather_expenses():
    """GATHER: Read all rows from expenses.csv into a list of dicts."""
    try:
        expenses = []
        with open(EXPENSE_FILE, newline="") as f:
            for row in csv.DictReader(f):
                expenses.append({
                    "date":        row["date"],
                    "category":    row["category"],
                    "amount":      float(row["amount"]),   # convert string → number
                    "description": row["description"],
                })
        return expenses, None
    except FileNotFoundError:
        return [], f"File not found: {EXPENSE_FILE}"
    except Exception as e:
        return [], f"Could not read expenses: {e}"


def gather_meetings():
    """GATHER: Read meetings.json and parse ISO 8601 datetimes."""
    try:
        with open(MEETINGS_FILE) as f:
            raw_list = json.load(f)

        meetings = []
        for raw in raw_list:
            meetings.append({
                "title":            raw["title"],
                # fromisoformat() converts "2026-02-15T14:00:00+00:00" → datetime object
                "start":            datetime.fromisoformat(raw["start"]),
                "duration_minutes": raw["duration_minutes"],
                "notes":            raw.get("notes", ""),
            })
        return meetings, None
    except FileNotFoundError:
        return [], f"File not found: {MEETINGS_FILE}"
    except Exception as e:
        return [], f"Could not read meetings: {e}"


def gather_journal():
    """GATHER: Read journal.json into a list of entry dicts."""
    try:
        with open(JOURNAL_FILE) as f:
            entries = json.load(f)
        return entries, None
    except FileNotFoundError:
        return [], f"File not found: {JOURNAL_FILE}"
    except Exception as e:
        return [], f"Could not read journal: {e}"


# ============================================================
# STEP 2 — PROCESS
# Each process_* function takes raw gathered data and computes
# something useful from it: totals, filters, counts, trends.
# Pure calculation — no file I/O, no printing here.
# ============================================================

def process_expenses(expenses):
    """PROCESS: Summarise spending for the current month."""
    if not expenses:
        return None

    # Keep only entries from this calendar month
    current_month = TODAY.strftime("%Y-%m")
    monthly = [e for e in expenses if e["date"].startswith(current_month)]

    if not monthly:
        return None

    total = sum(e["amount"] for e in monthly)

    # Group spending by category
    by_category = defaultdict(float)
    for e in monthly:
        by_category[e["category"]] += e["amount"]

    # Sort categories highest → lowest
    sorted_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)

    # Most recent three expenses (sorted by date, newest first)
    recent = sorted(expenses, key=lambda x: x["date"], reverse=True)[:3]

    return {
        "total":          total,
        "by_category":    sorted_categories,
        "recent":         recent,
        "count":          len(monthly),
    }


def process_meetings(meetings):
    """PROCESS: Filter meetings to today and compute end times."""
    today_meetings = []
    for m in meetings:
        # Convert UTC datetime to local system timezone before comparing dates
        local_start = m["start"].astimezone()
        if local_start.date() == TODAY:
            end_time = local_start + timedelta(minutes=m["duration_minutes"])
            today_meetings.append({
                "title":            m["title"],
                "start":            local_start,
                "end":              end_time,
                "duration_minutes": m["duration_minutes"],
                "notes":            m["notes"],
            })

    # Earliest meeting first
    today_meetings.sort(key=lambda x: x["start"])
    return today_meetings


def process_journal(entries):
    """PROCESS: Count moods and build a 7-day trend."""
    if not entries:
        return None

    # Only include entries from the last 7 days
    cutoff = TODAY - timedelta(days=7)
    recent = []
    for e in entries:
        try:
            entry_date = datetime.strptime(e["date"], "%Y-%m-%d %H:%M").date()
            if entry_date >= cutoff:
                recent.append({
                    "date":  entry_date,
                    "mood":  e["mood"],
                    "text":  e.get("text", ""),
                })
        except ValueError:
            continue  # skip any entry with an unexpected date format

    if not recent:
        return None

    # Count how many times each mood appears
    mood_counts = defaultdict(int)
    for e in recent:
        mood_counts[e["mood"]] += 1

    dominant_mood = max(mood_counts, key=mood_counts.get)

    # Sort newest → oldest for display
    recent.sort(key=lambda x: x["date"], reverse=True)

    return {
        "entries":       recent,
        "mood_counts":   dict(mood_counts),
        "dominant_mood": dominant_mood,
        "total_entries": len(recent),
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


def present_expenses(summary, error):
    """PRESENT: Spending summary with category bars and recent transactions."""
    lines = ["--- SPENDING SUMMARY " + "-" * 39, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not summary:
        lines += ["  No expense data found for this month.", ""]
        return "\n".join(lines)

    lines.append(
        f"  Month-to-date total:  ${summary['total']:.2f}"
        f"  ({summary['count']} transactions)"
    )
    lines.append("")
    lines.append("  By category:")

    for category, amount in summary["by_category"]:
        # Simple ASCII bar proportional to share of spending
        share   = amount / summary["total"] if summary["total"] else 0
        bar     = "#" * int(share * 24)
        lines.append(f"    {category:<14} ${amount:>8.2f}  [{bar:<24}]")

    lines.append("")
    lines.append("  Recent transactions:")
    for e in summary["recent"]:
        lines.append(
            f"    {e['date']}  {e['category']:<14}"
            f"  ${e['amount']:>7.2f}  {e['description']}"
        )

    lines.append("")
    return "\n".join(lines)


def present_meetings(today_meetings, error):
    """PRESENT: Today's meetings with times, duration and notes."""
    lines = ["--- TODAY'S MEETINGS " + "-" * 39, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not today_meetings:
        lines += ["  No meetings scheduled today. Enjoy the clear calendar!", ""]
        return "\n".join(lines)

    count = len(today_meetings)
    lines.append(f"  {count} meeting{'s' if count != 1 else ''} today:")
    lines.append("")

    for i, m in enumerate(today_meetings, 1):
        start_str = m["start"].strftime("%I:%M %p")
        end_str   = m["end"].strftime("%I:%M %p")
        lines.append(f"  {i}.  {m['title']}")
        lines.append(f"       {start_str} – {end_str}  ({m['duration_minutes']} min)")
        if m["notes"]:
            lines.append(f"       Notes: {m['notes']}")
        lines.append("")

    return "\n".join(lines)


def present_journal(analysis, error):
    """PRESENT: 7-day mood trend with a bar chart and recent entry snippets."""
    lines = ["--- MOOD TREND (Last 7 Days) " + "-" * 31, ""]

    if error:
        lines += [f"  [!] {error}", ""]
        return "\n".join(lines)

    if not analysis:
        lines += ["  No journal entries found in the last 7 days.", ""]
        return "\n".join(lines)

    lines.append(f"  Entries this week:  {analysis['total_entries']}")
    lines.append(f"  Dominant mood:      {analysis['dominant_mood'].upper()}")
    lines.append("")
    lines.append("  Mood breakdown:")

    for mood in ["happy", "neutral", "sad"]:
        count = analysis["mood_counts"].get(mood, 0)
        bar   = "*" * count
        lines.append(f"    {mood:<8}  {bar:<10}  ({count})")

    lines.append("")
    lines.append("  Recent entries:")

    for e in analysis["entries"][:5]:   # show up to 5 most recent
        date_str = e["date"].strftime("%b %d")
        snippet  = e["text"][:52] + "..." if len(e["text"]) > 52 else e["text"]
        lines.append(f"    {date_str}  [{e['mood']:<7}]  {snippet}")

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
#   GATHER   → collect raw data (may fail gracefully)
#   PROCESS  → compute summaries from raw data
#   PRESENT  → format summaries into a human-readable report
#   SAVE     → write report to a dated .txt file
# ============================================================

def main():
    print("Starting Morning Briefing Bot…\n")

    # ── GATHER ──────────────────────────────────────────────
    # Read every data source. Errors are captured, not raised,
    # so a missing file never stops the whole report.
    print("  [1/3] Gathering data…")
    raw_expenses,  expense_error  = gather_expenses()
    raw_meetings,  meeting_error  = gather_meetings()
    raw_journal,   journal_error  = gather_journal()

    # ── PROCESS ─────────────────────────────────────────────
    # Transform raw data into summaries the presenter can use.
    print("  [2/3] Processing data…")
    expense_summary  = process_expenses(raw_expenses)
    todays_meetings  = process_meetings(raw_meetings)
    mood_analysis    = process_journal(raw_journal)

    # ── PRESENT ─────────────────────────────────────────────
    # Assemble each section into one big report string.
    print("  [3/3] Generating report…\n")
    report = "\n".join([
        present_header(),
        present_expenses(expense_summary,  expense_error),
        present_meetings(todays_meetings,  meeting_error),
        present_journal(mood_analysis,     journal_error),
        present_footer(),
    ])

    # Print to terminal
    print(report)

    # ── SAVE ────────────────────────────────────────────────
    # Write the same report to a dated text file.
    try:
        with open(REPORT_FILE, "w") as f:
            f.write(report)
        print(f"\nReport saved → {REPORT_FILE}")
    except OSError as e:
        print(f"\n[!] Could not save report file: {e}")


if __name__ == "__main__":
    main()
