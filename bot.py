import os
import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ROWS = 5
COLS = 5
BAD_APPLES = 5
games = {}

def new_board():
    positions = [(r,c) for r in range(ROWS) for c in range(COLS)]
    bad = set(random.sample(positions, BAD_APPLES))
    return {"bad": bad, "opened": set(), "gain": 0, "multiplier": 1.0, "active": True}

def build_keyboard(game):
    keyboard = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            pos = (r,c)
            if pos in game["opened"]:
                row.append(InlineKeyboardButton("💥" if pos in game["bad"] else "🍏", callback_data="ignore"))
            else:
                txt = "❓" if not game["active"] else "🍎"
                row.append(InlineKeyboardButton(txt, callback_data=f"open_{r}_{c}" if game["active"] else "ignore"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(f"💰 Encaisser {game['gain']*10} FCFA (x{game['multiplier']:.2f})", callback_data="cashout")])
    keyboard.append([InlineKeyboardButton("🔄 Nouvelle partie", callback_data="newgame")])
    return InlineKeyboardMarkup(keyboard)

async def start(update, context):
    games[update.effective_user.id] = new_board()
    await update.message.reply_text(f"🍎 APPLE FORTUNE 🍎\n\n🍏=gagne 💥=perdu\nGain: {games[update.effective_user.id]['gain']*10} FCFA", reply_markup=build_keyboard(games[update.effective_user.id]))

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in games: games[user_id] = new_board()
    game = games[user_id]
    data = query.data
    if data == "newgame":
        games[user_id] = new_board()
        await query.edit_message_text(f"🍎 Nouvelle partie", reply_markup=build_keyboard(games[user_id]))
        return
    if data == "cashout":
        gain = game['gain']*10
        game['active']=False
        await query.edit_message_text(f"💰 BRAVO {gain} FCFA encaissé ! x{game['multiplier']:.2f}", reply_markup=build_keyboard(game))
        return
    if data.startswith("open_"):
        if not game["active"]: return
        _,r,c = data.split("_")
        pos=(int(r),int(c))
        if pos in game["opened"]: return
        game["opened"].add(pos)
        if pos in game["bad"]:
            game["active"]=False
            await query.edit_message_text(f"💥 BOOM Pomme pourrie !", reply_markup=build_keyboard(game))
        else:
            game["gain"]+=1
            game["multiplier"]+=0.3
            await query.edit_message_text(f"🍏 Bien joué ! Gain: {game['gain']*10} FCFA (x{game['multiplier']:.2f})", reply_markup=build_keyboard(game))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
