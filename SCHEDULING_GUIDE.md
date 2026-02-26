# ============================================================
# TASK SCHEDULING GUIDE
# Understanding Automated Tasks and Bot Deployment
# ============================================================

## 🤖 Why Automation Matters for Bots

A **bot** is only truly a "bot" if it runs automatically without you having
to remember to start it. That's the whole point!

Your morning briefing bot should:
- ✅ Wake up at 7:00 AM every day
- ✅ Fetch fresh data from APIs
- ✅ Generate your report
- ✅ Save it to a file
- ❌ NOT require you to manually run `python morning_briefing.py`

This is called **task scheduling** or **job scheduling**.

---

## 📅 What is Task Scheduling?

Task scheduling means telling your computer:
> "Run this program at this time, every day/week/month"

Think of it like setting an alarm clock for your code.

**Common Uses:**
- Daily backups at midnight
- Sending weekly reports every Monday
- Checking stock prices every 5 minutes
- Running maintenance scripts every weekend
- **Morning briefings at 7:00 AM!** ☕

---

## 🔧 Scheduling Methods Explained

### METHOD 1: launchd (macOS Native) — RECOMMENDED

**What is launchd?**
- Apple's built-in task scheduler for macOS
- Runs automatically when your Mac starts
- More reliable than cron on Mac
- Survives system restarts
- Built into macOS since OS X 10.4 (2005)

**Why launchd > cron on Mac?**
| Feature              | launchd | cron |
|---------------------|---------|------|
| Runs if Mac asleep? | ✅ Yes (catches up) | ❌ No (missed) |
| Survives reboot?    | ✅ Yes | ⚠️ Sometimes |
| macOS native?       | ✅ Yes | ❌ Unix legacy |
| Error logging?      | ✅ Built-in | ⚠️ Manual |
| Apple recommended?  | ✅ Yes | ❌ Deprecated |

**How it works:**
1. You create a `.plist` file (Property List) describing your task
2. Load it into launchd with `launchctl load`
3. launchd watches the clock and runs your script at the right time
4. Logs are saved automatically

**Where files live:**
- User tasks: `~/Library/LaunchAgents/` (runs when you're logged in)
- System tasks: `/Library/LaunchDaemons/` (runs even if no one is logged in)

---

### METHOD 2: Python schedule Library (Portable)

**What is the schedule library?**
- A simple Python package for scheduling
- Works on macOS, Linux, Windows
- Easy to understand (just Python code, no XML)
- Good for testing and development

**How it works:**
1. Your script runs continuously in the background
2. It checks every second: "Is it 7:00 AM yet?"
3. When the time matches, it runs your function
4. Then waits for tomorrow

**Trade-offs:**
| Pros | Cons |
|------|------|
| ✅ Cross-platform | ❌ Must keep Python running |
| ✅ Easy to understand | ❌ Stops if computer restarts |
| ✅ Flexible (run every 5 min, etc.) | ❌ Uses a tiny bit of memory |
| ✅ Great for development | ⚠️ Less "production-ready" |

---

## 🎯 Which Method Should You Use?

**For daily use on macOS:**
→ Use **launchd** (Method 1)
- Set it and forget it
- Survives reboots
- Apple's recommended way

**For testing or multi-platform:**
→ Use **schedule** (Method 2)
- Quick to test
- Easy to modify
- Works on any OS

**Pro tip:** Use Method 2 during development, then deploy with Method 1!

---

## 🚀 Next Steps

1. Read through both implementations below
2. Try Method 2 first (easier to test)
3. Once it works, set up Method 1 for daily use
4. Use the helper scripts to manage everything

---

## 📖 Additional Resources

- launchd guide: `man launchd.plist` in terminal
- Python schedule docs: https://schedule.readthedocs.io/
- cron vs launchd: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html
