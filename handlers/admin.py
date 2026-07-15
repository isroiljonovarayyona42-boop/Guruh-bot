"""
Admin buyruqlari va FSM holatlari.
Xodimlar, ta'tillar, bayramlar va guruh sozlamalari.
"""
import re
from datetime import date, datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import queries
from utils.messages import (
    format_employee_info,
    format_vacation_info,
    format_holiday_info,
)

router = Router()


# ═══════════════════════════════════════════
# FSM States
# ═══════════════════════════════════════════

class AddEmployee(StatesGroup):
    full_name = State()
    birth_date = State()
    username = State()


class AddVacation(StatesGroup):
    select_employee = State()
    start_date = State()
    end_date = State()


class AddHoliday(StatesGroup):
    holiday_name = State()
    holiday_date = State()
    is_recurring = State()


class SetGroup(StatesGroup):
    group_id = State()


class EditEmployee(StatesGroup):
    employee_id = State()
    full_name = State()
    birth_date = State()
    username = State()


class DeleteEmployee(StatesGroup):
    confirm = State()


class DeleteVacation(StatesGroup):
    confirm = State()


class DeleteHoliday(StatesGroup):
    confirm = State()


class AddAdmin(StatesGroup):
    user_id = State()
    full_name = State()

# ═══════════════════════════════════════════
# Yordamchi funksiyalar
# ═══════════════════════════════════════════

def back_button() -> InlineKeyboardMarkup:
    """Asosiy menyuga qaytish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")]
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])


def validate_mm_dd(text: str) -> bool:
    """MM-DD formatini tekshiradi."""
    try:
        parts = text.strip().split("-")
        if len(parts) != 2:
            return False
        month, day = int(parts[0]), int(parts[1])
        # Sanani tekshirish (2000 yilni foydalanimiz chunki u visokos yil)
        date(2000, month, day)
        return True
    except (ValueError, IndexError):
        return False


def validate_yyyy_mm_dd(text: str) -> bool:
    """YYYY-MM-DD formatini tekshiradi."""
    try:
        datetime.strptime(text.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalize_mm_dd(text: str) -> str:
    """MM-DD formatga keltiradi (01-05 kabi)."""
    parts = text.strip().split("-")
    return f"{int(parts[0]):02d}-{int(parts[1]):02d}"


def normalize_yyyy_mm_dd(text: str) -> str:
    """YYYY-MM-DD formatga keltiradi."""
    dt = datetime.strptime(text.strip(), "%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


# ═══════════════════════════════════════════
# Bekor qilish (barcha FSM'lar uchun)
# ═══════════════════════════════════════════

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Joriy amalni bekor qiladi va menyuga qaytadi."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Amal bekor qilindi.",
        reply_markup=back_button(),
    )
    await callback.answer()


# ═══════════════════════════════════════════
# XODIM QO'SHISH
# ═══════════════════════════════════════════

@router.message(Command("add_employee"))
@router.callback_query(F.data == "menu_add_employee")
async def cmd_add_employee(event: Message | CallbackQuery, state: FSMContext):
    """Xodim qo'shish jarayonini boshlaydi."""
    await state.set_state(AddEmployee.full_name)
    text = "👤 <b>Yangi xodim qo'shish</b>\n\nXodimning to'liq ismini kiriting (F.I.O):"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=cancel_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=cancel_keyboard(), parse_mode="HTML")


