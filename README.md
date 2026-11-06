# DIU ACM Contest Reminder Telegram Bot

An automated Telegram bot that monitors **Codeforces** and **AtCoder** contests and delivers reminders exactly **1 day (24 hours) before** each contest starts.

---

### Notice Format Sample

```text
#contest_reminder #codeforces

Codeforces Round 1132 (Div. 2)
📅 Date: Friday, 6 November, 2026
⏰ Start Time: 8:35 PM
⏳ Duration: 02 hours 15 minutes
🔗 Contest Link: https://codeforces.com/contests/2284

⚠️ Important Notice:

Any kind of cheating or plagiarism will result in a permanent ban from DIU ACM.

Best of luck to all participants.
Happy coding 🖤
```

---

## 🚀 Features

- **Exact Formatting**: 100% compliant with DIU ACM notice style for both `#codeforces` and `#atcoder`.
- **Dual Platforms**:
  - **Codeforces**: Real-time integration via Codeforces official API.
  - **AtCoder**: Real-time scraping of official upcoming contests table.
- **1-Day Reminder Window**: Automatically detects contests starting within $\le 24$ hours (configurable).
- **Zero Duplicate Notices**: Automatically tracks sent contest notices in persistent local storage (`notified_contests.json`).
- **Interactive Commands**: `/upcoming`, `/test`, `/check`, `/status`, `/help`.
- **Multiple Destinations**: Broadcasts to public channels (`@channel`), private channels (`-100...`), groups, or personal chats.
- **Built-in CLI Utilities**:
  - `python main.py --dry-run` (verify output in console without Telegram)
  - `python main.py --upcoming` (view all upcoming contests in table format)
  - `python main.py --test` (send a live sample message to your Telegram channel)
  - `python main.py --get-chat-id` (easily detect your Telegram Chat ID)

---

## 🛠️ Step-by-Step Setup Guide

### 1. Install Dependencies

Ensure Python 3.10+ is installed, then run:

```bash
pip install -r requirements.txt
```

*(If on Ubuntu/Debian with an externally managed environment, run `pip install --user --break-system-packages -r requirements.txt`)*

---

### 2. Create Your Telegram Bot

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`.
3. Choose a name (e.g., `DIU ACM Contest Bot`) and a username (e.g., `diu_acm_contest_bot`).
4. BotFather will provide an **HTTP API Token** (e.g., `7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Copy this token.

---

### 3. Get Your Telegram Chat ID or Channel ID

#### 🔹 For a Public Channel:
If your channel has a public link like `t.me/diu_acm_notices`:
- Use the channel username directly: `TELEGRAM_CHAT_ID=@diu_acm_notices`
- ⚠️ **Important**: Go to Channel Settings ➔ Administrators ➔ Add your bot as an **Administrator** with permission to "Post Messages".

#### 🔹 For a Private Channel or Group:
1. Add your bot as an **Administrator** to the channel or group.
2. Post any message into the channel or group.
3. Run the built-in detection command:
   ```bash
   python main.py --get-chat-id
   ```
   The script will display the detected Chat ID (e.g. `-1001234567890`).

#### 🔹 For Personal Direct Message:
1. Open your bot in Telegram and click **Start** or send `hello`.
2. Run:
   ```bash
   python main.py --get-chat-id
   ```
   Copy your user ID (e.g. `123456789`).

---

### 4. Configure Environment Variables

Copy the template file to `.env`:

```bash
cp .env.example .env
```

Open `.env` in a text editor (e.g. `nano .env`) and fill in your values:

```ini
# Bot token from @BotFather
TELEGRAM_BOT_TOKEN=7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Destination chat / channel (supports multiple separated by comma)
TELEGRAM_CHAT_ID=@diu_acm_notices

# Timezone for dates & times (Default: Asia/Dhaka for Bangladesh Standard Time)
TIMEZONE=Asia/Dhaka

# Periodic check interval in minutes (default: 15)
CHECK_INTERVAL_MINUTES=15

# Hours before contest to trigger reminder (default: 24.0)
REMINDER_HOURS_BEFORE=24.0

# Disable link previews in Telegram messages
DISABLE_WEB_PAGE_PREVIEW=true
```

---

## 🧪 Testing Your Bot

### 1. Dry Run (Console Preview)
See if upcoming contests within 24 hours are detected and check formatting without sending anything to Telegram:
```bash
python main.py --dry-run
```

### 2. View All Upcoming Contests
See full schedule of upcoming Codeforces and AtCoder contests in your terminal:
```bash
python main.py --upcoming
```

### 3. Send a Live Test Message
Send a preview notice of the nearest contest directly to your configured Telegram channel/chat:
```bash
python main.py --test
```

### 4. Run Single Check
Manually trigger a single check and send notices (without starting continuous polling):
```bash
python main.py --check
```

---

## 🏃 Running the Bot 24/7

### Method A: Run Directly in Terminal

