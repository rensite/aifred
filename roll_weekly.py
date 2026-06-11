import sqlite3, os, time, subprocess
DB = os.path.expanduser("~/aifred.db")
CLAUDE = os.path.expanduser("~/.local/bin/claude")

def claude(prompt, timeout=240):
    try:
        r = subprocess.run([CLAUDE, "-p", prompt, "--model", "haiku"], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip()
    except Exception:
        return ""

INSTR = "You maintain long-term memory about a chat. Merge the existing memory with the new daily notes into ONE updated memory: concise bullet points of stable facts, preferences, tone, agreements, personal setup of the other person. Drop outdated or duplicate items. Output in English, bullets only."

def main():
    now = int(time.time())
    c = sqlite3.connect(DB)
    chats = [r[0] for r in c.execute("SELECT DISTINCT chat_key FROM daily_summaries")]
    for ck in chats:
        daily = [r[0] for r in c.execute("SELECT summary FROM daily_summaries WHERE chat_key=? ORDER BY created_ts", (ck,))]
        if not daily:
            continue
        old = c.execute("SELECT memory FROM chat_memory WHERE chat_key=?", (ck,)).fetchone()
        old_mem = old[0] if old else "(none)"
        body = "EXISTING MEMORY:" + chr(10) + old_mem + chr(10)*2 + "NEW DAILY NOTES:" + chr(10) + chr(10).join(daily)
        merged = claude(INSTR + chr(10)*2 + body[:14000])
        if merged:
            c.execute("INSERT INTO chat_memory(chat_key,memory,updated_ts) VALUES(?,?,?) ON CONFLICT(chat_key) DO UPDATE SET memory=excluded.memory, updated_ts=excluded.updated_ts", (ck, merged, now))
    c.execute("DELETE FROM daily_summaries")
    c.commit(); c.close()
    print("weekly rollup done for " + str(len(chats)) + " chats")

if __name__ == "__main__":
    main()
