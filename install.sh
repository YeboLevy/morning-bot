#!/bin/bash
# ============================================================
# install.sh — Install the Morning Briefing Scheduler
#
# WHAT THIS SCRIPT DOES:
# Sets up automated daily execution of your morning briefing
# bot using your choice of launchd (Method 1) or Python
# scheduler (Method 2).
#
# USAGE:
#   ./install.sh launchd    → Install using macOS launchd
#   ./install.sh python     → Install using Python scheduler
#   ./install.sh            → Show usage help
#
# BASH SCRIPT BASICS:
# - #!/bin/bash → Tells system to run this with bash shell
# - $1, $2 → Command line arguments ($1 = first arg)
# - echo → Print to terminal
# - exit 0 → Exit successfully, exit 1 → Exit with error
# - if/elif/else → Conditional logic
# - mkdir -p → Create directory (and parents if needed)
# ============================================================

set -e  # Exit immediately if any command fails (safety!)

# Colors for pretty output (ANSI escape codes)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script lives
# ${BASH_SOURCE[0]} = path to this script
# dirname = extract directory part
# cd + pwd = convert to absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# File paths
PLIST_FILE="$SCRIPT_DIR/com.morningbot.briefing.plist"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCHAGENTS_DIR/com.morningbot.briefing.plist"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  MORNING BRIEFING BOT — INSTALLATION${NC}"
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
# METHOD 1: Install using macOS launchd
# ============================================================

install_launchd() {
    echo -e "${BLUE}Installing with launchd (Method 1)...${NC}"
    echo ""

    # Step 1: Create LaunchAgents directory if it doesn't exist
    print_info "Creating LaunchAgents directory..."
    mkdir -p "$LAUNCHAGENTS_DIR"
    print_success "Directory ready: $LAUNCHAGENTS_DIR"
    echo ""

    # Step 2: Create logs directory
    print_info "Creating logs directory..."
    mkdir -p "$SCRIPT_DIR/logs"
    print_success "Logs directory created"
    echo ""

    # Step 3: Copy .plist file to LaunchAgents
    print_info "Installing launchd configuration..."
    cp "$PLIST_FILE" "$INSTALLED_PLIST"
    print_success "Copied to: $INSTALLED_PLIST"
    echo ""

    # Step 4: Load the job into launchd
    print_info "Loading job into launchd..."
    launchctl load "$INSTALLED_PLIST"
    print_success "Job loaded successfully!"
    echo ""

    # Success message
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  ✓ INSTALLATION COMPLETE (launchd)${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo "Your morning briefing will run automatically at 7:00 AM daily."
    echo ""
    echo "Useful commands:"
    echo "  • Check status:  ./check_status.sh launchd"
    echo "  • Test now:      ./test_now.sh"
    echo "  • View logs:     tail -f logs/briefing_output.log"
    echo "  • Uninstall:     ./uninstall.sh launchd"
    echo ""
    echo "Logs will be saved to:"
    echo "  → $SCRIPT_DIR/logs/briefing_output.log"
    echo "  → $SCRIPT_DIR/logs/briefing_error.log"
    echo ""
}

# ============================================================
# METHOD 2: Install using Python scheduler
# ============================================================

install_python() {
    echo -e "${BLUE}Installing with Python scheduler (Method 2)...${NC}"
    echo ""

    # Step 1: Check if schedule library is installed
    print_info "Checking for 'schedule' library..."
    if python3 -c "import schedule" 2>/dev/null; then
        print_success "schedule library already installed"
    else
        print_info "Installing schedule library..."
        pip3 install schedule
        print_success "schedule library installed"
    fi
    echo ""

    # Step 2: Create logs directory
    print_info "Creating logs directory..."
    mkdir -p "$SCRIPT_DIR/logs"
    print_success "Logs directory created"
    echo ""

    # Step 3: Make scheduler.py executable
    print_info "Making scheduler.py executable..."
    chmod +x "$SCRIPT_DIR/scheduler.py"
    print_success "Permissions set"
    echo ""

    # Step 4: Create a launch script that keeps the scheduler running
    print_info "Creating background launcher..."

    LAUNCHER_SCRIPT="$SCRIPT_DIR/run_scheduler_background.sh"
    cat > "$LAUNCHER_SCRIPT" << 'EOF'
#!/bin/bash
# Auto-generated launcher for Python scheduler
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run scheduler in background, redirect output to log
nohup python3 scheduler.py >> logs/scheduler.log 2>&1 &

# Save the process ID (PID) so we can stop it later
echo $! > scheduler.pid

echo "Scheduler started in background (PID: $!)"
echo "Logs: $SCRIPT_DIR/logs/scheduler.log"
EOF

    chmod +x "$LAUNCHER_SCRIPT"
    print_success "Launcher created: run_scheduler_background.sh"
    echo ""

    # Step 5: Start the scheduler
    print_info "Starting scheduler in background..."
    "$LAUNCHER_SCRIPT"
    sleep 1  # Give it a moment to start

    if [ -f "$SCRIPT_DIR/scheduler.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/scheduler.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_success "Scheduler running (PID: $PID)"
        else
            print_error "Scheduler failed to start"
            exit 1
        fi
    fi
    echo ""

    # Success message
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  ✓ INSTALLATION COMPLETE (Python scheduler)${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo "Your morning briefing will run at 7:00 AM daily."
    echo ""
    echo "Useful commands:"
    echo "  • Check status:  ./check_status.sh python"
    echo "  • Test now:      ./test_now.sh"
    echo "  • View logs:     tail -f logs/scheduler.log"
    echo "  • Uninstall:     ./uninstall.sh python"
    echo ""
    echo "⚠️  Note: The Python scheduler stops if you restart your Mac."
    echo "   Run './install.sh python' again after reboot, or use launchd."
    echo ""
}

# ============================================================
# USAGE HELP
# ============================================================

show_usage() {
    print_header
    echo "This script installs automated scheduling for your morning briefing bot."
    echo ""
    echo "USAGE:"
    echo "  ./install.sh launchd    Install using macOS launchd (recommended)"
    echo "  ./install.sh python     Install using Python scheduler (portable)"
    echo ""
    echo "METHODS:"
    echo ""
    echo "  launchd (Method 1) — macOS native, production-ready"
    echo "    ✓ Runs automatically even after reboot"
    echo "    ✓ Apple's recommended scheduling system"
    echo "    ✓ Set it and forget it"
    echo ""
    echo "  python (Method 2) — Cross-platform, development-friendly"
    echo "    ✓ Works on any OS (macOS, Linux, Windows)"
    echo "    ✓ Easy to understand and modify"
    echo "    ✗ Stops if computer restarts"
    echo ""
    echo "RECOMMENDATION: Use launchd for daily use, python for testing."
    echo ""
}

# ============================================================
# MAIN SCRIPT LOGIC
# ============================================================

print_header

# Check command line argument
METHOD=$1

if [ -z "$METHOD" ]; then
    # No argument provided
    show_usage
    exit 0
fi

case "$METHOD" in
    launchd)
        install_launchd
        ;;
    python)
        install_python
        ;;
    *)
        print_error "Unknown method: $METHOD"
        echo ""
        show_usage
        exit 1
        ;;
esac
