import html
from typing import Optional

import MeguBot.modules.sql.blsticker_sql as sql
from MeguBot import LOGGER, dispatcher
from MeguBot.modules.connection import connected
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.alternate import send_message
from MeguBot.modules.helper_funcs.chat_status import (user_admin,
                                                           user_not_admin)
from MeguBot.modules.helper_funcs.misc import split_message
from MeguBot.modules.helper_funcs.string_handling import extract_time

from MeguBot.modules.log_channel import loggable
from MeguBot.modules.warns import warn
from telegram import (Chat, Message, ParseMode, Update, User, ChatPermissions)
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler)
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html, mention_markdown


@run_async
def blackliststicker(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    bot, args = context.bot, context.args
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id
            chat_name = chat.title

    sticker_list = "<b>Lista de stickers en la lista negra actualmente en {}:</b>\n".format(
        chat_name)

    all_stickerlist = sql.get_chat_stickers(chat_id)

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_stickerlist:
            sticker_list += "<code>{}</code>\n".format(html.escape(trigger))
    elif len(args) == 0:
        for trigger in all_stickerlist:
            sticker_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(sticker_list)
    for text in split_text:
        if sticker_list == "<b>Lista de stickers en la lista negra actualmente en {}:</b>\n".format(
                chat_name).format(chat_name):
            send_message(
                update.effective_message,
                "No hay stickers de lista negra en <b>{}</b>!".format(
                    chat_name),
                parse_mode=ParseMode.HTML)
            return
    send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_blackliststicker(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)
    bot = context.bot
    conn = connected(bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1].replace('https://t.me/addstickers/', '')
        to_blacklist = list(
            set(trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()))
        added = 0
        for trigger in to_blacklist:
            try:
                get = bot.getStickerSet(trigger)
                sql.add_to_stickers(chat_id, trigger.lower())
                added += 1
            except BadRequest:
                send_message(
                    update.effective_message,
                    "No se pudo encontrar el sticker `{}`!".format(trigger),
                    parse_mode="markdown")

        if added == 0:
            return

        if len(to_blacklist) == 1:
            send_message(
                update.effective_message,
                "Sticker <code>{}</code> agregado a la lista negra de stickers en <b>{}</b>!"
                .format(html.escape(to_blacklist[0]), chat_name),
                parse_mode=ParseMode.HTML)
        else:
            send_message(
                update.effective_message,
                "<code>{}</code> stickers añadidos a los stickers de la lista negra en <b>{}</b>!"
                .format(added, chat_name),
                parse_mode=ParseMode.HTML)
    elif msg.reply_to_message:
        added = 0
        trigger = msg.reply_to_message.sticker.set_name
        if trigger is None:
            send_message(update.effective_message, "El sticker no es válido!")
            return
        try:
            get = bot.getStickerSet(trigger)
            sql.add_to_stickers(chat_id, trigger.lower())
            added += 1
        except BadRequest:
            send_message(
                update.effective_message,
                "No se pudo encontrar el sticker `{}`!".format(trigger),
                parse_mode="markdown")

        if added == 0:
            return

        send_message(
            update.effective_message,
            "Sticker <code>{}</code> agregado a la lista negra de stickers en <b>{}</b>!"
            .format(trigger, chat_name),
            parse_mode=ParseMode.HTML)
    else:
        send_message(update.effective_message,
                     "Dame los stickers que quieres agregar a la lista negra.")


@run_async
@user_admin
def unblackliststicker(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)
    bot = context.bot
    conn = connected(bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1].replace('https://t.me/addstickers/', '')
        to_unblacklist = list(
            set(trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()))
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_stickers(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    update.effective_message,
                    "Sticker <code>{}</code> eliminado de la lista negra en <b>{}</b>!"
                    .format(html.escape(to_unblacklist[0]), chat_name),
                    parse_mode=ParseMode.HTML)
            else:
                send_message(update.effective_message,
                             "Este sticker no está en la lista negra...!")

        elif successful == len(to_unblacklist):
            send_message(
                update.effective_message,
                "Sticker <code>{}</code> eliminado de la lista negra en <b>{}</b>!"
                .format(successful, chat_name),
                parse_mode=ParseMode.HTML)

        elif not successful:
            send_message(
                update.effective_message,
                "Ninguna de estos stickers existe, por lo que no se pueden quitar.."
                .format(successful,
                        len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML)

        else:
            send_message(
                update.effective_message,
                "Sticker <code>{}</code> eliminado de la lista negra. {} no existía, por lo que no se borro."
                .format(successful,
                        len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML)
    elif msg.reply_to_message:
        trigger = msg.reply_to_message.sticker.set_name
        if trigger is None:
            send_message(update.effective_message, "El sticker no es válido!")
            return
        success = sql.rm_from_stickers(chat_id, trigger.lower())

        if success:
            send_message(
                update.effective_message,
                "Sticker <code>{}</code> eliminado de la lista negra en <b>{}</b>!"
                .format(trigger, chat_name),
                parse_mode=ParseMode.HTML)
        else:
            send_message(
                update.effective_message,
                "{} no se encuentra en los stickers de la lista negra...!".format(trigger))
    else:
        send_message(update.effective_message,
                     "Dame los stickers que quieres agregar a la lista negra.")


@run_async
@loggable
@user_admin
def blacklist_mode(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    bot, args = context.bot, context.args
    conn = connected(bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         "Solo puede usar este comando en grupos, no PM")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == 'off' or args[0].lower(
        ) == 'nothing' or args[0].lower() == 'no':
            settypeblacklist = 'turn off'
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() == 'del' or args[0].lower() == 'delete':
            settypeblacklist = 'left, the message will be deleted'
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == 'warn':
            settypeblacklist = 'warned'
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == 'mute':
            settypeblacklist = 'muted'
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == 'kick':
            settypeblacklist = 'kicked'
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == 'ban':
            settypeblacklist = 'banned'
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == 'tban':
            if len(args) == 1:
                teks = """Parece que está intentando establecer un valor temporal en la lista negra, pero no ha determinado la hora; use `/blstickermode tban <valor de tiempo>`.
                                          Ejemplos de valores de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown")
                return
            settypeblacklist = 'Prohibido temporalmente para {}'.format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == 'tmute':
            if len(args) == 1:
                teks = """Parece que está intentando establecer un valor temporal en la lista negra, pero no ha determinado la hora; use `/blstickermode tmute <valor de tiempo>`.
                                          Ejemplos de valores de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown")
                return
            settypeblacklist = 'temporarily muted for {}'.format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "Solo entiendo off/del/warn/ban/kick/mute/tban/tmute!")
            return
        if conn:
            text = "El modo de stickers de lista negra ha cambiado, los usuarios serán `{}` a *{}*!".format(
                settypeblacklist, chat_name)
        else:
            text = "El modo de etiqueta de lista negra ha cambiado, los usuarios serán `{}`!".format(
                settypeblacklist)
        send_message(update.effective_message, text, parse_mode="markdown")
        return "<b>{}:</b>\n" \
          "<b>Administrador:</b> {}\n" \
          "Changed sticker blacklist mode. users will be {}.".format(html.escape(chat.title),
                         mention_html(user.id, user.first_name), settypeblacklist)
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        if getmode == 0:
            settypeblacklist = "not active"
        elif getmode == 1:
            settypeblacklist = "hapus"
        elif getmode == 2:
            settypeblacklist = "warn"
        elif getmode == 3:
            settypeblacklist = "mute"
        elif getmode == 4:
            settypeblacklist = "kick"
        elif getmode == 5:
            settypeblacklist = "ban"
        elif getmode == 6:
            settypeblacklist = "Temporalmente prohibido para {}".format(getvalue)
        elif getmode == 7:
            settypeblacklist = "Temporalmente silenciado por {}".format(getvalue)
        if conn:
            text = "El modo de stickers de lista negra está configurado actualmente en *{}* en *{}*.".format(
                settypeblacklist, chat_name)
        else:
            text = "El modo de stickers de lista negra está configurado actualmente en *{}*.".format(
                settypeblacklist)
        send_message(
            update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


@run_async
@user_not_admin
def del_blackliststicker(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user
    to_match = message.sticker
    if not to_match:
        return
    bot = context.bot
    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_stickers(chat.id)
    for trigger in chat_filters:
        if to_match.set_name.lower() == trigger.lower():
            try:
                if getmode == 0:
                    return
                elif getmode == 1:
                    message.delete()
                elif getmode == 2:
                    message.delete()
                    warn(
                        update.effective_user,
                        chat,
                        "Usando el sticker '{}' que está en la lista negra de stickers".format(
                            trigger),
                        message,
                        update.effective_user,
                        conn=False)
                    return
                elif getmode == 3:
                    message.delete()
                    bot.restrict_chat_member(
                        chat.id,
                        update.effective_user.id,
                        permissions=ChatPermissions(can_send_messages=False))
                    bot.sendMessage(
                        chat.id,
                        "{} silenciado porque usa '{}' que esta en las stickers de la lista negra"
                        .format(
                            mention_markdown(user.id, user.first_name),
                            trigger),
                        parse_mode="markdown")
                    return
                elif getmode == 4:
                    message.delete()
                    res = chat.unban_member(update.effective_user.id)
                    if res:
                        bot.sendMessage(
                            chat.id,
                            "{} kickeado porque usa '{}' que está en la lista negra de stickers"
                            .format(
                                mention_markdown(user.id, user.first_name),
                                trigger),
                            parse_mode="markdown")
                    return
                elif getmode == 5:
                    message.delete()
                    chat.kick_member(user.id)
                    bot.sendMessage(
                        chat.id,
                        "{} baneado porque usa '{}' que está en la lista negra de stickers"
                        .format(
                            mention_markdown(user.id, user.first_name),
                            trigger),
                        parse_mode="markdown")
                    return
                elif getmode == 6:
                    message.delete()
                    bantime = extract_time(message, value)
                    chat.kick_member(user.id, until_date=bantime)
                    bot.sendMessage(
                        chat.id,
                        "{} baneado por {} porque usa '{}' que está en la lista negra de stickers"
                        .format(
                            mention_markdown(user.id, user.first_name), value,
                            trigger),
                        parse_mode="markdown")
                    return
                elif getmode == 7:
                    message.delete()
                    mutetime = extract_time(message, value)
                    bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        permissions=ChatPermissions(
                            can_send_messages=False, until_date=mutetime))
                    bot.sendMessage(
                        chat.id,
                        "{} muteado por {} porque usa '{}' que está en la lista negra de stickers"
                        .format(
                            mention_markdown(user.id, user.first_name), value,
                            trigger),
                        parse_mode="markdown")
                    return
            except BadRequest as excp:
                if excp.message == "Mensaje para eliminar no encontrado":
                    pass
                else:
                    LOGGER.exception("Error al eliminar el mensaje de la lista negra.")
                break


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get('sticker_blacklist', {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_stickers_chat_filters(chat_id)
    return "Hay "{}" stickers en la lista negra.".format(blacklisted)


def __stats__():
    return "{} blacklist stickers, across {} chats.".format(
        sql.num_stickers_filters(), sql.num_stickers_filter_chats())


__help__ = """
Los stickers de lista negra se utiliza para bloquear ciertos stickers. Siempre que se envíe un , el mensaje se eliminará inmediatamente.
*NOTA:* Las pegatinas de la lista negra no afectan al administrador del grupo.
 • `/blsticker`*:* Ver el sticker actual en la lista negra.
* Solo administrador:*
 • `/addblsticker <enlace de etiqueta>`*:* Agrega el disparador de etiqueta a la lista negra. Se puede agregar a través de la etiqueta de respuesta.
 • `/unblsticker <enlace adhesivo>`*:* Elimina los disparadores de la lista negra. Aquí se aplica la misma lógica de nueva línea, por lo que puede eliminar varios activadores a la vez.
 • `/rmblsticker <enlace de etiqueta>`*:* Igual que arriba.
 • `/blstickermode <ban / tban / mute / tmute>`*:* Configura una acción predeterminada sobre qué hacer si los usuarios usan pegatinas en la lista negra. (`tmute parece roto en este momento`)
Nota:
 • `<enlace de etiqueta>` puede ser `https://t.me/addstickers/ <sticker>` o simplemente `<sticker>` o responder al mensaje con el sticker.
"""

__mod_name__ = "Sticker Blacklist"

BLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler(
    "blsticker", blackliststicker, admin_ok=True)
ADDBLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler(
    "addblsticker", add_blackliststicker)
UNBLACKLIST_STICKER_HANDLER = CommandHandler(["unblsticker", "rmblsticker"],
                                             unblackliststicker)
BLACKLISTMODE_HANDLER = CommandHandler("blstickermode", blacklist_mode)
BLACKLIST_STICKER_DEL_HANDLER = MessageHandler(Filters.sticker & Filters.group,
                                               del_blackliststicker)

dispatcher.add_handler(BLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(ADDBLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(UNBLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_STICKER_DEL_HANDLER)