@router.message(AddEmployee.full_name)
async def process_employee_name(message: Message, state: FSMContext):
    """Xodim ismi qabul qilindi, tug'ilgan kunni so'raydi."""
    full_name = message.text.strip()
    if len(full_name) < 2:
        await message.answer(
            "⚠️ Ism juda qisqa. Iltimos, to'liq ism kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(full_name=full_name)
    await state.set_state(AddEmployee.birth_date)
    await message.answer(
        f"✅ Ism: <b>{full_name}</b>\n\n"
        "🎂 Tug'ilgan sanani kiriting (MM-DD formatda):\n"
        "Misol: <code>03-15</code> (15-mart)",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(AddEmployee.birth_date)
async def process_employee_birthdate(message: Message, state: FSMContext):
    """Tug'ilgan kun qabul qilindi, username so'raydi."""
    text = message.text.strip()

    if not validate_mm_dd(text):
        await message.answer(
            "⚠️ Noto'g'ri format! MM-DD formatda kiriting.\n"
            "Misol: <code>03-15</code> (15-mart)",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    birth_date = normalize_mm_dd(text)
    await state.update_data(birth_date=birth_date)
    await state.set_state(AddEmployee.username)
    await message.answer(
        f"✅ Tug'ilgan kun: <b>{birth_date}</b>\n\n"
        "📱 Telegram @username ni kiriting (@ belgisisiz):\n"
        "Misol: <code>ali_valiyev</code>\n\n"
        "Agar username bo'lmasa, <b>yo'q</b> deb yozing.",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(AddEmployee.username)
async def process_employee_username(message: Message, state: FSMContext):
    """Username qabul qilindi, xodim bazaga yoziladi."""
    text = message.text.strip().lstrip("@")
    username = None if text.lower() in ("yo'q", "yoq", "-", "none", "") else text

    data = await state.get_data()
    employee_id = await queries.add_employee(
        full_name=data["full_name"],
        username=username,
        birth_date=data["birth_date"],
    )
    await state.clear()

    username_display = f"@{username}" if username else "—"
    await message.answer(
        f"✅ <b>Xodim muvaffaqiyatli qo'shildi!</b>\n\n"
        f"👤 Ism: {data['full_name']}\n"
        f"🎂 Tug'ilgan kun: {data['birth_date']}\n"
        f"📱 Username: {username_display}\n"
        f"🆔 ID: {employee_id}",
        reply_markup=back_button(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════
# XODIMLAR RO'YXATI
# ═══════════════════════════════════════════

@router.message(Command("employees"))
@router.callback_query(F.data.startswith("menu_employees"))
async def cmd_employees(event: Message | CallbackQuery):
    """Barcha xodimlar ro'yxatini ko'rsatadi."""
    employees = await queries.get_all_employees()

    page = 1
    if isinstance(event, CallbackQuery) and event.data.startswith("menu_employees_"):
        try:
            page = int(event.data.split("_")[-1])
        except ValueError:
            page = 1

    if not employees:
        text = "📋 Xodimlar ro'yxati bo'sh.\n\nAvval /add_employee buyrug'i bilan xodim qo'shing."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")]
        ])
    else:
        ITEMS_PER_PAGE = 10
        total_pages = (len(employees) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
            
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_employees = employees[start_idx:end_idx]

        text = f"📋 <b>Xodimlar ro'yxati</b> ({len(employees)} ta):\n"
        if total_pages > 1:
            text += f"📄 Sahifa {page}/{total_pages}\n"
        text += "\n"
        
        for i, emp in enumerate(current_employees, start_idx + 1):
            text += format_employee_info(emp, i) + "\n\n"

        keyboard_rows = []
        for emp in current_employees:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"✏️ {emp['full_name']}",
                    callback_data=f"edit_emp_{emp['id']}",
                ),
                InlineKeyboardButton(
                    text=f"🗑 O'chirish",
                    callback_data=f"del_emp_{emp['id']}",
                ),
            ])
            
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"menu_employees_{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"menu_employees_{page+1}"))
            
        if nav_buttons:
            keyboard_rows.append(nav_buttons)
            
        keyboard_rows.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ─── Xodimni o'chirish ───

@router.callback_query(F.data.startswith("del_emp_"))
async def confirm_delete_employee(callback: CallbackQuery, state: FSMContext):
    """Xodimni o'chirish uchun tasdiqlash."""
    emp_id = int(callback.data.split("_")[-1])
    emp = await queries.get_employee(emp_id)

    if not emp:
        await callback.answer("Xodim topilmadi!", show_alert=True)
        return

    await state.set_state(DeleteEmployee.confirm)
    await state.update_data(delete_emp_id=emp_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_del_emp_{emp_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="menu_employees"),
        ]
    ])

    await callback.message.edit_text(
        f"⚠️ <b>Rostdan ham o'chirmoqchimisiz?</b>\n\n"
        f"👤 {emp['full_name']}\n"
        f"🎂 {emp['birth_date']}\n\n"
        f"Bu xodimning barcha ta'tillari ham o'chiriladi!",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_emp_"))
async def execute_delete_employee(callback: CallbackQuery, state: FSMContext):
    """Xodimni o'chiradi."""
    emp_id = int(callback.data.split("_")[-1])
    success = await queries.delete_employee(emp_id)
    await state.clear()

    if success:
        await callback.message.edit_text(
            "✅ Xodim muvaffaqiyatli o'chirildi.",
            reply_markup=back_button(),
        )
    else:
        await callback.message.edit_text(
            "❌ Xodim topilmadi yoki allaqachon o'chirilgan.",
            reply_markup=back_button(),
        )
    await callback.answer()


# ─── Xodimni tahrirlash ───

@router.callback_query(F.data.startswith("edit_emp_"))
async def start_edit_employee(callback: CallbackQuery, state: FSMContext):
    """Xodim tahrirlashni boshlaydi."""
    emp_id = int(callback.data.split("_")[-1])
    emp = await queries.get_employee(emp_id)

    if not emp:
        await callback.answer("Xodim topilmadi!", show_alert=True)
        return

    await state.set_state(EditEmployee.full_name)
    await state.update_data(edit_emp_id=emp_id, old_data=emp)

    await callback.message.edit_text(
        f"✏️ <b>Xodimni tahrirlash</b>\n\n"
        f"Hozirgi ma'lumotlar:\n"
        f"👤 Ism: {emp['full_name']}\n"
        f"🎂 Tug'ilgan kun: {emp['birth_date']}\n"
        f"📱 Username: {'@' + emp['username'] if emp.get('username') else '—'}\n\n"
        f"Yangi ismni kiriting (o'zgartirmaslik uchun <b>-</b> yozing):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EditEmployee.full_name)
async def edit_employee_name(message: Message, state: FSMContext):
    """Tahrirlash: ism."""
    text = message.text.strip()
    data = await state.get_data()
    old = data["old_data"]

    new_name = old["full_name"] if text == "-" else text
    await state.update_data(new_full_name=new_name)
    await state.set_state(EditEmployee.birth_date)

    await message.answer(
        f"✅ Ism: <b>{new_name}</b>\n\n"
        f"🎂 Yangi tug'ilgan sanani kiriting (MM-DD):\n"
        f"O'zgartirmaslik uchun <b>-</b> yozing.\n"
        f"Hozirgi: {old['birth_date']}",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(EditEmployee.birth_date)
async def edit_employee_birthdate(message: Message, state: FSMContext):
    """Tahrirlash: tug'ilgan kun."""
    text = message.text.strip()
    data = await state.get_data()
    old = data["old_data"]

    if text == "-":
        new_birth = old["birth_date"]
    else:
        if not validate_mm_dd(text):
            await message.answer(
                "⚠️ Noto'g'ri format! MM-DD formatda kiriting yoki <b>-</b> yozing.",
                reply_markup=cancel_keyboard(),
                parse_mode="HTML",
            )
            return
        new_birth = normalize_mm_dd(text)

    await state.update_data(new_birth_date=new_birth)
    await state.set_state(EditEmployee.username)

    await message.answer(
        f"✅ Tug'ilgan kun: <b>{new_birth}</b>\n\n"
        f"📱 Yangi username kiriting (@ belgisisiz):\n"
        f"O'zgartirmaslik uchun <b>-</b> yozing.\n"
        f"Hozirgi: {'@' + old['username'] if old.get('username') else '—'}",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(EditEmployee.username)
async def edit_employee_username(message: Message, state: FSMContext):
    """Tahrirlash: username va saqlash."""
    text = message.text.strip().lstrip("@")
    data = await state.get_data()
    old = data["old_data"]

    if text == "-":
        new_username = old.get("username")
    elif text.lower() in ("yo'q", "yoq", "none"):
        new_username = None
    else:
        new_username = text

    emp_id = data["edit_emp_id"]
    await queries.update_employee(
        employee_id=emp_id,
        full_name=data["new_full_name"],
        username=new_username,
        birth_date=data["new_birth_date"],
    )
    await state.clear()

    username_display = f"@{new_username}" if new_username else "—"
    await message.answer(
        f"✅ <b>Xodim muvaffaqiyatli yangilandi!</b>\n\n"
        f"👤 Ism: {data['new_full_name']}\n"
        f"🎂 Tug'ilgan kun: {data['new_birth_date']}\n"
        f"📱 Username: {username_display}",
        reply_markup=back_button(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════
# TA'TIL QO'SHISH
# ═══════════════════════════════════════════

@router.message(Command("add_vacation"))
@router.callback_query(F.data == "menu_add_vacation")
async def cmd_add_vacation(event: Message | CallbackQuery, state: FSMContext):
    """Ta'til qo'shish jarayonini boshlaydi."""
    employees = await queries.get_all_employees()

    if not employees:
        text = "⚠️ Avval xodim qo'shing! /add_employee"
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=back_button())
            await event.answer()
        else:
            await event.answer(text, reply_markup=back_button())
        return

    await state.set_state(AddVacation.select_employee)

    # Xodimlarni tanlash tugmalari
    keyboard_rows = []
    for emp in employees:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"👤 {emp['full_name']}",
                callback_data=f"vac_emp_{emp['id']}",
            )
        ])
    keyboard_rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    text = "🏖 <b>Ta'til qo'shish</b>\n\nQaysi xodimga ta'til qo'shmoqchisiz?"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("vac_emp_"), AddVacation.select_employee)
async def vacation_employee_selected(callback: CallbackQuery, state: FSMContext):
    """Xodim tanlandi, boshlanish sanasini so'raydi."""
    emp_id = int(callback.data.split("_")[-1])
    emp = await queries.get_employee(emp_id)

    if not emp:
        await callback.answer("Xodim topilmadi!", show_alert=True)
        return

    await state.update_data(vacation_emp_id=emp_id, vacation_emp_name=emp["full_name"])
    await state.set_state(AddVacation.start_date)

    await callback.message.edit_text(
        f"✅ Xodim: <b>{emp['full_name']}</b>\n\n"
        f"📅 Ta'til <b>boshlanish</b> sanasini kiriting (YYYY-MM-DD):\n"
        f"Misol: <code>2025-07-15</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddVacation.start_date)
async def process_vacation_start(message: Message, state: FSMContext):
    """Ta'til boshlanish sanasi qabul qilindi."""
    text = message.text.strip()

    if not validate_yyyy_mm_dd(text):
        await message.answer(
            "⚠️ Noto'g'ri format! YYYY-MM-DD formatda kiriting.\n"
            "Misol: <code>2025-07-15</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    start_date = normalize_yyyy_mm_dd(text)
    await state.update_data(vacation_start=start_date)
    await state.set_state(AddVacation.end_date)

    await message.answer(
        f"✅ Boshlanish: <b>{start_date}</b>\n\n"
        f"📅 Ta'til <b>tugash</b> sanasini kiriting (YYYY-MM-DD):\n"
        f"Misol: <code>2025-07-28</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(AddVacation.end_date)
async def process_vacation_end(message: Message, state: FSMContext):
    """Ta'til tugash sanasi qabul qilindi, bazaga yoziladi."""
    text = message.text.strip()

    if not validate_yyyy_mm_dd(text):
        await message.answer(
            "⚠️ Noto'g'ri format! YYYY-MM-DD formatda kiriting.\n"
            "Misol: <code>2025-07-28</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    end_date = normalize_yyyy_mm_dd(text)
    data = await state.get_data()
    start_date = data["vacation_start"]

    # Tugash sanasi boshlanishdan keyin bo'lishi kerak
    if end_date <= start_date:
        await message.answer(
            "⚠️ Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak!",
            reply_markup=cancel_keyboard(),
        )
        return

    vac_id = await queries.add_vacation(
        employee_id=data["vacation_emp_id"],
        start_date=start_date,
        end_date=end_date,
    )
    await state.clear()

    await message.answer(
        f"✅ <b>Ta'til muvaffaqiyatli qo'shildi!</b>\n\n"
        f"👤 Xodim: {data['vacation_emp_name']}\n"
        f"📅 Davr: {start_date} → {end_date}\n"
        f"🆔 ID: {vac_id}",
        reply_markup=back_button(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════
# TA'TILLAR RO'YXATI
# ═══════════════════════════════════════════

@router.message(Command("vacations"))
@router.callback_query(F.data.startswith("menu_vacations"))
async def cmd_vacations(event: Message | CallbackQuery):
    """Joriy va kelgusi ta'tillarni ko'rsatadi."""
    today_str = date.today().strftime("%Y-%m-%d")
    vacations = await queries.get_active_and_upcoming_vacations(today_str)

    page = 1
    if isinstance(event, CallbackQuery) and event.data.startswith("menu_vacations_"):
        try:
            page = int(event.data.split("_")[-1])
        except ValueError:
            page = 1

    if not vacations:
        text = "📅 Hozircha ta'tillar yo'q."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")]
        ])
    else:
        ITEMS_PER_PAGE = 10
        total_pages = (len(vacations) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
            
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_vacations = vacations[start_idx:end_idx]

        text = f"📅 <b>Joriy va kelgusi ta'tillar</b> ({len(vacations)} ta):\n"
        if total_pages > 1:
            text += f"📄 Sahifa {page}/{total_pages}\n"
        text += "\n"
        
        for i, vac in enumerate(current_vacations, start_idx + 1):
            text += format_vacation_info(vac, i) + "\n\n"

        keyboard_rows = []
        for vac in current_vacations:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"🗑 {vac['full_name']} ({vac['start_date']})",
                    callback_data=f"del_vac_{vac['id']}",
                )
            ])
            
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"menu_vacations_{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"menu_vacations_{page+1}"))
            
        if nav_buttons:
            keyboard_rows.append(nav_buttons)
            
        keyboard_rows.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_vac_"))
async def confirm_delete_vacation(callback: CallbackQuery):
    """Ta'tilni o'chirish tasdiqlash."""
    vac_id = int(callback.data.split("_")[-1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_del_vac_{vac_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="menu_vacations"),
        ]
    ])

    await callback.message.edit_text(
        f"⚠️ <b>Bu ta'tilni o'chirmoqchimisiz?</b> (ID: {vac_id})",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_vac_"))
async def execute_delete_vacation(callback: CallbackQuery):
    """Ta'tilni o'chiradi."""
    vac_id = int(callback.data.split("_")[-1])
    success = await queries.delete_vacation(vac_id)

    if success:
        await callback.message.edit_text("✅ Ta'til o'chirildi.", reply_markup=back_button())
    else:
        await callback.message.edit_text("❌ Ta'til topilmadi.", reply_markup=back_button())
    await callback.answer()


# ═══════════════════════════════════════════
# BAYRAM QO'SHISH
# ═══════════════════════════════════════════

@router.message(Command("add_holiday"))
@router.callback_query(F.data == "menu_add_holiday")
async def cmd_add_holiday(event: Message | CallbackQuery, state: FSMContext):
    """Bayram qo'shish jarayonini boshlaydi."""
    await state.set_state(AddHoliday.holiday_name)
    text = "🎉 <b>Yangi bayram qo'shish</b>\n\nBayram nomini kiriting:"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=cancel_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=cancel_keyboard(), parse_mode="HTML")


@router.message(AddHoliday.holiday_name)
async def process_holiday_name(message: Message, state: FSMContext):
    """Bayram nomi qabul qilindi."""
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(
            "⚠️ Nom juda qisqa. Iltimos, to'liq nom kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(holiday_name=name)
    await state.set_state(AddHoliday.is_recurring)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔁 Ha, har yili", callback_data="recurring_yes"),
            InlineKeyboardButton(text="📌 Yo'q, faqat shu yil", callback_data="recurring_no"),
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")],
    ])

    await message.answer(
        f"✅ Bayram nomi: <b>{name}</b>\n\n"
        f"Bu bayram har yili takrorlanadimi?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data.in_({"recurring_yes", "recurring_no"}), AddHoliday.is_recurring)
async def process_holiday_recurring(callback: CallbackQuery, state: FSMContext):
    """Takrorlanish tanlandi, sanani so'raydi."""
    is_recurring = callback.data == "recurring_yes"
    await state.update_data(is_recurring=is_recurring)
    await state.set_state(AddHoliday.holiday_date)

    if is_recurring:
        format_hint = "MM-DD"
        example = "01-01"
    else:
        format_hint = "YYYY-MM-DD"
        example = "2025-03-21"

    await callback.message.edit_text(
        f"📅 Bayram sanasini kiriting (<b>{format_hint}</b> formatda):\n"
        f"Misol: <code>{example}</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddHoliday.holiday_date)
async def process_holiday_date(message: Message, state: FSMContext):
    """Bayram sanasi qabul qilindi, bazaga yoziladi."""
    text = message.text.strip()
    data = await state.get_data()
    is_recurring = data["is_recurring"]

    if is_recurring:
        if not validate_mm_dd(text):
            await message.answer(
                "⚠️ Noto'g'ri format! MM-DD formatda kiriting.\n"
                "Misol: <code>01-01</code>",
                reply_markup=cancel_keyboard(),
                parse_mode="HTML",
            )
            return
        holiday_date = normalize_mm_dd(text)
    else:
        if not validate_yyyy_mm_dd(text):
            await message.answer(
                "⚠️ Noto'g'ri format! YYYY-MM-DD formatda kiriting.\n"
                "Misol: <code>2025-03-21</code>",
                reply_markup=cancel_keyboard(),
                parse_mode="HTML",
            )
            return
        holiday_date = normalize_yyyy_mm_dd(text)

    hol_id = await queries.add_holiday(
        holiday_name=data["holiday_name"],
        holiday_date=holiday_date,
        is_recurring=is_recurring,
    )
    await state.clear()

    recurring_text = "🔁 Har yili takrorlanadi" if is_recurring else "📌 Faqat shu yil"
    await message.answer(
        f"✅ <b>Bayram muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🎉 Nom: {data['holiday_name']}\n"
        f"📅 Sana: {holiday_date}\n"
        f"{recurring_text}\n"
        f"🆔 ID: {hol_id}",
        reply_markup=back_button(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════
# BAYRAMLAR RO'YXATI
# ═══════════════════════════════════════════

@router.message(Command("holidays"))
@router.callback_query(F.data.startswith("menu_holidays"))
async def cmd_holidays(event: Message | CallbackQuery):
    """Barcha bayramlar ro'yxatini ko'rsatadi."""
    holidays = await queries.get_all_holidays()

    page = 1
    if isinstance(event, CallbackQuery) and event.data.startswith("menu_holidays_"):
        try:
            page = int(event.data.split("_")[-1])
        except ValueError:
            page = 1

    if not holidays:
        text = "📜 Bayramlar ro'yxati bo'sh.\n\nAvval /add_holiday buyrug'i bilan bayram qo'shing."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")]
        ])
    else:
        ITEMS_PER_PAGE = 10
        total_pages = (len(holidays) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
            
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_holidays = holidays[start_idx:end_idx]

        text = f"📜 <b>Bayramlar ro'yxati</b> ({len(holidays)} ta):\n"
        if total_pages > 1:
            text += f"📄 Sahifa {page}/{total_pages}\n"
        text += "\n"
        
        for i, hol in enumerate(current_holidays, start_idx + 1):
            text += format_holiday_info(hol, i) + "\n\n"

        keyboard_rows = []
        for hol in current_holidays:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"🗑 {hol['holiday_name']}",
                    callback_data=f"del_hol_{hol['id']}",
                )
            ])
            
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"menu_holidays_{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"menu_holidays_{page+1}"))
            
        if nav_buttons:
            keyboard_rows.append(nav_buttons)
            
        keyboard_rows.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_hol_"))
async def confirm_delete_holiday(callback: CallbackQuery):
    """Bayramni o'chirish tasdiqlash."""
    hol_id = int(callback.data.split("_")[-1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_del_hol_{hol_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="menu_holidays"),
        ]
    ])

    await callback.message.edit_text(
        f"⚠️ <b>Bu bayramni o'chirmoqchimisiz?</b> (ID: {hol_id})",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_hol_"))
async def execute_delete_holiday(callback: CallbackQuery):
    """Bayramni o'chiradi."""
    hol_id = int(callback.data.split("_")[-1])
    success = await queries.delete_holiday(hol_id)

    if success:
        await callback.message.edit_text("✅ Bayram o'chirildi.", reply_markup=back_button())
    else:
        await callback.message.edit_text("❌ Bayram topilmadi.", reply_markup=back_button())
    await callback.answer()


# ═══════════════════════════════════════════
# GURUH SOZLASH
# ═══════════════════════════════════════════

def _extract_username_from_link(text: str) -> str | None:
    """
    Guruh linkidan username ni ajratib oladi.
    Qo'llab-quvvatlanadigan formatlar:
    - https://t.me/guruh_nomi
    - http://t.me/guruh_nomi
    - t.me/guruh_nomi
    - @guruh_nomi
    """
    text = text.strip()

    # https://t.me/username yoki t.me/username
    match = re.match(r"(?:https?://)?t\.me/([a-zA-Z][a-zA-Z0-9_]{3,})$", text)
    if match:
        return match.group(1)

    # @username
    match = re.match(r"@([a-zA-Z][a-zA-Z0-9_]{3,})$", text)
    if match:
        return match.group(1)

    return None


@router.message(Command("set_group"))
@router.callback_query(F.data == "menu_set_group")
async def cmd_set_group(event: Message | CallbackQuery, state: FSMContext):
    """Guruh ID ni sozlash."""
    current_group = await queries.get_setting("group_id")
    current_name = await queries.get_setting("group_name")

    if current_group:
        name_str = f" ({current_name})" if current_name else ""
        current_text = f"Hozirgi guruh: <code>{current_group}</code>{name_str}"
    else:
        current_text = "Hozir guruh sozlanmagan."

    await state.set_state(SetGroup.group_id)
    text = (
        f"⚙️ <b>Guruh sozlash</b>\n\n"
        f"{current_text}\n\n"
        f"Guruh linkini yoki @username ni kiriting:\n\n"
        f"📎 Link: <code>https://t.me/guruh_nomi</code>\n"
        f"📎 Username: <code>@guruh_nomi</code>"
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=cancel_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=cancel_keyboard(), parse_mode="HTML")


@router.message(SetGroup.group_id)
async def process_set_group(message: Message, state: FSMContext, bot: Bot):
    """Guruh linki yoki @username qabul qilindi va saqlanadi."""
    text = message.text.strip()

    username = _extract_username_from_link(text)
    if not username:
        await message.answer(
            "⚠️ Noto'g'ri format!\n\n"
            "Quyidagilardan birini kiriting:\n"
            "📎 <code>https://t.me/guruh_nomi</code>\n"
            "📎 <code>@guruh_nomi</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    try:
        chat = await bot.get_chat(f"@{username}")
    except Exception:
        await message.answer(
            f"⚠️ <b>@{username}</b> guruhini topib bo'lmadi!\n\n"
            f"Sabablari:\n"
            f"• Guruh ochiq (public) bo'lishi kerak\n"
            f"• Bot guruhga a'zo bo'lishi kerak\n"
            f"• Username to'g'ri yozilganligini tekshiring",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    # Bazaga saqlash
    await queries.set_setting("group_id", str(chat.id))
    if chat.title:
        await queries.set_setting("group_name", chat.title)
    await state.clear()

    await message.answer(
        f"✅ <b>Guruh muvaffaqiyatli sozlandi!</b>\n\n"
        f"📌 Guruh: <b>{chat.title}</b>\n"
        f"🆔 ID: <code>{chat.id}</code>\n\n"
        f"Endi bot har kuni ertalab shu guruhga eslatmalarni yuboradi.",
        reply_markup=back_button(),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════
# ADMIN BOSHQARUVI
# ═══════════════════════════════════════════

from config import ADMIN_IDS

@router.message(Command("admins"))
@router.callback_query(F.data == "menu_admins")
async def cmd_admins(event: Message | CallbackQuery):
    """Barcha adminlarni ko'rsatish."""
    db_admins = await queries.get_all_admins()
    
    text = "🛡 <b>Bot Adminlari:</b>\n\n"
    text += "<b>Asosiy adminlar (.env):</b>\n"
    for a_id in ADMIN_IDS:
        text += f"• <code>{a_id}</code>\n"
    
    text += "\n<b>Boshqa adminlar (Bazada):</b>\n"
    if not db_admins:
        text += "— Yo'q\n"
    else:
        for a in db_admins:
            text += f"• {a['full_name']} (<code>{a['user_id']}</code>)\n"
    
    # Tugmalar
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_admin")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="menu_back")]
    ])
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "add_admin")
async def start_add_admin(callback: CallbackQuery, state: FSMContext):
    """Yangi admin qo'shish."""
    await state.set_state(AddAdmin.user_id)
    await callback.message.edit_text(
        "➕ <b>Yangi admin qo'shish</b>\n\n"
        "Yangi adminning Telegram ID raqamini kiriting:\n"
        "(Foydalanuvchi botga start bosgan bo'lishi kerak)",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()

@router.message(AddAdmin.user_id)
async def process_admin_user_id(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ ID faqat raqamlardan iborat bo'lishi kerak:", reply_markup=cancel_keyboard())
        return
    
    await state.update_data(new_admin_id=int(text))
    await state.set_state(AddAdmin.full_name)
    await message.answer(
        f"✅ ID: <code>{text}</code>\n\n"
        "Admin ismini kiriting (qulaylik uchun):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )

@router.message(AddAdmin.full_name)
async def process_admin_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    data = await state.get_data()
    user_id = data["new_admin_id"]
    
    await queries.add_admin(
        user_id=user_id,
        full_name=full_name,
        username=None,
        added_by=message.from_user.id
    )
    await state.clear()
    
    await message.answer(
        f"✅ <b>Yangi admin qo'shildi!</b>\n\n"
        f"👤 {full_name}\n"
        f"🆔 <code>{user_id}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Adminlar ro'yxati", callback_data="menu_admins")]
        ]),
        parse_mode="HTML",
    )

