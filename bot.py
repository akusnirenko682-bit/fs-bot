import telebot
from telebot import types
import json, os, random
from mods_data import MODS
from flask import Flask
from threading import Thread

# ===== Flask-сервер для Render =====
app = Flask('')

@app.route('/')
def home():
    return "Бот работает! 🚜"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# =====================================

TOKEN = "9019511212:AAHn2aFpHFCDpcx74hu-VLi_INchc5ZgFbM"
ADMIN_ID = 8338661047
EXTRA_FILE = "mods_extra.json"

bot = telebot.TeleBot(TOKEN)

def load_extra():
    try:
        with open(EXTRA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_extra():
    try:
        extra = [m for m in MODS if m.get("extra")]
        with open(EXTRA_FILE, "w", encoding="utf-8") as f:
            json.dump(extra, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Ошибка сохранения:", e)

MODS += load_extra()
user_state = {}

def search_mods(query):
    words = query.lower().split()
    results = []
    for mod in MODS:
        text = (mod["name"] + " " + mod["cat"] + " " + mod["desc"]).lower()
        if all(w in text for w in words):
            results.append(mod)
    return results

def send_mod_list(chat_id, mods, page=1, per_page=10):
    total_pages = (len(mods) + per_page - 1) // per_page
    start = (page - 1) * per_page
    page_mods = mods[start:start + per_page]
    if not page_mods:
        bot.send_message(chat_id, "😕 Ничего не найдено")
        return
    text = f"🔎 Найдено <b>{len(mods)}</b> модов (стр. {page}/{total_pages}):\n\n"
    keyboard = types.InlineKeyboardMarkup()
    for i, mod in enumerate(page_mods, start + 1):
        text += f"{i}. 📦 <b>{mod['name']}</b> ({mod['game']})\n   🏷 {mod['cat']} — {mod['desc']}\n\n"
        keyboard.add(types.InlineKeyboardButton(f"⬇️ {mod['name'][:25]}", url=mod['link']))
    nav = []
    if page > 1:
        nav.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"prev_{page-1}"))
    if page < total_pages:
        nav.append(types.InlineKeyboardButton("Далее ▶️", callback_data=f"next_{page+1}"))
    if nav:
        keyboard.add(*nav)
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
    user_state[chat_id] = {"mods": mods, "page": page, "per_page": per_page}

@bot.callback_query_handler(func=lambda call: call.data.startswith("prev_") or call.data.startswith("next_"))
def handle_pagination(call):
    chat_id = call.message.chat.id
    st = user_state.get(chat_id)
    if not st:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    page = int(call.data.split("_")[1])
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except Exception:
        pass
    send_mod_list(chat_id, st["mods"], page, st["per_page"])
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['start'])
def start(m):
    text = (f"🚜 <b>Привет, фермер!</b>\n\n"
            f"📊 В базе: <b>{len(MODS)}</b> модов\n\n"
            "📌 <b>Поиск:</b>\n"
            "/search слово — умный поиск\n"
            "/random — случайный мод\n"
            "/stats — статистика\n\n"
            "📌 <b>Фильтры:</b>\n"
            "/fs20 • /fs22 • /tractors • /combines • /maps • /trucks\n\n"
            "📌 <b>Моё:</b>\n"
            "/save номер • /saved • /unsave номер\n\n"
            "/help — все команды")
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['search'])
def search_cmd(m):
    words = m.text.split()[1:]
    if not words:
        bot.send_message(m.chat.id, "❗ Напиши: /search запрос")
        return
    query = " ".join(words).lower()
    results = search_mods(query)
    if not results:
        bot.send_message(m.chat.id, f"😕 Ничего не найдено по запросу: <b>{query}</b>", parse_mode="HTML")
        return
    send_mod_list(m.chat.id, results)

@bot.message_handler(commands=['fs20'])
def fs20(m):
    results = [x for x in MODS if x["game"] == "FS20"]
    if results:
        send_mod_list(m.chat.id, results)
    else:
        bot.send_message(m.chat.id, "😕 Нет модов для FS20")

@bot.message_handler(commands=['fs22'])
def fs22(m):
    results = [x for x in MODS if x["game"] == "FS22"]
    if results:
        send_mod_list(m.chat.id, results)
    else:
        bot.send_message(m.chat.id, "😕 Нет модов для FS22")

@bot.message_handler(commands=['tractors'])
def tractors(m):
    results = [x for x in MODS if x["cat"] == "Трактор"]
    if results:
        send_mod_list(m.chat.id, results)
    else:
        bot.send_message(m.chat.id, "😕 Тракторов нет")

@bot.message_handler(commands=['combines'])
def combines(m):
    results = [x for x in MODS if x["cat"] == "Комбайн"]
    if results:
        send_mod_list(m.chat.id, results)
    else:
        bot.send_message(m.chat.id, "😕 Комбайнов нет")

