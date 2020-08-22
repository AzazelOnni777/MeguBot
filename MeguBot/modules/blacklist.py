import html
import re

import MeguBot.modules.sql.blacklist_sql as sql
from MeguBot import LOGGER, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import (connection_status,
                                                           user_admin,
                                                           user_not_admin)
from MeguBot.modules.helper_funcs.extraction import extract_text
from MeguBot.modules.helper_funcs.misc import split_message
from MeguBot.modules.helper_funcs.regex_helper import (infinite_loop_check,
                                                            regex_searcher)
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)

BLACKLIST_GROUP = 11


@run_async
@connection_status
@user_admin
def blacklist(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args
    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        base_blacklist_string = "<b>Palabras incluidas en la lista negra actuales</b>:\n"
    else:
        base_blacklist_string = f"<b>Palabras incluidas en la lista negra actuales en {update_chat_title}</b>:\n"

    all_blacklisted = sql.get_chat_blacklist(chat.id)

    filter_list = base_blacklist_string

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += f"<code>{html.escape(trigger)}</code>\n"
    else:
        for trigger in all_blacklisted:
            filter_list += f" - <code>{html.escape(trigger)}</code>\n"

    split_text = split_message(filter_list)
    for text in split_text:
        if text == base_blacklist_string:
            if update_chat_title == message_chat_title:
                msg.reply_text("No hay mensajes en la lista negra aquí!")
            else:
                msg.reply_text(
                    f"No hay mensajes en la lista negra en <b>{update_chat_title}</b>!",
                    parse_mode=ParseMode.HTML)
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
@connection_status
@user_admin
def add_blacklist(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(
            set(trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()))

        for trigger in to_blacklist:
            try:
                re.compile(trigger)
            except Exception as exce:
                msg.reply_text(f"No se pudo agregar la expresión regular, error: {exce}")
                return
            check = infinite_loop_check(trigger)
            if not check:
                sql.add_to_blacklist(chat.id, trigger.lower())
            else:
                msg.reply_text("Me temo que no puedo agregar esa expresión regular.")
                return

        if len(to_blacklist) == 1:
            msg.reply_text(
                f"Se agregó <code>{html.escape(to_blacklist[0])}</code> a la lista negra!",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"Se agregó <code>{len(to_blacklist)}</code> triggers a la lista negra.",
                parse_mode=ParseMode.HTML)

    else:
        msg.reply_text(
            "Dime qué palabras te gustaría eliminar de la lista negra..")


@run_async
@connection_status
@user_admin
def unblacklist(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            set(trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()))
        successful = 0

        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat.id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text(
                    f"<code>{html.escape(to_unblacklist[0])}</code> removido de la lista negra!",
                    parse_mode=ParseMode.HTML)
            else:
                msg.reply_text("Este trigger no esta en la lista negra...!")

        elif successful == len(to_unblacklist):
            msg.reply_text(
                f"Se eliminaron los triggers <code>{successful}</code> de la lista negra..",
                parse_mode=ParseMode.HTML)

        elif not successful:
            msg.reply_text(
                "Ninguno de estos triggers existe, por lo que no se eliminaron.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"Se eliminaron <code>{successful}</code> triggers de la lista negra."
                f" {len(to_unblacklist) - successful} no existía, por lo que no se elimino.",
                parse_mode=ParseMode.HTML)
    else:
        msg.reply_text(
            "Dime qué palabras te gustaría eliminar de la lista negra.")


@run_async
@connection_status
@user_not_admin
def del_blacklist(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    to_match = extract_text(message)
    msg = update.effective_message
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + trigger + r"( |$|[^\w])"
        match = regex_searcher(pattern, to_match)
        if not match:
            #Skip to next item in blacklist
            continue
        if match:
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Mensaje para eliminar no encontrado":
                    pass
                else:
                    LOGGER.exception("Error al eliminar el mensaje de la lista negra.")
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "Hay {} palabras en la lista negra.".format(blacklisted)


def __stats__():
    return "{} blacklist triggers, across {} chats.".format(
        sql.num_blacklist_filters(), sql.num_blacklist_filter_chats())


__help__ = """
La lista negra se utiliza para evitar que ciertos factores desencadenantes se digan en un grupo. Cada vez que se menciona el disparador, \
el mensaje se eliminará inmediatamente. A veces, una buena combinación es combinar esto con filtros de advertencia.

* NOTA:* las listas negras no afectan a los administradores de grupo.

 • `/blacklist`*:* Ver las palabras actuales de la lista negra.

*Solo administradores:*
 • `/addblacklist <triggers>`*:* Agrega un trigger a la lista negra. Cada línea se considera un trigger, por lo que el uso de \
las líneas le permitirán agregar múltiples activadores.
 • `/unblacklist <triggers>`*:* Elimina los triggers de la lista negra. Aquí se aplica la misma lógica de nueva línea, por lo que puede eliminar \
múltiples disparadores a la vez.
 • `/rmblacklist <triggers>`*:* Igual que arriba.
"""

BLACKLIST_HANDLER = DisableAbleCommandHandler("blacklist", blacklist)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist)
UNBLACKLIST_HANDLER = CommandHandler(["unblacklist", "rmblacklist"],
                                     unblacklist)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo)
    & Filters.group,
    del_blacklist,
    allow_edit=True)
dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)

__mod_name__ = "Palabras Prohibidas"
__handlers__ = [
    BLACKLIST_HANDLER, ADD_BLACKLIST_HANDLER, UNBLACKLIST_HANDLER,
    (BLACKLIST_DEL_HANDLER, BLACKLIST_GROUP)
]
