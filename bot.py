import time
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from decimal import Decimal

# ✅ Telegram token va chat ID
TELEGRAM_BOT_TOKEN = "7858589930:AAEPowvEr3Rkol4VJIadHbiHnISJclvdEAw"
CHAT_ID = 5831802170  # Sizning Telegram IDingiz

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ✅ Exchange API lar
EXCHANGES = {
    "binance": "https://api.binance.com/api/v3/ticker/price",
    "mexc": "https://www.mexc.com/open/api/v2/market/ticker",
    "bybit": "https://api.bybit.com/v5/market/tickers?category=spot",
    "huobi": "https://api.huobi.pro/market/tickers"
}

# 🔹 /start komandasi - MENYU qo‘shildi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    check_button = KeyboardButton("🔍 Arbitrage Tekshirish")
    markup.add(check_button)

    bot.send_message(
        message.chat.id,
        f"👋 Salom, {message.from_user.first_name}!\n\n"
        "Men **kriptovalyuta arbitrage botiman**! 🔥\n"
        "💹 **Narxlarni tekshiraman va foydali arbitrage imkoniyatlarini topaman**\n\n"
        "⚡ **Menyudan foydalanib tekshirishingiz mumkin!**",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 🔹 Narxlarni olish funksiyasi
def fetch_prices():
    prices = {}
    try:
        response = requests.get(EXCHANGES["binance"])
        if response.status_code == 200:
            data = response.json()
            for item in data:
                if item["symbol"].endswith("USDT"):
                    prices[f"binance_{item['symbol']}"] = Decimal(item["price"])

        response = requests.get(EXCHANGES["mexc"])
        if response.status_code == 200:
            data = response.json()
            for item in data["data"]:
                if item["symbol"].endswith("_USDT"):
                    prices[f"mexc_{item['symbol'].replace('_', '')}"] = Decimal(item["last"])

        response = requests.get(EXCHANGES["bybit"])
        if response.status_code == 200:
            data = response.json()
            for item in data["result"]["list"]:
                if item["symbol"].endswith("USDT"):
                    prices[f"bybit_{item['symbol']}"] = Decimal(item["lastPrice"])

        response = requests.get(EXCHANGES["huobi"])
        if response.status_code == 200:
            data = response.json()
            for item in data["data"]:
                if item["symbol"].endswith("usdt"):
                    prices[f"huobi_{item['symbol'].upper()}"] = Decimal(item["close"])

    except Exception as e:
        print(f"❌ Narxlarni olishda xatolik: {e}")

    return prices

# 🔹 Arbitraj imkoniyatlarini aniqlash
def find_arbitrage_opportunities(prices):
    opportunities = []
    symbols = {key.split("_")[1] for key in prices.keys()}

    for symbol in symbols:
        exchange_prices = {key.split("_")[0]: prices[key] for key in prices if symbol in key}

        if len(exchange_prices) > 1:
            min_ex = min(exchange_prices, key=exchange_prices.get)
            max_ex = max(exchange_prices, key=exchange_prices.get)
            min_price = exchange_prices[min_ex]
            max_price = exchange_prices[max_ex]

            if min_price > 0:
                profit_percent = ((max_price - min_price) / min_price) * 100
                profit_percent = round(profit_percent, 2)  # ✅ FOYDA YAXLITLANADI

                if profit_percent > 1:
                    opportunities.append({
                        "symbol": symbol,
                        "buy": min_ex.capitalize(),
                        "sell": max_ex.capitalize(),
                        "buy_price": min_price,
                        "sell_price": max_price,
                        "profit": profit_percent
                    })

    return opportunities

# 🔹 Arbitrage natijalarini chiqarish (Vaqtinchalik yuklanmoqda xabarini o‘chirib)
def send_telegram_alerts(chat_id, loading_message_id):
    prices = fetch_prices()
    opportunities = find_arbitrage_opportunities(prices)

    # ⏳ "Yuklanmoqda..." xabarini o‘chirib tashlaymiz
    bot.delete_message(chat_id, loading_message_id)

    if opportunities:
        opp = opportunities[0]  # Faqat 1 ta natija yuboriladi
        message = (
            f"🔥 **Arbitrage Opportunity** 🔥\n\n"
            f"💰 **{opp['symbol']}**\n"
            f"🔹 Buy on **{opp['buy']}** at `{opp['buy_price']:.2f} USDT`\n"
            f"🔹 Sell on **{opp['sell']}** at `{opp['sell_price']:.2f} USDT`\n"
            f"📈 **Profit:** `{opp['profit']}%`"  # ✅ FOYDA YAXLITLANIB CHIQARILADI
        )

        markup = InlineKeyboardMarkup()
        more_info_btn = InlineKeyboardButton("ℹ️ Ko‘proq ma’lumot", callback_data=f"info_{opp['symbol']}")
        markup.add(more_info_btn)

        bot.send_message(chat_id, message, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⚠️ Hozircha foydali arbitraj topilmadi.", parse_mode="Markdown")

# 🔹 Arbitrage tekshirish tugmasi
@bot.message_handler(func=lambda message: message.text == "🔍 Arbitrage Tekshirish")
def check_arbitrage(message):
    # ⏳ Yuklanmoqda xabarini yuboramiz va ID sini saqlab qo‘yamiz
    loading_message = bot.send_message(message.chat.id, "⏳ Arbitrage ma’lumotlari yuklanmoqda...")
    
    # Yangi ma’lumotlarni chiqarish
    send_telegram_alerts(message.chat.id, loading_message.message_id)

# 🔹 Tugmalarni boshqarish (Ko‘proq ma’lumot)
@bot.callback_query_handler(func=lambda call: call.data.startswith("info_"))
def callback_info(call):
    symbol = call.data.split("_")[1]
    bot.answer_callback_query(call.id, f"{symbol} haqida qo‘shimcha ma’lumot...")
    
    google_url = f"https://www.google.com/search?q={symbol}+crypto+price"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔍 Google'da qidirish", url=google_url))

    bot.edit_message_text(
        f"📊 **{symbol} haqida ma’lumot:**\n\n"
        f"🔗 [Google'da qidirish]({google_url})",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# 🔹 Botni ishga tushirish
print("✅ Bot ishga tushdi!")
bot.polling(none_stop=True)
