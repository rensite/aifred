import sqlite3, os, time, subprocess
DB = os.path.expanduser("~/aifred.db")
CLAUDE = os.path.expanduser("~/.local/bin/claude")

def claude(prompt, timeout=180):
    try:
        r = subprocess.run([CLAUDE, "-p", prompt, "--model", "haiku"], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip()
    except Exception:
        return ""

INSTR = "Summarize this chat into a few concise bullet points capturing what matters for future context: the other persons preferences, tone, agreements, ongoing topics, personal setup, important facts. Skip trivial chatter. Output in English, bullets only."

def main():
    now = int(time.time())
    c = sqlite3.connect(DB)
    chats = [r[0] for r in c.execute("SELECT DISTINCT chat_key FROM messages")]
    for ck in chats:
        rows = c.execute("SELECT sender, is_owner, text FROM messages WHERE chat_key=? ORDER BY ts", (ck,)).fetchall()
        if not rows:
            continue
        convo = "".join((("[OWNER] " if r[1] else (str(r[0] or "other")+": ")) + (r[2] or "") + chr(10)) for r in rows)
        summ = claude(INSTR + chr(10) + chr(10) + convo[:12000])
        if summ:
            day = time.strftime("%Y-%m-%d", time.gmtime(now))
            c.execute("INSERT INTO daily_summaries(chat_key,day,summary,created_ts) VALUES(?,?,?,?)", (ck, day, summ, now))
    c.execute("DELETE FROM messages")
    c.commit(); c.close()
    print("daily rollup done for " + str(len(chats)) + " chats")

if __name__ == "__main__":
    main()
