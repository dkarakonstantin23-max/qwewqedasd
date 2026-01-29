from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import random

# ===== НАСТРОЙКИ =====
TOKEN = "8391281405:AAF51N8yOnvLYt3_HCdL55kONmWVsSgV-m0"
ADMIN_ID = "6680144882"
CARD_NUMBER = "https://send.monobank.ua/jar/5Rg57x14zH"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ===== ЦЕНЫ =====
prices = {
    # КБ
    "kb_solo": 10,
    "kb_duo": 30,
    "kb_squad": 80,

    # СНС
    "sns_solo": 50,
    "sns_duo": 100,
    "sns_squad": 200,

    # Ультиматум
    "ult_solo": 50,
    "ult_duo": 100,

    # Битва отрядов
    "battle_solo": 50,
    "battle_duo": 100,
    "battle_squad": 200
}

# ===== ЛИМИТЫ БИЛЕТОВ =====
ticket_limits = {
    "kb": 48,
    "sns": 2,
    "ult": 2,
    "battle": 2
}

# ===== FSM =====
class Form(StatesGroup):
    tournament = State()
    mode = State()
    players = State()
    receipt = State()

# ===== /start =====
@dp.message_handler(commands="start")
async def start(msg: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🏆 КБ", callback_data="t_kb"),
        types.InlineKeyboardButton("🔥 СНС", callback_data="t_sns"),
        types.InlineKeyboardButton("⚡ Ультиматум", callback_data="t_ult"),
        types.InlineKeyboardButton("⚔️ Битва отрядов", callback_data="t_battle")
    )
    await msg.answer("Выберите турнир:", reply_markup=kb)

# ===== ВЫБОР ТУРНИРА =====
@dp.callback_query_handler(lambda c: c.data.startswith("t_"))
async def choose_tournament(call: types.CallbackQuery, state: FSMContext):
    tournament = call.data.replace("t_", "")
    await state.update_data(tournament=tournament)

    kb = types.InlineKeyboardMarkup(row_width=1)

    if tournament == "kb":
        kb.add(
            types.InlineKeyboardButton("Соло — 10 грн", callback_data="kb_solo"),
            types.InlineKeyboardButton("Дуо — 30 грн", callback_data="kb_duo"),
            types.InlineKeyboardButton("Отряд — 80 грн", callback_data="kb_squad")
        )
    elif tournament == "sns":
        kb.add(
            types.InlineKeyboardButton("Соло — 50 грн", callback_data="sns_solo"),
            types.InlineKeyboardButton("Дуо — 100 грн", callback_data="sns_duo"),
            types.InlineKeyboardButton("Отряд — 200 грн", callback_data="sns_squad")
        )
    elif tournament == "ult":
        kb.add(
            types.InlineKeyboardButton("Соло — 50 грн", callback_data="ult_solo"),
            types.InlineKeyboardButton("Дуо — 100 грн", callback_data="ult_duo")
        )
    elif tournament == "battle":
        kb.add(
            types.InlineKeyboardButton("Соло — 50 грн", callback_data="battle_solo"),
            types.InlineKeyboardButton("Дуо — 100 грн", callback_data="battle_duo"),
            types.InlineKeyboardButton("Отряд — 200 грн", callback_data="battle_squad")
        )

    await call.message.answer("Выберите режим:", reply_markup=kb)
    await call.answer()

# ===== ВЫБОР РЕЖИМА =====
@dp.callback_query_handler(lambda c: c.data in prices)
async def choose_mode(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(mode=call.data)
    await Form.players.set()

    if "solo" in call.data:
        text = "Введите ваш ник и ID"
    elif "duo" in call.data:
        text = "Введите ник и ID двух игроков"
    else:
        text = "Введите ник и ID всех игроков отряда"

    await call.message.answer(text)
    await call.answer()

# ===== ВВОД ИГРОКОВ =====
@dp.message_handler(state=Form.players)
async def players(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    price = prices[data["mode"]]

    info = f"{msg.from_user.full_name} (@{msg.from_user.username})\n{msg.text}"
    await state.update_data(players=info)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Оплатить", callback_data="pay"))

    await msg.answer(f"💰 К оплате: {price} грн", reply_markup=kb)

# ===== ОПЛАТА =====
@dp.callback_query_handler(lambda c: c.data == "pay", state="*")
async def pay(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = prices[data["mode"]]
    await Form.receipt.set()

    await call.message.answer(
        f"💳 Оплата турнира\n\n"
        f"Карта:\n{CARD_NUMBER}\n\n"
        f"Сумма: {price} грн\n\n"
        f"📄 Отправьте квитанцию в формате PDF"
    )
    await call.answer()

# ===== ПОЛУЧЕНИЕ PDF + БИЛЕТ =====
@dp.message_handler(content_types=["document"], state=Form.receipt)
async def receipt(msg: types.Message, state: FSMContext):
    if msg.document.mime_type != "application/pdf":
        await msg.answer("❌ Только PDF файл.")
        return

    data = await state.get_data()
    tournament = data["tournament"]
    mode = data["mode"]
    price = prices[mode]

    max_ticket = ticket_limits[tournament]
    ticket_number = random.randint(1, max_ticket)

    admin_text = (
        "🆕 Новая заявка\n\n"
        f"Турнир: {tournament}\n"
        f"Режим: {mode}\n"
        f"Игроки:\n{data['players']}\n\n"
        f"Сумма: {price} грн\n"
        f"Билет: #{ticket_number}"
    )

    await bot.send_document(ADMIN_ID, msg.document.file_id, caption=admin_text)

    await msg.answer(
        f"🎫 БИЛЕТ ВЫДАН\n\n"
        f"Турнир: {tournament}\n"
        f"Режим: {mode}\n"
        f"Номер билета: #{ticket_number}\n"
        f"Сумма: {price} грн\n\n"
        f"Удачи в турнире!"
    )

    await state.finish()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
