# 🤖 Morning Briefing Bot — Automation Guide

## Quick Start

```bash
# Test that your bot works
./test_now.sh

# Install automated scheduling (choose one method)
./install.sh launchd    # macOS native (recommended)
./install.sh python     # Portable Python scheduler

# Check if it's running
./check_status.sh

# Stop it (if needed)
./uninstall.sh launchd  # or python
```

---

## 📚 What You've Built

You now have **two complete scheduling systems** for your morning briefing bot:

### METHOD 1: launchd (macOS Native)
- ✅ **Production-ready** — Set it and forget it
- ✅ **Survives reboots** — Runs automatically when Mac starts
- ✅ **Apple recommended** — Native macOS scheduling
- ✅ **Better than cron** — Catches up on missed runs
- 📄 Configuration: `com.morningbot.briefing.plist`

### METHOD 2: Python Scheduler
- ✅ **Cross-platform** — Works on macOS, Linux, Windows
- ✅ **Easy to understand** — Pure Python, no XML
- ✅ **Flexible** — Easy to change schedule (every hour, etc.)
- ⚠️ **Stops on reboot** — Need to restart manually
- 📄 Script: `scheduler.py`

---

## 📖 Learning Concepts

### What is Task Scheduling?

**Task scheduling** = Telling your computer to run a program at specific times automatically.

**Real-world examples:**
- Backups running at 2:00 AM every night
- Weekly reports sent every Monday morning
- Security scans running every weekend
- **Your morning briefing at 7:00 AM!**

### Why Bots Need Automation

A bot that requires manual execution isn't really a "bot" — it's just a script.

**True bots:**
- ⏰ Run on a schedule (no human intervention)
- 📊 Gather fresh data automatically
- 💾 Store results for later review
- 🔁 Repeat forever until told to stop

Your morning briefing bot is now a **true bot**!

---

## 🛠️ Complete File Overview

### Core Bot Files
| File | Purpose |
|------|---------|
| `morning_briefing.py` | Main bot (fetches APIs, generates report) |
| `.env` | API keys and configuration |
| `SCHEDULING_GUIDE.md` | Educational guide to scheduling concepts |

### Method 1: launchd Files
| File | Purpose |
|------|---------|
| `com.morningbot.briefing.plist` | launchd configuration (XML) |
| Runs at: | 7:00 AM daily via macOS launchd system |

### Method 2: Python Scheduler Files
| File | Purpose |
|------|---------|
| `scheduler.py` | Python-based scheduler (runs continuously) |
| `run_scheduler_background.sh` | Auto-generated launcher script |
| `scheduler.pid` | Process ID file (tracking running scheduler) |

### Management Scripts
| Script | Purpose |
|--------|---------|
| `install.sh` | Install automated scheduling |
| `uninstall.sh` | Remove automated scheduling |
| `check_status.sh` | Check if scheduler is running |
| `test_now.sh` | Run briefing immediately for testing |

### Logs
| Log File | Contains |
|----------|----------|
| `logs/briefing_output.log` | Normal output from bot (launchd) |
| `logs/briefing_error.log` | Errors from bot (launchd) |
| `logs/scheduler.log` | Python scheduler activity log |
| `morning_briefing_YYYY-MM-DD.txt` | Daily briefing reports |

---

## 📋 Step-by-Step Usage

### 1️⃣ First Time Setup

```bash
# Make sure your bot works manually
python3 morning_briefing.py

# Or use the test script
./test_now.sh
```

**Expected output:**
```
============================================================
  MORNING BRIEFING  —  Thursday, February 26, 2026
============================================================
  Good morning, Andrew! Here's what's happening today.
...
```

If you see errors, check:
- ✅ `NEWS_API_KEY` is set in `.env`
- ✅ Internet connection is working
- ✅ Dependencies installed: `pip3 install requests python-dotenv schedule`

---

### 2️⃣ Choose Your Scheduling Method

#### Option A: launchd (Recommended for Daily Use)

```bash
./install.sh launchd
```

**What happens:**
1. Creates `~/Library/LaunchAgents/com.morningbot.briefing.plist`
2. Loads job into macOS launchd system
3. Bot will run at 7:00 AM every day automatically
4. Survives reboots (starts automatically when Mac boots)

**Check it's running:**
```bash
./check_status.sh launchd
```

**View logs:**
```bash
tail -f logs/briefing_output.log
```

**Uninstall:**
```bash
./uninstall.sh launchd
```

---

#### Option B: Python Scheduler (Great for Testing)

```bash
./install.sh python
```

**What happens:**
1. Installs `schedule` library (if needed)
2. Starts `scheduler.py` in background
3. Creates `scheduler.pid` to track the process
4. Bot will run at 7:00 AM every day while scheduler is running

**Check it's running:**
```bash
./check_status.sh python
```

**View logs:**
```bash
tail -f logs/scheduler.log
```

**Uninstall:**
```bash
./uninstall.sh python
```

**⚠️ Important:** Python scheduler stops if you restart your Mac. Run `./install.sh python` again after reboot.

---

### 3️⃣ Monitoring & Maintenance

#### Check Status
```bash
# Check all schedulers
./check_status.sh

# Check specific method
./check_status.sh launchd
./check_status.sh python
```

#### View Logs

**launchd logs:**
```bash
# Normal output
tail -f logs/briefing_output.log

# Errors only
tail -f logs/briefing_error.log
```

**Python scheduler logs:**
```bash
tail -f logs/scheduler.log
```

