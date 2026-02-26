#!/bin/bash
# ============================================================
# test_now.sh — Test the Morning Briefing Immediately
#
# WHAT THIS SCRIPT DOES:
# Runs your morning briefing bot RIGHT NOW instead of waiting
# for the scheduled 7:00 AM time. Perfect for testing!
#
# USAGE:
#   ./test_now.sh
#
# WHY THIS IS USEFUL:
# - Test that your bot works before scheduling it
# - Verify API keys are configured correctly
# - See what the output looks like
# - Debug any issues immediately
#
# This is just a convenient wrapper around:
#   python3 morning_briefing.py
# ============================================================

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================
# HEADER
# ============================================================

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  TESTING MORNING BRIEFING BOT${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${YELLOW}Running briefing NOW (not waiting for 7:00 AM)...${NC}"
echo ""

# ============================================================
# RUN THE BRIEFING
# ============================================================

cd "$SCRIPT_DIR"

# Run the briefing and capture the exit code
if python3 morning_briefing.py; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

echo ""

# ============================================================
# SHOW RESULTS
# ============================================================

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  ✓ TEST SUCCESSFUL${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo "Your morning briefing bot is working correctly!"
    echo ""

    # Show the generated file
    TODAY=$(date +%Y-%m-%d)
    REPORT_FILE="morning_briefing_$TODAY.txt"

    if [ -f "$REPORT_FILE" ]; then
        echo "Report saved to: $REPORT_FILE"
        echo ""
        echo "To view the file:"
        echo "  cat $REPORT_FILE"
        echo ""
    fi

    echo "Ready to schedule!"
    echo "  • For launchd:  ./install.sh launchd"
    echo "  • For Python:   ./install.sh python"
    echo ""

else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}  ✗ TEST FAILED (Exit code: $EXIT_CODE)${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    echo "The briefing bot encountered an error."
    echo ""
    echo "Common issues:"
    echo "  1. Missing API key: Check your .env file has NEWS_API_KEY"
    echo "  2. Network error: Check your internet connection"
    echo "  3. Missing library: Run 'pip3 install requests python-dotenv'"
    echo ""
    echo "To debug:"
    echo "  • Check error messages above"
    echo "  • Run manually: python3 morning_briefing.py"
    echo "  • Verify .env file: cat .env"
    echo ""
    exit 1
fi
