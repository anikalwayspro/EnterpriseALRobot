import time
from telegram import Update
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, CallbackContext
from telegram.ext.filters import BaseFilter, Filters
from tg_bot import dispatcher as d, log
from typing import Optional, List
from functools import lru_cache

message_history = {}

def rate_limit(messages_per_window: int, window_seconds: int):
    """
    Decorator that limits the rate at which a function can be called.

    Args:
        messages_per_window (int): The maximum number of messages allowed within the time window.
        window_seconds (int): The duration of the time window in seconds.

    Returns:
        function: The decorated function.

    Example:
        @rate_limit(40, 60)
        def my_function(update: Update, context: CallbackContext):
            # Function implementation
    """
    def decorator(func):

        @lru_cache(maxsize=1024)
        def wrapper(update: Update, context: CallbackContext):
            user_id = update.effective_user.id
            current_time = time.time()

            if user_id not in message_history:
                message_history[user_id] = []

            # Remove messages outside the current time window
            message_history[user_id] = [t for t in message_history[user_id] if current_time - t <= window_seconds]

            if len(message_history[user_id]) >= messages_per_window:
                log.debug(f"Rate limit exceeded for user {user_id}. Allowed {messages_per_window} updates in {window_seconds} seconds for {func.__name__}")
                return

            message_history[user_id].append(current_time)
            func(update, context)

        return wrapper

    return decorator

class KigyoTelegramHandler:
    def __init__(self, d):
        self._dispatcher = d

    def command(
            self, command: str, filters: Optional[BaseFilter] = None, admin_ok: bool = False, pass_args: bool = False,
            pass_chat_data: bool = False, run_async: bool = True, can_disable: bool = True,
            group: Optional[int] = 40
    ):
        if filters:
           filters = filters & ~Filters.update.edited_message
        else:
            filters = ~Filters.update.edited_message
        def _command(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok), group
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async, pass_args=pass_args), group
                    )
                log.debug(f"[KIGCMD] Loaded handler {command} for function {func.__name__} in group {group}")
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok, pass_chat_data=pass_chat_data)
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async, pass_args=pass_args,
                                       pass_chat_data=pass_chat_data)
                    )
                log.debug(f"[KIGCMD] Loaded handler {command} for function {func.__name__}")

            return func

        return _command

    def message(self, pattern: Optional[BaseFilter] = None, can_disable: bool = True, run_async: bool = True,
                group: Optional[int] = 60, friendly=None):
        if pattern:
           pattern = pattern & ~Filters.update.edited_message
        else:
           pattern = ~Filters.update.edited_message
        def _message(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async), group
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async), group
                    )
                log.debug(f"[KIGMSG] Loaded filter pattern {pattern} for function {func.__name__} in group {group}")
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async)
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async)
                    )
                log.debug(f"[KIGMSG] Loaded filter pattern {pattern} for function {func.__name__}")

            return func

        return _message

    def callbackquery(self, pattern: str = None, run_async: bool = True):
        def _callbackquery(func):
            self._dispatcher.add_handler(CallbackQueryHandler(pattern=pattern, callback=func, run_async=run_async))
            log.debug(f'[KIGCALLBACK] Loaded callbackquery handler with pattern {pattern} for function {func.__name__}')
            return func

        return _callbackquery

    def inlinequery(self, pattern: Optional[str] = None, run_async: bool = True, pass_user_data: bool = True,
                    pass_chat_data: bool = True, chat_types: List[str] = None):
        def _inlinequery(func):
            self._dispatcher.add_handler(
                InlineQueryHandler(pattern=pattern, callback=func, run_async=run_async, pass_user_data=pass_user_data,
                                   pass_chat_data=pass_chat_data, chat_types=chat_types))
            log.debug(
                f'[KIGINLINE] Loaded inlinequery handler with pattern {pattern} for function {func.__name__} | PASSES '
                f'USER DATA: {pass_user_data} | PASSES CHAT DATA: {pass_chat_data} | CHAT TYPES: {chat_types}')
            return func

        return _inlinequery


kigcmd = KigyoTelegramHandler(d).command
kigmsg = KigyoTelegramHandler(d).message
kigcallback = KigyoTelegramHandler(d).callbackquery
kiginline = KigyoTelegramHandler(d).inlinequery