#### View Generated Reports
```bash
# List all reports
ls -lh morning_briefing_*.txt

# View today's report
cat morning_briefing_$(date +%Y-%m-%d).txt
```

---

### 4️⃣ Testing Before Scheduling

**Always test manually first!**

```bash
./test_now.sh
```

This runs your briefing immediately (doesn't wait for 7:00 AM).

**Why test?**
- ✅ Verify API keys work
- ✅ Check network connectivity
- ✅ See what the output looks like
- ✅ Catch errors before scheduling

---

## 🔧 Troubleshooting

### Bot Doesn't Run at 7:00 AM

**launchd:**
```bash
# Check if job is loaded
launchctl list | grep morningbot

# If not loaded, reinstall
./uninstall.sh launchd
./install.sh launchd

# Check logs for errors
cat logs/briefing_error.log
```

**Python scheduler:**
```bash
# Check if process is running
./check_status.sh python

# If stopped, restart
./uninstall.sh python
./install.sh python

# Check scheduler logs
tail logs/scheduler.log
```

---

### API Errors in Logs

```bash
# Check your .env file
cat .env

# Make sure NEWS_API_KEY is set
# Make sure there are no extra spaces

# Test the bot manually
./test_now.sh
```

Common API errors:
- `401 Unauthorized` → Bad API key
- `429 Too Many Requests` → Quota exceeded (wait or upgrade)
- `Timeout` → Network slow, increase timeout in code
- `NEWS_API_KEY not found` → Missing from `.env`

---

### Python Scheduler Stopped After Reboot

**This is expected!** Python scheduler doesn't auto-start on boot.

**Solution 1:** Use launchd instead (auto-starts)
```bash
./uninstall.sh python
./install.sh launchd
```

**Solution 2:** Manually restart after reboot
```bash
./install.sh python
```

---

### Change the Scheduled Time

#### launchd (modify .plist file)

1. Open `com.morningbot.briefing.plist`
2. Find `<key>StartCalendarInterval</key>` section
3. Change the hour (0-23 format):
   ```xml
   <key>Hour</key>
   <integer>8</integer>  <!-- Change from 7 to 8 -->
   ```
4. Reload:
   ```bash
   ./uninstall.sh launchd
   ./install.sh launchd
   ```

#### Python scheduler (modify scheduler.py)

1. Open `scheduler.py`
2. Find this line:
   ```python
   schedule.every().day.at("07:00").do(run_morning_briefing)
   ```
3. Change the time:
   ```python
   schedule.every().day.at("08:00").do(run_morning_briefing)
   ```
4. Restart:
   ```bash
   ./uninstall.sh python
   ./install.sh python
   ```

---

## 🎓 Educational Notes

### What You Learned

1. **Task Scheduling Concepts**
   - launchd vs cron vs Python schedulers
   - When to use each method
   - Trade-offs between approaches

2. **macOS launchd System**
   - `.plist` file format (XML)
   - Property List key-value structure
   - LaunchAgents vs LaunchDaemons
   - `launchctl` command usage

3. **Python Scheduling**
   - `schedule` library usage
   - Background processes
   - Process ID (PID) tracking
   - Logging to files

4. **Bash Scripting**
   - Shell script structure (`#!/bin/bash`)
   - Command-line arguments (`$1`, `$2`)
   - Conditional logic (`if/else/case`)
   - Colors in terminal output (ANSI codes)
   - Process management (`ps`, `kill`, `nohup`)

5. **Bot Deployment Patterns**
   - Automated execution
   - Logging and monitoring
   - Error handling
   - Production vs development approaches

### Key Takeaways

**A real bot must:**
1. ⏰ Run automatically (scheduled)
2. 🔄 Run repeatedly (daily/weekly/etc.)
3. 📊 Fetch fresh data each time
4. 💾 Save results persistently
5. 📝 Log activity for debugging
6. ⚠️ Handle errors gracefully
7. 🔧 Be easy to start/stop/monitor

**You've built all of this!** 🎉

---

## 🚀 Next Steps

### Enhance Your Bot

1. **Add more data sources**
   - Stock prices (Alpha Vantage API)
   - GitHub activity (GitHub API)
   - Email summary (Gmail API)
   - Calendar events (Google Calendar API)

2. **Improve scheduling**
   - Different schedules for weekdays/weekends
   - Run multiple times per day
   - Skip holidays automatically

3. **Add notifications**
   - Send email with the report
   - Post to Slack
   - macOS notification banner

4. **Store historical data**
   - Save to SQLite database
   - Track trends over time
   - Generate weekly summaries

### Explore Advanced Topics

- **Cron syntax** (Unix/Linux scheduling)
- **Systemd timers** (Linux alternative to cron)
- **Windows Task Scheduler** (Windows equivalent)
- **Docker scheduling** (for containerized bots)
- **Cloud scheduling** (AWS EventBridge, Google Cloud Scheduler)

---

## 📚 Additional Resources

- **launchd**: `man launchd.plist` in terminal
- **Python schedule**: https://schedule.readthedocs.io/
- **Bash scripting**: https://www.shellscript.sh/
- **Process management**: `man ps`, `man kill`
- **Apple docs**: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/

---

## 🎉 Congratulations!

You've learned professional-grade bot deployment techniques:
- ✅ Two complete scheduling systems
- ✅ Production-ready automation
- ✅ Comprehensive logging
- ✅ Easy management scripts
- ✅ Proper error handling

Your morning briefing bot is now a **real, production-ready automated system**!

🌅 Wake up tomorrow to fresh data at 7:00 AM! ☕
