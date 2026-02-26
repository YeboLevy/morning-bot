#!/usr/bin/env python3
# ============================================================
# scheduler.py — Portable Python-Based Task Scheduler
#
# WHAT THIS IS:
# An alternative to launchd that runs your morning briefing
# using pure Python. This script runs continuously in the
# background and executes your bot at 7:00 AM every day.
#
# WHY USE THIS INSTEAD OF LAUNCHD?
# - Cross-platform (works on Windows, Linux, macOS)
# - Easier to understand (just Python, no XML)
# - Great for development and testing
# - More flexible (can run every 5 min, every hour, etc.)
#
# HOW IT WORKS:
# 1. This script starts and runs forever
# 2. Every second, it checks: "Is it time to run yet?"
# 3. When the clock hits 7:00 AM, it runs morning_briefing.py
# 4. After running, it waits until tomorrow at 7:00 AM
# 5. Repeat forever (or until you stop it)
#
# SCHEDULING LIBRARY:
# We use the `schedule` library, which makes scheduling
# incredibly simple compared to cron syntax.
#
# Install: pip install schedule
#
# RUNNING IN BACKGROUND:
# - macOS/Linux: nohup python3 scheduler.py &
# - Or use the install.sh script which sets this up
#
# ============================================================

import schedule
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================
# LOGGING SETUP
# Logging lets us track what happened even when the script
# runs in the background where we can't see print() output.
#
# Logs are saved to: logs/scheduler.log
# ============================================================

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
# - Level INFO: Log normal operations (DEBUG would be too verbose)
# - Format: timestamp, log level, message
# - Handlers: Write to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        # Write to file (appends, doesn't overwrite)
        logging.FileHandler(LOGS_DIR / "scheduler.log"),
        # Also print to console (useful when testing)
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================
# PATH CONFIGURATION
# ============================================================

# Get the directory where this script lives
SCRIPT_DIR = Path(__file__).parent

# Path to the morning briefing script
BRIEFING_SCRIPT = SCRIPT_DIR / "morning_briefing.py"

# ============================================================
# JOB FUNCTION — What to run at the scheduled time
# ============================================================

def run_morning_briefing():
    """
    Execute the morning briefing bot.

    This function is called by the scheduler at 7:00 AM.
    It runs morning_briefing.py as a subprocess and logs
    the result (success or failure).

    SUBPROCESS EXPLAINED:
    subprocess.run() executes another program from Python.
    It's like typing a command in the terminal, but from code.

    Parameters:
    - args: The command to run (python3 + script path)
    - capture_output: Save stdout/stderr to result object
    - text: Return output as string (not bytes)
    - check: Raise exception if command fails

    Returns: CompletedProcess object with:
    - returncode: 0 = success, non-zero = error
    - stdout: Normal output
    - stderr: Error messages
    """
    logger.info("=" * 60)
    logger.info("Starting scheduled morning briefing...")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run the briefing script
        # subprocess.run() waits for the script to finish before continuing
        result = subprocess.run(
            ["python3", str(BRIEFING_SCRIPT)],
            capture_output=True,  # Capture stdout and stderr
            text=True,            # Return strings (not bytes)
            check=True,           # Raise exception if script fails
            cwd=SCRIPT_DIR,       # Run from the morning-bot directory
        )

        # Log success
        logger.info("✓ Morning briefing completed successfully!")

        # Log the output (first 500 chars to avoid huge logs)
        if result.stdout:
            output_preview = result.stdout[:500]
            logger.info(f"Output preview: {output_preview}...")

    except subprocess.CalledProcessError as e:
        # Script ran but returned non-zero exit code (error)
        logger.error(f"✗ Morning briefing failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")

    except FileNotFoundError:
        # Script file doesn't exist
        logger.error(f"✗ Could not find briefing script: {BRIEFING_SCRIPT}")

    except Exception as e:
        # Any other unexpected error
        logger.error(f"✗ Unexpected error running briefing: {e}")

    logger.info("=" * 60)
    logger.info("")  # Blank line for readability


# ============================================================
# SCHEDULING CONFIGURATION
# ============================================================

def setup_schedule():
    """
    Configure the schedule for running tasks.

    The `schedule` library uses a fluent, English-like syntax:
    - schedule.every().day.at("07:00").do(function)
    - schedule.every(5).minutes.do(function)
    - schedule.every().monday.at("09:00").do(function)
    - schedule.every().hour.do(function)

    More examples:
    - schedule.every(10).seconds.do(job)  # Every 10 seconds
    - schedule.every().hour.do(job)        # Every hour
    - schedule.every().day.at("10:30").do(job)  # Daily at 10:30 AM
    - schedule.every().monday.do(job)      # Every Monday at 00:00
    - schedule.every().wednesday.at("13:15").do(job)  # Wed 1:15 PM
    """
    # Schedule the briefing to run every day at 7:00 AM
    schedule.every().day.at("07:00").do(run_morning_briefing)

    logger.info("Scheduler initialized!")
    logger.info("Morning briefing scheduled for 7:00 AM daily")
    logger.info("Press Ctrl+C to stop the scheduler")
    logger.info("")

    # Show next scheduled run
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"Next run scheduled for: {next_run}")
    logger.info("")


# ============================================================
# MAIN LOOP — Keep the scheduler running forever
# ============================================================

def run_scheduler():
    """
    Main loop that keeps the scheduler alive.

    HOW SCHEDULING WORKS:
    1. schedule.run_pending() checks if any jobs are due
    2. If a job is scheduled for now, it executes it
    3. If not, it does nothing
    4. time.sleep(60) pauses for 60 seconds
    5. Loop repeats forever (until Ctrl+C or script is killed)

    WHY SLEEP 60 SECONDS?
    - We only need minute-level precision (not second-level)
    - Checking every second would waste CPU
    - 60 seconds is perfect for daily tasks at specific times
    - For tasks that need second precision, use sleep(1)

    GRACEFUL SHUTDOWN:
    The try/except block catches Ctrl+C (KeyboardInterrupt)
    and logs a clean shutdown message instead of an error.
    """
    setup_schedule()

    try:
        while True:
            # Check if any scheduled tasks are due to run
            schedule.run_pending()

            # Sleep for 60 seconds before checking again
            # (We don't need second-level precision for a daily 7 AM task)
            time.sleep(60)

    except KeyboardInterrupt:
        # User pressed Ctrl+C to stop the scheduler
        logger.info("")
        logger.info("Scheduler stopped by user (Ctrl+C)")
        logger.info("Goodbye!")

    except Exception as e:
        # Unexpected error in the main loop
        logger.error(f"Scheduler crashed with error: {e}")
        raise  # Re-raise so we can debug it


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    """
    This block runs when you execute: python3 scheduler.py

    It doesn't run if this file is imported as a module.
    This is a Python best practice.
    """
    # Log startup message
    logger.info("=" * 60)
    logger.info("MORNING BRIEFING SCHEDULER STARTING")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    logger.info("")

    # Start the scheduler loop
    run_scheduler()
