from typing import Callable, Dict, Any, Awaitable
import json
import os
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from bot.database.models import User

class I18nMiddleware(BaseMiddleware):
    def __init__(self, locales_dir: str):
        self.locales: Dict[str, Dict[str, str]] = {}
        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                lang = filename.split(".")[0]
                with open(os.path.join(locales_dir, filename), "r", encoding="utf-8") as f:
                    self.locales[lang] = json.load(f)

        # Ensure fallback
        self.default_lang = "uz"

    def get_text(self, lang: str, key: str, **kwargs) -> str:
        text = self.locales.get(lang, {}).get(key)
        if not text:
            # Fallback to uz
            text = self.locales.get(self.default_lang, {}).get(key, key)

        return text.format(**kwargs) if text else key

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        db_user: User | None = data.get("db_user")

        lang = db_user.language if db_user else self.default_lang

        # Pass a localized translation function down
        def _(key: str, **kwargs) -> str:
            return self.get_text(lang, key, **kwargs)

        data["_"] = _
        return await handler(event, data)