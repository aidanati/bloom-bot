import asyncio
import json
import os
from datetime import date
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8907663431:AAFgs1SM9sdWTGuG2V7519IPmplpHioqxBU"
CHAT_ID = 74161606

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_key():
    return str(date.today())

def get_today(data):
    key = today_key()
    if key not in data:
        data[key] = {
            "water": 0, "coffee": False,
            "vitamins": {"d3": False, "c": False, "omega": False, "chlor": False,
                         "lec1": False, "lec2": False, "lec3": False, "mg": False},
            "steps": 0, "workout": False, "mood": None, "wellbeing": None,
            "weight": None, "note": ""
        }
    return data[key]

def water_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="+ стакан воды 💧", callback_data="water_add"),
        InlineKeyboardButton(text="Сводка /today", callback_data="today"),
    ]])

def morning_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выпила воду 💧", callback_data="water_add")],
        [InlineKeyboardButton(text="D3 ✓", callback_data="vit_d3"),
         InlineKeyboardButton(text="Витамин С ✓", callback_data="vit_c")],
        [InlineKeyboardButton(text="Омега-3 ✓", callback_data="vit_omega"),
         InlineKeyboardButton(text="Хлорофилл ✓", callback_data="vit_chlor")],
    ])

def lecithin_kb(meal):
    labels = {"1": "завтраком", "2": "обедом", "3": "ужином"}
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"Лецитин с {labels[meal]} ✓", callback_data=f"vit_lec{meal}")
    ]])

def mood_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="😴", callback_data="mood_1"),
        InlineKeyboardButton(text="😕", callback_data="mood_2"),
        InlineKeyboardButton(text="😊", callback_data="mood_3"),
        InlineKeyboardButton(text="😄", callback_data="mood_4"),
        InlineKeyboardButton(text="✨", callback_data="mood_5"),
    ]])

def workout_kb(name):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"✓ Выполнила: {name}", callback_data="workout_done"),
        InlineKeyboardButton(text="Пропускаю", callback_data="workout_skip"),
    ]])

def magnesium_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Магний принят 🌙", callback_data="vit_mg"),
    ]])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "Привет, Айдана! 🌿\n\n"
        "Я твой wellness-помощник Bloom.\n\n"
        "Команды:\n"
        "/today — сводка дня\n"
        "/water — добавить стакан воды\n"
        "/steps 4500 — записать шаги\n"
        "/weight 74.5 — записать вес\n"
        "/checkin — вечерний чекин\n"
        "/week — статистика за неделю"
    )

@dp.message(Command("water"))
async def cmd_water(msg: Message):
    data = load_data()
    today = get_today(data)
    today["water"] += 250
    save_data(data)
    glasses = today["water"] // 250
    bar = "🟦" * glasses + "⬜" * max(0, 8 - glasses)
    await msg.answer(f"Записала 💧\n{bar}\n{today['water']} мл из 2000 мл", reply_markup=water_kb())

