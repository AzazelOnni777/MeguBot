import html
# AI module using Intellivoid's Coffeehouse API by @TheRealPhoenix
from time import sleep, time

import MeguBot.modules.sql.chatbot_sql as sql
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError
from coffeehouse.lydia import LydiaAI
from MeguBot import AI_API_KEY, OWNER_ID, SUPPORT_CHAT, dispatcher
from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.helper_funcs.filters import CustomFilters
from MeguBot.modules.log_channel import gloggable
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

CoffeeHouseAPI = API(AI_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


@run_async
@user_admin
@gloggable
def add_chat(update: Update, context: CallbackContext):
    global api_client
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        sql.set_ses(chat.id, ses_id, expires)
        chat.send_message("IA habilitada con éxito para este chat!")
        message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#IA_Activada\n"
                   f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n")
        return message
    else:
        msg.reply_text("La IA ya está habilitada para este chat!")
        return ""


@run_async
@user_admin
@gloggable
def remove_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        chat.send_message("La IA no está habilitada aquí en primer lugar!")
        return ""
    else:
        sql.rem_chat(chat.id)
        chat.send_message("IA deshabilitada exitosamente!")
        message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#IA_Desactivada\n"
                   f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n")
        return message


def check_message(context: CallbackContext, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "megu":
        return True
    if reply_msg:
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


@run_async
def chatbot(update: Update, context: CallbackContext):
    global api_client
    msg = update.effective_message
    chat = update.effective_chat
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    bot = context.bot
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(context, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            chat.send_message(rep, timeout=60)
        except CFError as e:
            bot.send_message(OWNER_ID,
                             f"Error de chatbot: {e} ocurrió en {chat_id}!")


@run_async
def list_chatbot_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_chats()
    text = "<b>Chats habilitados para IA</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_chat(*chat)
        except Unauthorized:
            sql.rem_chat(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")


__mod_name__ = "Chatbot"

__help__ = f"""
Chatbot utiliza la API CoffeeHouse y permite que Megu hable y proporciona una experiencia de chat grupal más interactiva.

*Comandos:*
*Solo administradores:*
 • `/addchat`*:* Habilita el modo Chatbot en el chat.
 • `/rmchat`*:* Desactiva el modo Chatbot en el chat.
 
* Demonios Carmesí o superior únicamente: *
 • `/listaichats`*:* Lista los chats en los que está habilitado el modo chat.

Informa errores en {SUPPORT_CHAT}
*Desarrollado por CoffeeHouse*(https://coffeehouse.intellivoid.net/) de @Intellivoid
"""

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot)
LIST_CB_CHATS_HANDLER = CommandHandler(
    "listaichats", list_chatbot_chats, filters=CustomFilters.dev_filter)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(LIST_CB_CHATS_HANDLER)
