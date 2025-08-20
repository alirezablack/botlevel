import logging
import psycopg
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======= تنظیمات =======
TOKEN = "7981388986:AAE3xI26bTu7WJjTa9vx_svYrfVHbqBE4RU"  # مستقیم توکن بذار
DATABASE_URL = "postgresql://alireza_sbi0_user:vWClPVxY8onlO2f8OkwXFauKWyAHitYw@dpg-d2ipq23e5dus73b9gg7g-a.oregon-postgres.render.com/alireza_sbi0"  # لینک دیتابیس تو Render

if not TOKEN or not DATABASE_URL:
    raise ValueError("توکن یا دیتابیس وارد نشده!")

# ======= اتصال دیتابیس =======
conn = psycopg.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT,
    chat_id BIGINT,
    username TEXT,
    level INT DEFAULT 0,
    PRIMARY KEY (user_id, chat_id)
)
""")
conn.commit()

# ======= تنظیم لاگ =======
logging.basicConfig(level=logging.INFO)

# ======= فانکشن‌ها =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من روشنم 😊")

async def increase_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id

    cur.execute("""
    INSERT INTO users (user_id, chat_id, username, level)
    VALUES (%s, %s, %s, 1)
    ON CONFLICT (user_id, chat_id) DO UPDATE
    SET level = users.level + 1, username = EXCLUDED.username
    """, (user.id, chat_id, user.username))
    conn.commit()

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    cur.execute("SELECT username, level FROM users WHERE chat_id=%s ORDER BY level DESC LIMIT 10", (chat_id,))
    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("هنوز کسی تو این گروه لول نگرفته 😅")
        return

    text = "🏆 لیدربرد گروه:\n\n"
    for i, row in enumerate(rows, start=1):
        text += f"{i}. @{row[0]} → لول {row[1]}\n"
    await update.message.reply_text(text)

async def global_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT username, SUM(level) as total FROM users GROUP BY username ORDER BY total DESC LIMIT 10")
    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("هیچ کاربری هنوز لول نداره 😅")
        return

    text = "🌍 لیدربرد جهانی:\n\n"
    for i, row in enumerate(rows, start=1):
        text += f"{i}. @{row[0]} → لول {row[1]}\n"
    await update.message.reply_text(text)

# ======= ران اصلی =======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("global_leaderboard", global_leaderboard))

    # هندل فارسی
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^لیدر برد$"), leaderboard))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^لیدر برد جهانی$"), global_leaderboard))

    # افزایش لول با هر پیام
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), increase_level))

    app.run_polling()

if __name__ == "__main__":
    main()

