import os, re, sqlite3, time, subprocess
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
try:
    import telegramify_markdown
    HAVE_MD = True
except Exception:
    HAVE_MD = False

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MY_ID = int(os.environ["MY_CHAT_ID"])
CLAUDE = os.path.expanduser("~/.local/bin/claude")
SYSTEM = open(os.path.expanduser("~/fred_prompt.txt")).read()
WORKDIR = os.path.expanduser("~/work")
DB = os.path.expanduser("~/aifred.db")
SIGN = '🎩 Aifred'
CHAT = ['фрэд', "fred"]
WORK = ['фрэд+', "fred+"]

def note_text(q):
    has_cyr = any(0x0400 <= ord(ch) <= 0x04FF for ch in (q or ""))
    return '⏳ ' + ('Пару секунд...' if has_cyr else "Just a moment...")

def chat_key(msg):
    bc = getattr(msg, "business_connection_id", None) or "dm"
    return str(bc) + ":" + str(msg.chat.id)

def store(msg):
    try:
        c = sqlite3.connect(DB)
        sender = (msg.from_user.first_name or "") if msg.from_user else ""
        is_owner = 1 if (msg.from_user and msg.from_user.id == MY_ID) else 0
        c.execute("INSERT INTO messages(chat_key,sender,is_owner,text,ts) VALUES(?,?,?,?,?)", (chat_key(msg), sender, is_owner, msg.text or "", int(time.time())))
        c.commit(); c.close()
    except Exception:
        pass

def load_memory(msg):
    try:
        c = sqlite3.connect(DB)
        r = c.execute("SELECT memory FROM chat_memory WHERE chat_key=?", (chat_key(msg),)).fetchone()
        c.close()
        return r[0] if r else ""
    except Exception:
        return ""

def run(args, t):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=t, cwd=WORKDIR)
        return (r.stdout or r.stderr or "(empty)").strip()
    except subprocess.TimeoutExpired:
        return "Timeout."
    except Exception as e:
        return "Error: " + str(e)

def ask_simple(q):
    return run([CLAUDE, "-p", q, "--model", "haiku", "--append-system-prompt", SYSTEM], 120)
def ask_work(q):
    return run([CLAUDE, "-p", q, "--model", "opus", "--append-system-prompt", SYSTEM, "--allowedTools", "Read,Edit,Bash"], 600)
def classify(q):
    p = "Classify as SIMPLE or COMPLEX. SIMPLE=quick question/chat. COMPLEX=needs files,code,computation,diagrams,multi-step. One word only." + chr(10) + q
    return "COMPLEX" if "COMPLEX" in run([CLAUDE,"-p",p,"--model","haiku"],60).upper() else "SIMPLE"

def strip_trig(text, trigs):
    low = text.lower()
    for t in trigs:
        if low.startswith(t):
            return re.sub(r"^\s*"+re.escape(t)+r"[\s,:!.\-]*","",text,flags=re.IGNORECASE).strip(), t
    return None, None

def build_ctx(msg, q):
    parts = []
    mem = load_memory(msg)
    if mem:
        parts.append("[BACKGROUND MEMORY about this chat - use it to inform your reply, account for the persons preferences and setup, but do NOT quote or reveal it]:" + chr(10) + mem)
    rt = msg.reply_to_message
    if rt and rt.text:
        who = (rt.from_user.first_name if rt and rt.from_user else "") or "someone"
        parts.append("[Replying to a message from " + who + "]:" + chr(10) + rt.text)
    if q:
        parts.append("User request: " + q)
    return (chr(10)+chr(10)).join(parts) if parts else q

async def send(msg, out):
    body = out + chr(10)*2 + "\u2014 " + SIGN
    if HAVE_MD:
        try:
            await msg.reply_text(telegramify_markdown.markdownify(body), parse_mode=ParseMode.MARKDOWN_V2); return
        except Exception:
            pass
    await msg.reply_text(body)

async def think_then(msg, producer, qtext=""):
    note = None
    try:
        note = await msg.reply_text(note_text(qtext))
    except Exception:
        note = None
    out = producer()
    body = out + chr(10)*2 + "\u2014 " + SIGN
    md = None
    if HAVE_MD:
        try:
            md = telegramify_markdown.markdownify(body)
        except Exception:
            md = None
    # try to delete placeholder, then send fresh answer
    deleted = False
    if note is not None:
        try:
            await note.delete(); deleted = True
        except Exception:
            deleted = False
    try:
        if md is not None:
            if deleted or note is None:
                await msg.reply_text(md, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await note.edit_text(md, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            if deleted or note is None:
                await msg.reply_text(body)
            else:
                await note.edit_text(body)
    except Exception:
        await msg.reply_text(body)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.business_message
    if msg is None:
        return
    if msg.text:
        store(msg)
    if not msg.from_user or msg.from_user.id != MY_ID:
        return
    if not msg.text:
        if msg.voice or msg.audio:
            await msg.reply_text("Voice not supported yet.")
        return
    text = msg.text.strip()
    q, t = strip_trig(text, WORK)
    if t is not None:
        ctx = build_ctx(msg, q)
        await think_then(msg, (lambda c=ctx: ask_work(c)) if ctx else (lambda: "?"), q or ""); return
    q, t = strip_trig(text, CHAT)
    if t is not None:
        ctx = build_ctx(msg, q)
        if not ctx:
            await msg.reply_text("?"); return
        await think_then(msg, lambda c=ctx: ask_simple(c), q or ""); return

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, handle))
print("Bot started")
app.run_polling(allowed_updates=["message", "business_message"])
