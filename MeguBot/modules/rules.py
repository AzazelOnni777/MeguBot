from typing import Optional

import MeguBot.modules.sql.rules_sql as sql
from MeguBot import dispatcher
from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.helper_funcs.string_handling import markdown_parser
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      ParseMode, Update, User)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import escape_markdown


@run_async
def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "El atajo de reglas para este chat no se ha configurado correctamente! Pida a los administradores que "
                "arreglen esto.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = f"Las reglas para *{escape_markdown(chat.title)}* son:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif from_pm:
        bot.send_message(
            user.id,
            "Los administradores del grupo aún no han establecido ninguna regla para este chat.. "
            "Aunque esto probablemente no significa que se permitan cosas ilegales...")
    elif rules:
        update.effective_message.reply_text(
            "Contáctame en privado para conocer las reglas de este grupo.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="Reglas", url=f"t.me/{bot.username}?start={chat_id}")
            ]]))
    else:
        update.effective_message.reply_text(
            "Los administradores del grupo aún no han establecido ninguna regla para este chat.. "
            "Aunque esto probablemente no significa que se permitan cosas ilegales...!")


@run_async
@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None,
                          1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(
            raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text(
            "Se establecieron las reglas para este grupo éxitosamente.")


@run_async
@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Reglas borradas éxitosamente!")


def __stats__():
    return f"{sql.num_chats()} chats tienen reglas establecidas."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Este chat tiene sus reglas establecidas: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
 •`/rules`*:* Obtiene las reglas para este chat.

*Solo administradores:*
  •`/setrules <sus reglas aquí>`*:* Establece las reglas para este chat.
  •`/clearrules`*:* Borra las reglas para este chat.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler(
    "clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
