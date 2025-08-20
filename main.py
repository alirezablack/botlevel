import os
import psycopg
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- توکن و دیتابیس ---
TOKEN = "8397328636:AAEJFNymHkjykxQh_H8FsgTgm58CjrYc9Ig"
DATABASE_URL = "postgresql://alireza_sbi0_user:vWClPVxY8onlO2f8OkwXFauKWyAHitYw@dpg-d2ipq23e5dus73b9gg7g-a.oregon-postgres.render.com/alireza_sbi0"

# --- اتصال به دیتابیس ---
conn = psycopg.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

# --- ایجاد جدول‌ها اگر وجود نداشت ---
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT,
    group_id BIGINT,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    PRIMARY KEY(user_id, group_id)
);
""")
conn.commit()

# --- فانکشن افزایش XP ---
async def add_xp(user_id: int, group_id: int, xp: int):
    cur.execute("SELECT xp, level FROM users WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    row = cur.fetchone()
    if row:
        new_xp = row[0] + xp
        new_level = row[1]
        if new_xp >= new_level * 100:
            new_level += 1
        cur.execute("UPDATE users SET xp=%s, level=%s WHERE user_id=%s AND group_id=%s",
                    (new_xp, new_level, user_id, group_id))
    else:
        cur.execute("INSERT INTO users(user_id, group_id, xp, level) VALUES(%s, %s, %s, %s)",
                    (user_id, group_id, xp, 1))
    conn.commit()

# --- دستور لیدربرد گروه ---
async def group_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cur.execute("SELECT user_id, xp, level FROM users WHERE group_id=%s ORDER BY xp DESC LIMIT 10", (chat_id,))
    rows = cur.fetchall()
    if rows:
        msg = "🏆 لیدربرد گروه:\n"
        for i, row in enumerate(rows, start=1):
            msg += f"{i}. کاربر {row[0]} - سطح {row[2]} - XP {row[1]}\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("هیچ داده‌ای برای این گروه موجود نیست.")

# --- دستور لیدربرد جهانی ---
async def global_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT user_id, SUM(xp) as total_xp, MAX(level) as max_level FROM users GROUP BY user_id ORDER BY total_xp DESC LIMIT 10")
    rows = cur.fetchall()
    if rows:
        msg = "🌐 لیدربرد جهانی:\n"
        for i, row in enumerate(rows, start=1):
            msg += f"{i}. کاربر {row[0]} - سطح {row[2]} - XP {row[1]}\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("هیچ داده‌ای جهانی موجود نیست.")

# --- دستور تست XP (مثلا برای ارسال پیام) ---
async def addxp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await add_xp(user_id, chat_id, 10)
    await update.message.reply_text("✅ شما ۱۰ XP گرفتید!")

# --- اجرای بات ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("group_leaderboard", group_leaderboard))
app.add_handler(CommandHandler("global_leaderboard", global_leaderboard))
app.add_handler(CommandHandler("addxp", addxp_command))

print("Bot is running...")
app.run_polling()

