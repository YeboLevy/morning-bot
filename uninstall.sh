#!/bin/bash
# ============================================================
# uninstall.sh — Remove the Morning Briefing Scheduler
#
# WHAT THIS SCRIPT DOES:
# Safely removes the automated scheduler (launchd or Python)
# and stops any running background processes.
#
# USAGE:
#   ./uninstall.sh launchd  → Remove launchd configuration
#   ./uninstall.sh python   → Stop Python scheduler
#   ./uninstall.sh all      → Remove everything
# ============================================================

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLED_PLIST="$HOME/Library/LaunchAgents/com.morningbot.briefing.plist"
PID_FILE="$SCRIPT_DIR/scheduler.pid"

# Helper functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  MORNING BRIEFING BOT — UNINSTALLATION${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# ============================================================
# UNINSTALL LAUNCHD
# ============================================================

uninstall_launchd() {
    echo -e "${BLUE}Uninstalling launchd scheduler...${NC}"
    echo ""

    if [ -f "$INSTALLED_PLIST" ]; then
        # Unload the job from launchd (stops it from running)
        print_info "Unloading from launchd..."
        launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
        print_success "Job unloaded"
        echo ""

        # Remove the .plist file
        print_info "Removing configuration file..."
        rm "$INSTALLED_PLIST"
        print_success "Configuration removed"
        echo ""

        echo -e "${GREEN}✓ launchd scheduler uninstalled successfully${NC}"
    else
        print_info "launchd scheduler is not installed (nothing to remove)"
    fi
    echo ""
}

# ============================================================
# UNINSTALL PYTHON SCHEDULER
# ============================================================

uninstall_python() {
    echo -e "${BLUE}Stopping Python scheduler...${NC}"
    echo ""

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        print_info "Found scheduler process (PID: $PID)"

        # Check if process is actually running
        if ps -p "$PID" > /dev/null 2>&1; then
            print_info "Stopping scheduler..."
            kill "$PID"
            sleep 1  # Give it time to shut down gracefully

            # Force kill if it's still running
            if ps -p "$PID" > /dev/null 2>&1; then
                print_info "Force stopping..."
                kill -9 "$PID" 2>/dev/null || true
            fi

            print_success "Scheduler stopped"
        else
            print_info "Scheduler process not running"
        fi

        # Remove PID file
        rm "$PID_FILE"
        print_success "PID file removed"
    else
        print_info "No scheduler PID file found (already stopped or never started)"
    fi
    echo ""

    # Remove background launcher if it exists
    if [ -f "$SCRIPT_DIR/run_scheduler_background.sh" ]; then
        print_info "Removing background launcher..."
        rm "$SCRIPT_DIR/run_scheduler_background.sh"
        print_success "Launcher removed"
        echo ""
    fi

    echo -e "${GREEN}✓ Python scheduler uninstalled successfully${NC}"
    echo ""
}

# ============================================================
# USAGE HELP
# ============================================================

show_usage() {
    print_header
    echo "This script removes the automated scheduler."
    echo ""
    echo "USAGE:"
    echo "  ./uninstall.sh launchd   Remove launchd scheduler"
    echo "  ./uninstall.sh python    Stop Python scheduler"
    echo "  ./uninstall.sh all       Remove everything"
    echo ""
    echo "This will stop your morning briefing from running automatically."
    echo "You can reinstall anytime with ./install.sh"
    echo ""
}

# ============================================================
# MAIN LOGIC
# ============================================================

print_header

METHOD=$1

if [ -z "$METHOD" ]; then
    show_usage
    exit 0
fi

case "$METHOD" in
    launchd)
        uninstall_launchd
        ;;
    python)
        uninstall_python
        ;;
    all)
        uninstall_launchd
        uninstall_python
        echo -e "${GREEN}============================================================${NC}"
        echo -e "${GREEN}  ✓ ALL SCHEDULERS REMOVED${NC}"
        echo -e "${GREEN}============================================================${NC}"
        echo ""
        ;;
    *)
        print_error "Unknown method: $METHOD"
        echo ""
        show_usage
        exit 1
        ;;
esac

echo "Your morning briefing bot is still installed, just not scheduled."
echo "To run it manually: python3 morning_briefing.py"
echo ""
