from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Состояния для диалога
class SessionDestroy(StatesGroup):
    waiting_for_phone = State()
    waiting_for_reason = State()
    waiting_for_code = State()

# Обработка кнопки "Снос сессий"
@dp.callback_query(F.data == "session_destroy")
async def start_destroy(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📲 **МОДУЛЬ СНОСА V1.0**\n\nВведите номер телефона цели в международном формате (например, +79991234567):")
    await state.set_state(SessionDestroy.waiting_for_phone)

# Получаем номер и предлагаем причины
@dp.message(SessionDestroy.waiting_for_phone)
async def get_phone(message: types.Message, state: FSMContext):
    if not message.text.startswith('+') or not message.text[1:].isdigit():
        return await message.answer("❌ Неверный формат! Номер должен начинаться с + и содержать только цифры.")
    
    await state.update_data(target_phone=message.text)
    
    kb = InlineKeyboardBuilder()
    reasons = ["⚠️ Угрозы", "💸 Мошенничество", "🛡️ Спам/Обман", "🔞 Нарушение правил"]
    for r in reasons:
        kb.button(text=r, callback_data=f"reason_{r}")
    kb.adjust(1)
    
    await message.answer(f"✅ Номер `{message.text}` принят.\nВыберите причину для инициации сброса:", 
                         reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(SessionDestroy.waiting_for_reason)

# Обработка выбора причины и переход к "ожиданию кода"
@dp.callback_query(F.data.startswith("reason_"))
async def get_reason(callback: types.CallbackQuery, state: FSMContext):
    reason = callback.data.split("_")[1]
    data = await state.get_data()
    
    # Кнопка "Жду код" без комментариев
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 ЖДУ КОД", callback_data="wait_code_silent")
    
    await callback.message.answer(
        f"🚀 **ЗАПУСК ПРОЦЕССА...**\n\n"
        f"🎯 Цель: `{data['target_phone']}`\n"
        f"📝 Причина: `{reason}`\n"
        f"🌐 IP инициатора: `{request.remote_addr if request else '127.0.0.1'}`\n\n"
        "Система подключается к серверам авторизации...",
        reply_markup=kb.as_markup(), parse_mode="Markdown"
    )
    # Здесь могла бы быть логика, но мы останавливаемся на интерфейсе
