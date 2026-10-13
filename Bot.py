
import asyncio
import feedparser
import requests
from telegram import Bot
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

# CONFIG - Yahan apna naya token daalna
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_NEW_TOKEN_HERE")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # Agar channel me bhejna hai toh @channelusername, warna blank chhod do - bot DM karega

IST = pytz.timezone("Asia/Kolkata")

# RSS Sources for Stock Market
RSS_FEEDS = {
    "Energy & Commodities": "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1808152121.cms",
    "Macroeconomic & Regulatory": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "IT & Technology": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
}

def fetch_news(category, limit=2):
    try:
        feed = feedparser.parse(RSS_FEEDS[category])
        items = []
        for entry in feed.entries[:limit]:
            title = entry.title.strip()
            items.append(f"{len(items)+1}. {title}")
        return "\n\n".join(items) if items else "No updates"
    except Exception as e:
        return f"Error fetching {category}: {e}"

def build_morning_message():
    date_str = datetime.now(IST).strftime("%d %b")
    msg = f"*{date_str}: Important pre-market news updates.*\n\n"
    for cat in ["Energy & Commodities", "Macroeconomic & Regulatory", "IT & Technology"]:
        msg += f"*{cat}*\n{fetch_news(cat)}\n\n----\n\n"
    msg += "_Powered by @stock_market_newsbot | Auto at 8:30 AM_"
    return msg

def build_evening_message():
    date_str = datetime.now(IST).strftime("%d %b")
    msg = f"*{date_str}: Market Wrap - Evening Update (6 PM)*\n\n"
    for cat in ["Markets", "Macroeconomic & Regulatory", "Energy & Commodities"]:
        msg += f"*{cat}*\n{fetch_news(cat)}\n\n----\n\n"
    msg += "_Powered by @stock_market_newsbot | Auto at 6 PM_"
    return msg

# Telegram Commands
async def start(update, context):
    await update.message.reply_text("Namaste! 🙏\nMain roz 8:30 AM aur 6 PM ko stock market news bhejunga.\n\nCommands:\n/morning - Pre-market news\n/evening - Market wrap\n/today - Aaj ki summary")

async def morning_cmd(update, context):
    await update.message.reply_text(build_morning_message(), parse_mode="Markdown")

async def evening_cmd(update, context):
    await update.message.reply_text(build_evening_message(), parse_mode="Markdown")

async def today_cmd(update, context):
    msg = build_morning_message() + "\n\n" + build_evening_message()
    await update.message.reply_text(msg, parse_mode="Markdown")

async def send_scheduled(bot, is_morning=True):
    # Get all subscribers - for now sends to CHANNEL_ID if set, else you need DB
    # Simple version: if CHANNEL_ID set, send there
    text = build_morning_message() if is_morning else build_evening_message()
    if CHANNEL_ID:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")
            print(f"Sent {'morning' if is_morning else 'evening'} to {CHANNEL_ID}")
        except Exception as e:
            print(f"Send failed: {e}")
    else:
        print("CHANNEL_ID not set - scheduled send skipped. Set CHANNEL_ID env to enable auto broadcast.")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("morning", morning_cmd))
    app.add_handler(CommandHandler("evening", evening_cmd))
    app.add_handler(CommandHandler("today", today_cmd))

    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled(app.bot, True)), 'cron', hour=8, minute=30)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled(app.bot, False)), 'cron', hour=18, minute=0)
    scheduler.start()
    print("Bot started - Morning 8:30 AM | Evening 6:00 PM IST")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