@dp.message(Command("steps"))
async def cmd_steps(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Напиши так: /steps 4500")
        return
    try:
        steps = int(parts[1])
    except ValueError:
        await msg.answer("Не поняла число, попробуй ещё раз")
        return
    data = load_data()
    today = get_today(data)
    today["steps"] = steps
    save_data(data)
    bar = "🟩" * min(10, steps // 500) + "⬜" * max(0, 10 - steps // 500)
    text = f"Шаги записаны 👟\n{bar}\n{steps} из 5000"
    if steps >= 5000:
        text += "\n\nЦель дня выполнена! 🎉"
    await msg.answer(text)

@dp.message(Command("weight"))
async def cmd_weight(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Напиши так: /weight 74.5")
        return
    try:
        kg = float(parts[1].replace(",", "."))
    except ValueError:
        await msg.answer("Не поняла число")
        return
    data = load_data()
    today = get_today(data)
    today["weight"] = kg
    save_data(data)
    all_keys = sorted(k for k in data.keys() if k != today_key())
    prev_weight = None
    for k in reversed(all_keys):
        if data[k].get("weight"):
            prev_weight = data[k]["weight"]
            break
    if prev_weight:
        diff = round(kg - prev_weight, 1)
        sign = "+" if diff > 0 else ""
        await msg.answer(f"Вес {kg} кг записан 📊\nИзменение: {sign}{diff} кг")
    else:
        await msg.answer(f"Вес {kg} кг записан — старт взят! 🌱")

@dp.message(Command("today"))
async def cmd_today(msg: Message):
    data = load_data()
    today = get_today(data)
    glasses = today["water"] // 250
    water_bar = "🟦" * glasses + "⬜" * max(0, 8 - glasses)
    v = today["vitamins"]
    mood_map = {1:"😴", 2:"😕", 3:"😊", 4:"😄", 5:"✨", None:"—"}
    steps = today.get("steps", 0)
    steps_bar = "🟩" * min(10, steps // 500) + "⬜" * max(0, 10 - steps // 500)
    text = (
        f"Сводка за сегодня 🌿\n\n"
        f"💧 Вода: {water_bar}\n"
        f"   {today['water']} мл из 2000 мл\n\n"
        f"👟 Шаги: {steps_bar}\n"
        f"   {steps} из 5000\n\n"
        f"💊 Витамины утро:\n"
        f"   D3 {'✅' if v['d3'] else '⬜'}  "
        f"Витамин С {'✅' if v['c'] else '⬜'}  "
        f"Омега {'✅' if v['omega'] else '⬜'}  "
        f"Хлорофилл {'✅' if v['chlor'] else '⬜'}\n\n"
        f"🧠 Лецитин:\n"
        f"   Завтрак {'✅' if v['lec1'] else '⬜'}  "
        f"Обед {'✅' if v['lec2'] else '⬜'}  "
        f"Ужин {'✅' if v['lec3'] else '⬜'}\n\n"
        f"🌙 Магний: {'✅' if v['mg'] else '⬜'}\n\n"
        f"🏃 Тренировка: {'✅ выполнена' if today['workout'] else '⬜ ещё нет'}\n"
        f"🌸 Настроение: {mood_map[today['mood']]}\n"
        f"⭐ Самочувствие: {today['wellbeing'] or '—'}/10"
    )
    await msg.answer(text)

@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    await msg.answer("Как настроение сегодня? 🌸", reply_markup=mood_kb())

@dp.message(Command("week"))
async def cmd_week(msg: Message):
    data = load_data()
    keys = sorted(data.keys())[-7:]
    if not keys:
        await msg.answer("Данных пока нет — начнём сегодня! 🌱")
        return
    lines = []
    for k in keys:
        d = data[k]
        w = d.get("weight", "—")
        steps = d.get("steps", 0)
        glasses = d["water"] // 250
        lines.append(f"{k}: 💧{glasses}/8  👟{steps}  {'🏃' if d['workout'] else '—'}  {w} кг")
    await msg.answer("Последние 7 дней:\n\n" + "\n".join(lines))

@dp.callback_query(F.data == "water_add")
async def cb_water(cb: CallbackQuery):
    data = load_data()
    today = get_today(data)
    today["water"] += 250
    save_data(data)
    glasses = today["water"] // 250
    bar = "🟦" * glasses + "⬜" * max(0, 8 - glasses)
    await cb.answer(f"+250 мл · всего {today['water']} мл")
    await cb.message.edit_text(f"Записала 💧\n{bar}\n{today['water']} мл из 2000 мл", reply_markup=water_kb())

@dp.callback_query(F.data.startswith("vit_"))
async def cb_vitamin(cb: CallbackQuery):
    key = cb.data.replace("vit_", "")
    data = load_data()
    today = get_today(data)
    today["vitamins"][key] = True
    save_data(data)
    names = {
        "d3": "Витамин D3 ☀️", "c": "Витамин С 🍊",
        "omega": "Омега-3 🐟", "chlor": "Хлорофилл 🌿",
        "lec1": "Лецитин (завтрак) 🧠", "lec2": "Лецитин (обед) 🧠",
        "lec3": "Лецитин (ужин) 🧠", "mg": "Магний 🌙"
    }
    await cb.answer(f"{names.get(key, key)} принят!")
    await cb.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(F.data == "workout_done")
async def cb_workout_done(cb: CallbackQuery):
    data = load_data()
    today = get_today(data)
    today["workout"] = True
    save_data(data)
    await cb.answer("Тренировка засчитана! 🌟")
    await cb.message.edit_text("Тренировка выполнена — ты молодец! 💪🌿")

@dp.callback_query(F.data == "workout_skip")
async def cb_workout_skip(cb: CallbackQuery):
    await cb.answer("Окей!")
    await cb.message.edit_text("Всё ок — отдых тоже часть плана 🫶")

@dp.callback_query(F.data.startswith("mood_"))
async def cb_mood(cb: CallbackQuery):
    score = int(cb.data.split("_")[1])
    data = load_data()
    today = get_today(data)
    today["mood"] = score
    save_data(data)
    await cb.answer("Настроение записано!")
    wb_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"wb_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(text=str(i), callback_data=f"wb_{i}") for i in range(6, 11)],
    ])
    await cb.message.answer("Самочувствие от 1 до 10:", reply_markup=wb_kb)

@dp.callback_query(F.data.startswith("wb_"))
async def cb_wellbeing(cb: CallbackQuery):
    score = int(cb.data.split("_")[1])
    data = load_data()
    today = get_today(data)
    today["wellbeing"] = score
    save_data(data)
    texts = {range(1,4): "Береги себя сегодня 🤍", range(4,7): "Надеюсь, будет лучше 💛", range(7,11): "Отличное самочувствие! ✨"}
    text = next((v for k, v in texts.items() if score in k), "")
    await cb.answer("Записала!")
    await cb.message.edit_text(f"Самочувствие {score}/10. {text}")

@dp.callback_query(F.data == "today")
async def cb_today(cb: CallbackQuery):
    await cb.answer()
    await cmd_today(cb.message)

WORKOUTS = {
    1: ("Бачата сегодня в 20:00 💃", "бачата"),
    2: ("Беговая дорожка — 35-40 мин 🏃", "дорожка"),
    3: ("Бачата сегодня в 20:00 💃", "бачата"),
    4: ("Ходьба + растяжка дома 🧘", "растяжка"),
    5: None,
    6: ("Дорожка или танцы дома 🏃", "дорожка"),
    0: None,
}

def setup_reminders():
    async def send(text, kb=None):
        await bot.send_message(CHAT_ID, text, reply_markup=kb)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Доброе утро, Айдана! Сначала хлорофилл натощак 🌿",
             InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Хлорофилл ✓ 🌿", callback_data="vit_chlor")]]))
    ), "cron", hour=7, minute=30)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Стакан воды и утренние витамины! 💊", morning_kb())
    ), "cron", hour=8, minute=0)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Лецитин с завтраком! 🧠", lecithin_kb("1"))
    ), "cron", hour=9, minute=0)

    water_msgs = {
        10: "Уже 10 утра — пора выпить воды 💧",
        12: "Середина дня, не забудь про воду 💧",
        14: "Стакан воды сейчас = хорошее самочувствие 💛",
        16: "16:00 — вода и небольшой перерыв ✨",
        18: "Ещё один стакан воды 💧",
        20: "Последний стакан воды на сегодня 🌙",
    }
    for hour, msg in water_msgs.items():
        scheduler.add_job(
            lambda m=msg: asyncio.create_task(send(m, water_kb())),
            "cron", hour=hour, minute=0
        )

    scheduler.add_job(lambda: asyncio.create_task(
        send("Лецитин с обедом! 🧠", lecithin_kb("2"))
    ), "cron", hour=13, minute=0)

    async def workout_reminder():
        from datetime import datetime
        dow = datetime.now().isoweekday()
        info = WORKOUTS.get(dow % 7)
        if info:
            title, name = info
            await send(f"Тренировка сегодня:\n{title}\n\nНебольшое движение = минус стресс 💛", workout_kb(name))
        else:
            await send("Сегодня день отдыха — заслуженно! 🛌")

    scheduler.add_job(lambda: asyncio.create_task(workout_reminder()), "cron", hour=10, minute=0)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Через час бачата 💃 Возьми воду с собой!")
    ), "cron", day_of_week="mon,wed", hour=19, minute=0)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Лецитин с ужином! 🧠", lecithin_kb("3"))
    ), "cron", hour=19, minute=30)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Время вечернего магния 🌙", magnesium_kb())
    ), "cron", hour=21, minute=0)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Как прошёл день, Айдана? 🌸", mood_kb())
    ), "cron", hour=21, minute=30)

    scheduler.add_job(lambda: asyncio.create_task(
        send("Пора готовиться ко сну 🌙 Хорошего отдыха!")
    ), "cron", hour=23, minute=0)

async def main():
    setup_reminders()
    scheduler.start()
    print("Bloom bot запущен! 🌿")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
