from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def templates_keyboard(templates: list, _):
    keyboard = []
    for t in templates:
        keyboard.append([InlineKeyboardButton(text=t.name, callback_data=f"tpl_{t.id}")])
    keyboard.append([InlineKeyboardButton(text=_("btn_cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cancel_keyboard(_):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("btn_cancel"), callback_data="cancel")]
    ])