```bash
python main.py
```
This runs both:
1. The background scheduler (checks every 15 minutes for contests starting in $\le 24$h).
2. Interactive command polling (`/upcoming`, `/test`, `/check`, `/status`).

---

### Method B: Run as a Linux `systemd` Service (Recommended for VPS / Server)

Running as a systemd service ensures the bot restarts automatically if the server reboots or crashes.

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/acm-bot.service
   ```

2. Paste the following configuration (replace `/home/anup/Downloads/acm-bot` with your actual directory and `anup` with your username):
   ```ini
   [Unit]
   Description=DIU ACM Contest Reminder Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=anup
   WorkingDirectory=/home/anup/Downloads/acm-bot
   ExecStart=/usr/bin/python3 /home/anup/Downloads/acm-bot/main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Reload and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now acm-bot.service
   ```

4. Check bot status and logs:
   ```bash
   sudo systemctl status acm-bot.service
   journalctl -u acm-bot.service -f
   ```

---

### Method C: Run in Background with `screen` or `nohup`

Using `tmux` or `screen`:
```bash
screen -S acmbot
python main.py
# Press Ctrl+A then D to detach
```

Using `nohup`:
```bash
nohup python main.py > bot.log 2>&1 &
```

---

### Method D: Run via Linux `cron` (Periodic Trigger)

If you only want a scheduled task without a background process running:

```bash
crontab -e
```

Add this line to run the check every 15 minutes:
```cron
*/15 * * * * cd /home/anup/Downloads/acm-bot && /usr/bin/python3 main.py --check >> bot.log 2>&1
```

---

## 🤖 Telegram Bot Commands

When the bot is running, you or your admins can send these commands directly in Telegram:

| Command | Description |
|---|---|
| `/upcoming` | Lists upcoming contests from Codeforces & AtCoder with dates & times in BST |
| `/test` | Sends sample preview notices in the exact template to the chat |
| `/check` | Triggers an immediate scan for contests within 24h and sends reminders |
| `/status` | Shows timezone, check interval, reminder window, and number of tracked contests |
| `/help` | Displays bot instructions and command overview |

---

## 🌐 Online Hosting Options

You have several great options to host this bot online 24/7:

### Option 1: GitHub Actions (100% Free Forever, Serverless)
If you only need the bot to send **automated 1-day reminders to your channel** (without running interactive commands 24/7):
1. Push this codebase to a private or public GitHub repository.
2. In your GitHub repo, go to **Settings ➔ Secrets and variables ➔ Actions**.
3. Add two repository secrets:
   - `TELEGRAM_BOT_TOKEN`: Your token from @BotFather
   - `TELEGRAM_CHAT_ID`: `@your_channel` or `-100xxxxxxxxxx`
4. In **Settings ➔ Actions ➔ General ➔ Workflow permissions**, select **Read and write permissions** (so the action can save `notified_contests.json`).
5. The pre-configured [`.github/workflows/reminder.yml`](.github/workflows/reminder.yml) workflow will automatically run every 30 minutes, check for contests, and send notices. **Cost: $0 / Free forever.**

---

### Option 2: Railway.app (Easiest Full 24/7 Bot)
For full 24/7 daemon with interactive commands (`/upcoming`, `/test`, etc.):
1. Push this project to your GitHub account.
2. Go to [Railway.app](https://railway.app/) and sign up.
3. Click **New Project ➔ Deploy from GitHub repo** and select this repo.
4. Go to **Variables** tab and add:
   - `TELEGRAM_BOT_TOKEN = your_bot_token`
   - `TELEGRAM_CHAT_ID = @your_channel`
   - `TIMEZONE = Asia/Dhaka`
5. Railway will automatically detect the [`Dockerfile`](Dockerfile) or [`Procfile`](Procfile) and start the bot immediately!

---

### Option 3: Docker on any VPS / Cloud Server
If you have a Linux VPS (Oracle Cloud Always-Free, Hetzner, DigitalOcean):
```bash
git clone <your-repo-url> acm-bot
cd acm-bot
cp .env.example .env
nano .env # add your credentials
docker compose up -d
```
The container will run in the background, restart on reboots, and persist notified contests to `./notified_contests.json`.

---

## 📁 Project Structure

```text
acm-bot/
├── config.py                 # Configuration loader (.env and defaults)
├── models.py                 # Contest dataclass & time calculations
├── formatter.py              # Exact DIU ACM notice message formatter
├── storage.py                # Deduplication storage (notified_contests.json)
├── scheduler.py              # Background worker & reminder logic
├── bot.py                    # TeleBot command handlers
├── main.py                   # CLI entry point & daemon runner
├── platforms/
│   ├── __init__.py
│   ├── codeforces.py         # Codeforces API fetcher
│   └── atcoder.py            # AtCoder web scraper
├── tests/
│   └── test_bot.py           # Unit tests
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # Complete documentation
```

---

## 🧪 Unit Tests

Run the test suite to ensure message formatting and deduplication pass:

```bash
python -m unittest discover tests
```
