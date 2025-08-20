import os
import asyncio
import asyncpg
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- توکن و دیتابیس ---
TOKEN = "8397328636:AAEJFNymHkjykxQh_H8FsgTgm58CjrYc9Ig"
DATABASE_URL = "postgresql://alireza_sbi0_user:vWClPVxY8onlO2f8OkwXFauKWyAHitYw@dpg-d2ipq23e5dus73b9gg7g-a.oregon-postgres.render.com/alireza_sbi0"

# --- اتصال async به دیتابیس ---
async def create_pool():
    return await asyncpg.create_pool(DATABASE_URL, ssl="require")

# --- فانکشن افزایش XP ---
async def add_xp(pool, user_id: int, group_id: int, xp: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT xp, level FROM users WHERE user_id=$1 AND group_id=$2", user_id, group_id)
        if row:
            new_xp = row["xp"] + xp
            new_level = row["level"]
            if new_xp >= new_level * 100:
                new_level += 1
            await conn.execute("UPDATE users SET xp=$1, level=$2 WHERE user_id=$3 AND group_id=$4",
                               new_xp, new_level, user_id, group_id)
        else:
            await conn.execute("INSERT INTO users(user_id, group_id, xp, level) VALUES($1, $2, $3, $4)",
                               user_id, group_id, xp, 1)

# --- دستور لیدربرد گروه ---
async def group_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pool = context.bot_data["db_pool"]
    chat_id = update.effective_chat.id
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, xp, level FROM users WHERE group_id=$1 ORDER BY xp DESC LIMIT 10", chat_id)
        if rows:
            msg = "🏆 لیدربرد گروه:\n"
            for i, row in enumerate(rows, start=1):
                msg += f"{i}. کاربر {row['user_id']} - سطح {row['level']} - XP {row['xp']}\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("هیچ داده‌ای برای این گروه موجود نیست.")

# --- دستور لیدربرد جهانی ---
async def global_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pool = context.bot_data["db_pool"]
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, SUM(xp) as total_xp, MAX(level) as max_level FROM users GROUP BY user_id ORDER BY total_xp DESC LIMIT 10"
        )
        if rows:
            msg = "🌐 لیدربرد جهانی:\n"
            for i, row in enumerate(rows, start=1):
                msg += f"{i}. کاربر {row['user_id']} - سطح {row['max_level']} - XP {row['total_xp']}\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("هیچ داده‌ای جهانی موجود نیست.")

# --- دستور تست XP ---
async def addxp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pool = context.bot_data["db_pool"]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await add_xp(pool, user_id, chat_id, 10)
    await update.message.reply_text("✅ شما ۱۰ XP گرفتید!")

# --- اجرای بات ---
async def main():
    pool = await create_pool()
    app = ApplicationBuilder().token(TOKEN).build()

    # ذخیره pool تو bot_data
    app.bot_data["db_pool"] = pool

    # اضافه کردن هاندلرها
    app.add_handler(CommandHandler("group_leaderboard", group_leaderboard))
    app.add_handler(CommandHandler("global_leaderboard", global_leaderboard))
    app.add_handler(CommandHandler("addxp", addxp_command))

    print("Bot is running...")
    await app.run_polling()  # polling async و امن برای Render

if __name__ == "__main__":
    asyncio.run(main())
