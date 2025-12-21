# Scraper Scheduler Setup Guide

This guide explains how to set up the web scraper to run automatically every 3 hours.

## 📋 Overview

You have **two options** for scheduling:

1. **Option A: System Cron Job** (Recommended for servers)
   - Uses macOS/Linux built-in cron
   - Runs in the background
   - Persists across reboots

2. **Option B: Python Scheduler** (Recommended for development)
   - Keeps a Python process running
   - Easier to monitor and debug
   - Must keep terminal/process alive

---

## 🔧 Option A: System Cron Job Setup

### Step 1: Test the Runner Script

First, verify the runner script works manually:

```bash
cd /Users/shehrambaig/PycharmProjects/Agentic_IRIS/src
python3 run_scraper.py
```

This should scrape all companies and log to `logs/scraper_YYYYMMDD.log`

### Step 2: Find Python Path

Find your Python 3 path:

```bash
which python3
```

Copy the output (e.g., `/usr/local/bin/python3` or `/usr/bin/python3`)

### Step 3: Edit Crontab

Open your crontab for editing:

```bash
crontab -e
```

### Step 4: Add Cron Entry

Add this line to run every 3 hours:

```bash
0 */3 * * * /usr/bin/python3 /Users/shehrambaig/PycharmProjects/Agentic_IRIS/src/run_scraper.py >> /Users/shehrambaig/PycharmProjects/Agentic_IRIS/logs/cron.log 2>&1
```

**Important:** Replace `/usr/bin/python3` with your actual Python path from Step 2.

#### Cron Schedule Explanation:
- `0 */3 * * *` = Every 3 hours at minute 0 (12:00 AM, 3:00 AM, 6:00 AM, etc.)

#### Alternative Schedules:
```bash
# Every 3 hours
0 */3 * * * ...

# Every 6 hours
0 */6 * * * ...

# Every day at 9 AM
0 9 * * * ...

# Every 3 hours between 9 AM and 6 PM
0 9-18/3 * * * ...
```

### Step 5: Verify Cron Job

List your cron jobs to verify:

```bash
crontab -l
```

### Step 6: Monitor Logs

Check if it's running:

```bash
# View cron execution log
tail -f /Users/shehrambaig/PycharmProjects/Agentic_IRIS/logs/cron.log

# View scraper application log
tail -f /Users/shehrambaig/PycharmProjects/Agentic_IRIS/logs/scraper_$(date +%Y%m%d).log
```

### Troubleshooting Cron

If cron doesn't run:

1. **Check cron is running:**
   ```bash
   sudo launchctl list | grep cron
   ```

2. **Check Python path is correct:**
   ```bash
   which python3
   ```

3. **Test the command manually:**
   ```bash
   /usr/bin/python3 /Users/shehrambaig/PycharmProjects/Agentic_IRIS/src/run_scraper.py
   ```

4. **Check system logs:**
   ```bash
   # macOS
   log show --predicate 'process == "cron"' --last 1h

   # Linux
   grep CRON /var/log/syslog
   ```

---

## 🐍 Option B: Python Scheduler Setup

### Step 1: Start the Scheduler

Run the scheduler (keeps running):

```bash
cd /Users/shehrambaig/PycharmProjects/Agentic_IRIS/src
python3 scheduler.py
```

**Custom interval:**
```bash
# Run every 6 hours instead of 3
python3 scheduler.py 6
```

### Step 2: Run in Background (Optional)

To run in background and keep it running after closing terminal:

```bash
nohup python3 scheduler.py > ../logs/scheduler.log 2>&1 &
```

Save the process ID that's displayed.

### Step 3: Monitor the Scheduler

```bash
# View logs
tail -f /Users/shehrambaig/PycharmProjects/Agentic_IRIS/logs/scheduler_*.log

# Check if running
ps aux | grep scheduler.py
```

### Step 4: Stop the Scheduler

```bash
# If running in foreground: Press Ctrl+C

# If running in background:
pkill -f scheduler.py

# Or with specific PID:
kill <PID>
```

### Run as macOS Service (Advanced)

Create a launchd plist file at `~/Library/LaunchAgents/com.agentic_iris.scheduler.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agentic_iris.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/shehrambaig/PycharmProjects/Agentic_IRIS/src/scheduler.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/shehrambaig/PycharmProjects/Agentic_IRIS/logs/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/shehrambaig/PycharmProjects/Agentic_IRIS/logs/scheduler_error.log</string>
</dict>
</plist>
```

Then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.agentic_iris.scheduler.plist
```

---

## 📊 Monitoring & Logs

### Log Locations

```
Agentic_IRIS/
├── logs/
│   ├── scraper_YYYYMMDD.log      # Daily scraper logs
│   ├── scheduler_YYYYMMDD.log    # Scheduler logs (Option B)
│   └── cron.log                  # Cron output (Option A)
└── change_tracking/
    ├── new_urls/                 # New URLs discovered
    ├── changes/                  # Change reports
    └── url_tracking.../          # Master URL files
```

### View Recent Activity

```bash
# View today's scraper log
tail -100 logs/scraper_$(date +%Y%m%d).log

# View new URLs discovered today
ls -lh change_tracking/new_urls/*$(date +%Y%m%d)*.json

# Count total new URLs discovered today
find change_tracking/new_urls -name "*$(date +%Y%m%d)*.json" -exec grep -o '"total_new_urls":[^,}]*' {} \; | cut -d: -f2 | paste -sd+ | bc
```

### Email Notifications (Optional)

To get email notifications when new URLs are found, modify `run_scraper.py` to send emails:

```python
# Add at the end of run_scraper() function
if total_new_urls > 0:
    send_email_notification(
        subject=f"New URLs Discovered: {total_new_urls}",
        body=f"Found {total_new_urls} new URLs across {successful_companies} companies"
    )
```

---

## 🔍 Quick Reference

### Check Status
```bash
# Check if cron job exists
crontab -l | grep run_scraper

# Check if Python scheduler is running
ps aux | grep scheduler.py

# View latest logs
tail -f logs/scraper_*.log
```

### Manual Run
```bash
cd /Users/shehrambaig/PycharmProjects/Agentic_IRIS/src
python3 run_scraper.py
```

### Stop Everything
```bash
# Stop cron job
crontab -e  # Then delete the line

# Stop Python scheduler
pkill -f scheduler.py
```

---

## ⚙️ Configuration

### Change Interval

**Cron:** Edit crontab and change `*/3` to desired interval
**Python Scheduler:** Pass interval as argument: `python3 scheduler.py 6`

### Change Companies

Edit `src/company_urls.json` to add/remove companies:

```json
[
  {
    "company_name": "Your Company",
    "url": "https://yourcompany.com/news"
  }
]
```

### Change Headless Mode

Edit `run_scraper.py` or `scheduler.py`:

```python
# Line ~52 or similar
async with UniversalScraper(headless=True, max_concurrent=5) as scraper:
#                                    ^^^^
#                          Change to False to see browser
```

---

## 📝 Recommendation

**For Production:** Use **Option A (Cron)** - more reliable, survives reboots
**For Testing:** Use **Option B (Python Scheduler)** - easier to debug and monitor

Both options create the same logs and output files!
