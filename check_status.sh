#!/bin/bash
# ============================================================
# check_status.sh — Check Scheduler Status
#
# WHAT THIS SCRIPT DOES:
# Shows whether your morning briefing scheduler is running
# and when the next execution is scheduled.
#
# USAGE:
#   ./check_status.sh launchd   Check launchd status
#   ./check_status.sh python    Check Python scheduler status
#   ./check_status.sh           Check both
# ============================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/scheduler.pid"
LABEL="com.morningbot.briefing"

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  SCHEDULER STATUS CHECK${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

# ============================================================
# CHECK LAUNCHD STATUS
# ============================================================

check_launchd() {
    echo -e "${YELLOW}━━━ LAUNCHD STATUS (Method 1) ━━━${NC}"
    echo ""

    # Check if the job is loaded
    if launchctl list | grep -q "$LABEL"; then
        echo -e "${GREEN}✓ launchd job is LOADED and ACTIVE${NC}"
        echo ""

        # Show job details
        echo "Job details:"
        launchctl list | grep "$LABEL"
        echo ""

        # Show next run time (launchd doesn't easily expose this, so we show schedule)
        echo "Scheduled time: Daily at 7:00 AM"
        echo ""

        # Check recent logs
        if [ -f "$SCRIPT_DIR/logs/briefing_output.log" ]; then
            echo "Most recent execution:"
            tail -n 5 "$SCRIPT_DIR/logs/briefing_output.log" | head -n 3
            echo ""
        fi

        # Show log locations
        echo "Logs:"
        echo "  → $SCRIPT_DIR/logs/briefing_output.log"
        echo "  → $SCRIPT_DIR/logs/briefing_error.log"
        echo ""

    else
        echo -e "${RED}✗ launchd job is NOT loaded${NC}"
        echo ""
        echo "To install: ./install.sh launchd"
        echo ""
    fi
}

# ============================================================
# CHECK PYTHON SCHEDULER STATUS
# ============================================================

check_python() {
    echo -e "${YELLOW}━━━ PYTHON SCHEDULER STATUS (Method 2) ━━━${NC}"
    echo ""

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")

        # Check if the process is actually running
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Python scheduler is RUNNING${NC}"
            echo ""
            echo "Process ID: $PID"
            echo ""

            # Show process info
            echo "Process details:"
            ps -p "$PID" -o pid,etime,command | tail -n 1
            echo ""

            # Show recent scheduler logs
            if [ -f "$SCRIPT_DIR/logs/scheduler.log" ]; then
                echo "Recent scheduler activity:"
                tail -n 10 "$SCRIPT_DIR/logs/scheduler.log" | grep -E "(Next run|Starting scheduled)" | tail -n 3
                echo ""
            fi

            # Show log location
            echo "Logs:"
            echo "  → $SCRIPT_DIR/logs/scheduler.log"
            echo ""

        else
            echo -e "${RED}✗ Python scheduler is NOT running${NC}"
            echo "  (PID file exists but process $PID is dead)"
            echo ""
            echo "To restart: ./install.sh python"
            echo ""
        fi
    else
        echo -e "${RED}✗ Python scheduler is NOT running${NC}"
        echo "  (No PID file found)"
        echo ""
        echo "To install: ./install.sh python"
        echo ""
    fi
}

# ============================================================
# SHOW RECENT BRIEFINGS
# ============================================================

show_recent_briefings() {
    echo -e "${YELLOW}━━━ RECENT BRIEFING FILES ━━━${NC}"
    echo ""

    # Find the most recent briefing files
    BRIEFING_FILES=$(ls -t "$SCRIPT_DIR"/morning_briefing_*.txt 2>/dev/null | head -n 3)

    if [ -n "$BRIEFING_FILES" ]; then
        echo "Recent briefings generated:"
        for file in $BRIEFING_FILES; do
            FILENAME=$(basename "$file")
            SIZE=$(ls -lh "$file" | awk '{print $5}')
            TIMESTAMP=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d. -f1)
            echo "  • $FILENAME ($SIZE) — $TIMESTAMP"
        done
        echo ""
    else
        echo "No briefing files found yet."
        echo ""
    fi
}

# ============================================================
# MAIN LOGIC
# ============================================================

print_header

METHOD=$1

if [ -z "$METHOD" ]; then
    # No method specified, check both
    check_launchd
    echo ""
    check_python
    echo ""
    show_recent_briefings
elif [ "$METHOD" = "launchd" ]; then
    check_launchd
    show_recent_briefings
elif [ "$METHOD" = "python" ]; then
    check_python
    show_recent_briefings
else
    echo -e "${RED}Unknown method: $METHOD${NC}"
    echo ""
    echo "USAGE:"
    echo "  ./check_status.sh          Check all methods"
    echo "  ./check_status.sh launchd  Check launchd only"
    echo "  ./check_status.sh python   Check Python scheduler only"
    echo ""
    exit 1
fi

echo -e "${BLUE}============================================================${NC}"
echo ""
