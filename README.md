# claude-agent

Telegram bot ("Fred") powered by Claude, running as a warm systemd service on EC2.

## Components
- `claude_bot.py` - main Telegram bot (long-running process)
- `roll_daily.py` / `roll_weekly.py` - scheduled rollup jobs
- `fred_prompt.txt` - system prompt

## Setup
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.claude_env` and fill in your values.
3. Run: `python3 claude_bot.py`

## Environment variables
- `TELEGRAM_BOT_TOKEN` - bot token from @BotFather
- `MY_CHAT_ID` - allowed Telegram chat ID

## Deployment
Runs as `claude-bot.service` (systemd) on the EC2 instance for auto-restart and a warm, always-on process.

## Not in repo
Secrets (`.claude_env`), database (`aifred.db`), and logs are gitignored.