@bot.message_handler(commands=['maps'])
def maps(m):
    results = [x for x in MODS if x["cat"] == "Карта"]
    if results:
        send_mod_list(m.chat.id, results)
    else:
        bot.send_message(m.chat.id, "😕 Карт нет")

@bot.message_handler(commands=['trucks'])
def trucks(m):
    results = [x for x in MODS if x["cat"] == "Грузовик"]
    if results:
        send_mod_list(m.chat.id, results)
    else:
        bot.send_message(m.chat.id, "😕 Грузовиков нет")

@bot.message_handler(commands=['random'])
def random_mod(m):
    mod = random.choice(MODS)
    text = (f"🎲 <b>Случайный мод:</b>\n\n"
            f"📦 <b>{mod['name']}</b> ({mod['game']})\n"
            f"🏷 {mod['cat']} — {mod['desc']}")
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬇️ Скачать мод", url=mod['link']))
    bot.send_message(m.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

@bot.message_handler(commands=['stats'])
def stats(m):
    total = len(MODS)
    vers = {}
    cats = {}
    for mod in MODS:
        vers[mod["game"]] = vers.get(mod["game"], 0) + 1
        cats[mod["cat"]] = cats.get(mod["cat"], 0) + 1
    text = f"📊 <b>Статистика базы:</b>\n\n🔢 <b>Всего:</b> {total}\n\n🎮 <b>По версиям:</b>\n"
    for v, n in sorted(vers.items(), key=lambda x: -x[1]):
        text += f"• {v}: {n}\n"
    text += "\n🏷 <b>Топ категорий:</b>\n"
    for c, n in sorted(cats.items(), key=lambda x: -x[1])[:8]:
        text += f"• {c}: {n}\n"
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['new'])
def new_mods(m):
    last = MODS[-10:]
    text = "🆕 <b>Последние 10 модов:</b>\n\n"
    keyboard = types.InlineKeyboardMarkup()
    for mod in last:
        text += f"📦 <b>{mod['name']}</b> ({mod['game']})\n   🏷 {mod['cat']}\n\n"
        keyboard.add(types.InlineKeyboardButton(f"⬇️ {mod['name'][:25]}", url=mod['link']))
    bot.send_message(m.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

@bot.message_handler(commands=['save'])
def save_mod(m):
    st = user_state.get(m.chat.id)
    if not st or not st.get("mods"):
        bot.send_message(m.chat.id, "❗ Сначала найди моды через /search, потом /save номер")
        return
    try:
        mod = st["mods"][int(m.text.split()[1]) - 1]
    except Exception:
        bot.send_message(m.chat.id, "❗ Напиши: /save номер")
        return
    saved = user_state.setdefault(m.chat.id, {}).setdefault("saved", [])
    if any(s["name"] == mod["name"] for s in saved):
        bot.send_message(m.chat.id, f"⭐ <b>{mod['name']}</b> уже в избранном!", parse_mode="HTML")
        return
    saved.append(mod)
    bot.send_message(m.chat.id, f"⭐ Сохранено: <b>{mod['name']}</b>\nВ избранном: {len(saved)}", parse_mode="HTML")

@bot.message_handler(commands=['saved'])
def show_saved(m):
    saved = user_state.get(m.chat.id, {}).get("saved", [])
    if not saved:
        bot.send_message(m.chat.id, "📭 Избранное пусто. Добавляй через /save номер")
        return
    text = f"⭐ <b>Избранное</b> ({len(saved)}):\n\n"
    keyboard = types.InlineKeyboardMarkup()
    for i, mod in enumerate(saved, 1):
        text += f"{i}. 📦 <b>{mod['name']}</b> ({mod['game']})\n   🏷 {mod['cat']}\n\n"
        keyboard.add(types.InlineKeyboardButton(f"⬇️ {mod['name'][:25]}", url=mod['link']))
    bot.send_message(m.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

@bot.message_handler(commands=['unsave'])
def unsave_mod(m):
    saved = user_state.get(m.chat.id, {}).get("saved", [])
    try:
        removed = saved.pop(int(m.text.split()[1]) - 1)
        bot.send_message(m.chat.id, f"🗑 Удалено: <b>{removed['name']}</b>", parse_mode="HTML")
    except Exception:
        bot.send_message(m.chat.id, "❗ Напиши: /unsave номер")

@bot.message_handler(commands=['version'])
def by_version(m):
    args = m.text.split()[1:]
    if not args:
        bot.send_message(m.chat.id, "❗ Напиши: /version fs20")
        return
    ver = args[0].upper()
    results = [x for x in MODS if x["game"] == ver]
    if not results:
        bot.send_message(m.chat.id, f"😕 Версии {ver} нет. Смотри /versions")
        return
    send_mod_list(m.chat.id, results)

@bot.message_handler(commands=['category'])
def by_category(m):
    args = m.text.split()[1:]
    if not args:
        bot.send_message(m.chat.id, "❗ Напиши: /category трактор")
        return
    cat = " ".join(args).lower()
    results = [x for x in MODS if cat in x["cat"].lower()]
    if not results:
        bot.send_message(m.chat.id, f"😕 Категории «{cat}» нет. Смотри /categories")
        return
    send_mod_list(m.chat.id, results)

@bot.message_handler(commands=['categories'])
def all_categories(m):
    cats = {}
    for mod in MODS:
        cats[mod["cat"]] = cats.get(mod["cat"], 0) + 1
    text = "🏷 <b>Все категории:</b>\n\n"
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        text += f"• {c} — {n} шт ( /category {c.lower()} )\n"
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['versions'])
def all_versions(m):
    vers = {}
    for mod in MODS:
        vers[mod["game"]] = vers.get(mod["game"], 0) + 1
    text = "🎮 <b>Все версии:</b>\n\n"
    for v, n in sorted(vers.items(), key=lambda x: -x[1]):
        text += f"• {v} — {n} шт ( /version {v.lower()} )\n"
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['similar'])
def similar(m):
    st = user_state.get(m.chat.id)
    if not st or not st.get("mods"):
        bot.send_message(m.chat.id, "❗ Сначала /search, потом /similar номер")
        return
    try:
        mod = st["mods"][int(m.text.split()[1]) - 1]
    except Exception:
        bot.send_message(m.chat.id, "❗ Напиши: /similar номер")
        return
    results = [x for x in MODS if x["cat"] == mod["cat"] and x["game"] == mod["game"] and x is not mod]
    if not results:
        bot.send_message(m.chat.id, f"😕 Похожих на «{mod['name']}» нет")
        return
    send_mod_list(m.chat.id, results)

