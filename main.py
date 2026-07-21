import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
HIGHLIGHTLY_KEY = os.getenv('HIGHLIGHTLY_API_KEY')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

HEADERS = {
    'x-rapidapi-key': HIGHLIGHTLY_KEY,
    'x-rapidapi-host': 'sport-highlights-api.p.rapidapi.com'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚽ Today's Matches", callback_data='today')],
        [InlineKeyboardButton("🔥 Best Winning Bets", callback_data='bets')],
        [InlineKeyboardButton("🔮 Smart Value Tips", callback_data='tips')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 **Soccer Value Bot** — Full Pipeline Mode\n\n"
        "Highlightly + football-data.org", 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def today_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not HIGHLIGHTLY_KEY:
        await update.message.reply_text("❌ Highlightly API key missing.")
        return
    
    try:
        url = "https://sport-highlights-api.p.rapidapi.com/football/matches"
        params = {'date': date.today().isoformat(), 'limit': 20}
        
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        
        matches = data.get('data', [])[:12]
        if not matches:
            await update.message.reply_text("No matches today.")
            return
        
        message = f"⚽ **Matches Today** ({date.today()})\n\n"
        for m in matches:
            home = m.get('homeTeam', {}).get('name', 'Home')
            away = m.get('awayTeam', {}).get('name', 'Away')
            league = m.get('league', 'Unknown')
            time = str(m.get('date', '')).split('T')[1][:5] if 'T' in str(m.get('date','')) else '?'
            message += f"🕒 {time} | {league}\n**{home}** vs **{away}**\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def best_winning_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not HIGHLIGHTLY_KEY:
        await update.message.reply_text("❌ Highlightly API key missing.")
        return
    
    try:
        url = "https://sport-highlights-api.p.rapidapi.com/football/odds"
        params = {'date': date.today().isoformat(), 'oddsType': 'prematch', 'limit': 15}
        
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        
        message = "🔥 **Best Winning Bets Today**\n\n"
        count = 0
        for item in data.get('data', [])[:8]:
            home = item.get('homeTeam', {}).get('name', 'Home')
            away = item.get('awayTeam', {}).get('name', 'Away')
            
            best = "No clear favorite"
            for odd in item.get('odds', [])[:2]:
                if odd.get('market') == 'Full Time Result':
                    values = odd.get('values', [])
                    if values:
                        fav = min(values, key=lambda x: float(x.get('odd', 999)))
                        best = f"**{fav.get('value')}** @ {fav.get('odd')}"
            
            message += f"**{home} vs {away}**\nPick: {best}\n\n"
            count += 1
            if count >= 6:
                break
        
        if count == 0:
            message += "No strong bets right now. Check back later!"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Bets Error: {str(e)}\n\n(Highlightly odds may need paid plan)")

async def value_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔮 **Smart Daily Value Tips**\n\n"
        "• Bet on strong favorites when odds are better than expected\n"
        "• Over 2.5 goals in attacking matches\n"
        "• BTTS Yes when both teams are scoring well\n"
        "• World Cup matches usually have great value\n\n"
        "**Always gamble responsibly** — no guarantee of wins."
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'today':
        await today_matches(query, context)
    elif query.data == 'bets':
        await best_winning_bets(query, context)
    elif query.data == 'tips':
        await value_tips(query, context)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Soccer Value Bot — Pipeline Mode Running!")
    app.run_polling()