@bot.message_handler(commands=['addmod'])
def add_mod(m):
    if m.from_user.id != ADMIN_ID:
        bot.send_message(m.chat.id, "🔒 Только для админа")
        return
    parts = m.text.split(" ", 1)
    if len(parts) < 2 or "|" not in parts[1]:
        bot.send_message(m.chat.id, "❗ Формат:\n/addmod Название|FS20|Трактор|Описание|ссылка")
        return
    fields = [p.strip() for p in parts[1].split("|")]
    if len(fields) < 5:
        bot.send_message(m.chat.id, "❗ Нужно 5 частей через |")
        return
    mod = {"name": fields[0], "game": fields[1], "cat": fields[2],
           "desc": fields[3], "link": fields[4], "extra": True}
    MODS.append(mod)
    save_extra()
    bot.send_message(m.chat.id, f"✅ Добавлено: <b>{mod['name']}</b>\nВ базе: {len(MODS)} модов", parse_mode="HTML")

@bot.message_handler(commands=['delmod'])
def del_mod(m):
    if m.from_user.id != ADMIN_ID:
        bot.send_message(m.chat.id, "🔒 Только для админа")
        return
    query = " ".join(m.text.split()[1:]).lower()
    if not query:
        bot.send_message(m.chat.id, "❗ Напиши: /delmod название")
        return
    to_del = [x for x in MODS if x.get("extra") and query in x["name"].lower()]
    if not to_del:
        bot.send_message(m.chat.id, "😕 Ничего не найдено")
        return
    for x in to_del:
        MODS.remove(x)
    save_extra()
    bot.send_message(m.chat.id, f"🗑 Удалено {len(to_del)} модов. В базе: {len(MODS)}")

@bot.message_handler(commands=['id'])
def show_id(m):
    bot.send_message(m.chat.id, f"🆔 Твой ID: <code>{m.from_user.id}</code>", parse_mode="HTML")

@bot.message_handler(commands=['info'])
def info(m):
    bot.send_message(m.chat.id, f"🚜 <b>FS Mod Finder</b>\n\nВ базе: {len(MODS)} модов\nВерсий: {len(set(x['game'] for x in MODS))}\nКатегорий: {len(set(x['cat'] for x in MODS))}\n\nСобрано с 🤍 для фермеров.", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    text = ("📖 <b>Справка:</b>\n\n"
            "🔍 /search маз — поиск\n"
            "🎲 /random — случайный мод\n"
            "👯 /similar 3 — похожие на №3\n"
            "🎮 /version fs20 — по версии\n"
            "🏷 /category трактор — по категории\n"
            "⭐ /save 5 — сохранить №5\n"
            "📭 /saved — избранное\n"
            "🗑 /unsave 2 — убрать №2\n"
            "📊 /stats — статистика\n"
            "🆕 /new — последние 10\n"
            "📋 /categories • /versions\n"
            "ℹ️ /info — о боте\n\n"
            "👑 Админу:\n"
            "➕ /addmod Название|FS20|Трактор|Описание|ссылка\n"
            "➖ /delmod название\n"
            "🆔 /id — узнать ID")
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def echo(m):
    bot.send_message(m.chat.id, "🤔 Не понимаю. Напиши /help")

print(f"🚀 Бот запущен! В базе {len(MODS)} модов.")
keep_alive()
bot.polling(none_stop=True)
