import html

import telegram
from MeguBot import LOGGER, SUPPORT_CHAT, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import (connection_status,
                                                           user_admin)
from MeguBot.modules.helper_funcs.extraction import extract_text
from MeguBot.modules.helper_funcs.filters import CustomFilters
from MeguBot.modules.helper_funcs.misc import build_keyboard
from MeguBot.modules.helper_funcs.regex_helper import (infinite_loop_check,
                                                            regex_searcher)
from MeguBot.modules.helper_funcs.string_handling import (
    button_markdown_parser, split_quotes)
from MeguBot.modules.sql import cust_filters_sql as sql
from telegram import InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CommandHandler,
                          DispatcherHandlerStop, MessageHandler, run_async)

HANDLER_GROUP = 10


@run_async
@connection_status
def list_handlers(update: Update, context: CallbackContext):
    chat = update.effective_chat
    all_handlers = sql.get_chat_triggers(chat.id)

    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        BASIC_FILTER_STRING = "<b>triggers en este chat:</b>\n"
    else:
        BASIC_FILTER_STRING = f"<b>triggers en {update_chat_title}</b>:\n"

    if not all_handlers:
        if update_chat_title == message_chat_title:
            update.effective_message.reply_text("Aquí no hay triggers activos!")
        else:
            update.effective_message.reply_text(
                f"No hay triggers activos en <b>{update_chat_title}</b>!",
                parse_mode=telegram.ParseMode.HTML)
        return

    filter_list = ""
    for keyword in all_handlers:
        entry = f" • <code>{html.escape(keyword)}</code>\n"
        if len(entry) + len(filter_list) + len(
                BASIC_FILTER_STRING) > telegram.MAX_MESSAGE_LENGTH:
            filter_list = BASIC_FILTER_STRING + html.escape(filter_list)
            update.effective_message.reply_text(
                filter_list, parse_mode=telegram.ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != BASIC_FILTER_STRING:
        filter_list = BASIC_FILTER_STRING + filter_list
        update.effective_message.reply_text(
            filter_list, parse_mode=telegram.ParseMode.HTML)


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@connection_status
@user_admin
def filters(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    args = msg.text.split(None, 1)

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])
    if len(extracted) < 1:
        return
    # set trigger -> lower, so as to avoid adding duplicate filters with different cases
    keyword = extracted[0]
    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    buttons = []

    # determine what the contents of the filter are - text, image, sticker, etc
    if len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text)  # set correct offset relative to command + notename
        content, buttons = button_markdown_parser(
            extracted[1], entities=msg.parse_entities(), offset=offset)
        content = content.strip()
        if not content:
            msg.reply_text(
                "No hay mensaje de nota: no puede sólo tener botones, necesita un mensaje para acompañarlo!"
            )
            return

    elif msg.reply_to_message and msg.reply_to_message.sticker:
        content = msg.reply_to_message.sticker.file_id
        is_sticker = True

    elif msg.reply_to_message and msg.reply_to_message.document:
        content = msg.reply_to_message.document.file_id
        is_document = True

    elif msg.reply_to_message and msg.reply_to_message.photo:
        content = msg.reply_to_message.photo[
            -1].file_id  # last elem = best quality
        is_image = True

    elif msg.reply_to_message and msg.reply_to_message.audio:
        content = msg.reply_to_message.audio.file_id
        is_audio = True

    elif msg.reply_to_message and msg.reply_to_message.voice:
        content = msg.reply_to_message.voice.file_id
        is_voice = True

    elif msg.reply_to_message and msg.reply_to_message.video:
        content = msg.reply_to_message.video.file_id
        is_video = True

    else:
        msg.reply_text("No especificaste con qué responder!")
        return
    if infinite_loop_check(keyword):
        msg.reply_text("Me temo que no puedo agregar esa expresión regular")
        return
    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(chat.id, keyword, content, is_sticker, is_document, is_image,
                   is_audio, is_voice, is_video, buttons)

    msg.reply_text("Trigger '{}' añadido!".format(keyword))
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@connection_status
@user_admin
def stop_filter(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    args = msg.text.split(None, 1)

    if len(args) < 2:
        return

    chat_filters = sql.get_chat_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("Aquí no hay triggers activos!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat.id, args[1])
            msg.reply_text("Sí, dejaré de responder a eso.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "Ese no es un trigger actual: pon /filters para ver todos los triggers activos.")


@run_async
def reply_filter(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    to_match = extract_text(message)

    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + keyword + r"( |$|[^\w])"
        match = regex_searcher(pattern, to_match)
        if not match:
            #Skip to next item
            continue
        if match:
            filt = sql.get_filter(chat.id, keyword)
            if filt.is_sticker:
                message.reply_sticker(filt.reply)
            elif filt.is_document:
                message.reply_document(filt.reply)
            elif filt.is_image:
                message.reply_photo(filt.reply)
            elif filt.is_audio:
                message.reply_audio(filt.reply)
            elif filt.is_voice:
                message.reply_voice(filt.reply)
            elif filt.is_video:
                message.reply_video(filt.reply)
            elif filt.has_markdown:
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                try:
                    message.reply_text(
                        filt.reply,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)
                except BadRequest as excp:
                    if excp.message == "Protocolo de URL no admitido":
                        message.reply_text(
                            "Parece que intentas utilizar un protocolo de URL no compatible. Telegram "
                            "no admite botones para algunos protocolos, como tg: //. Por favor, inténtalo "
                            f"de nuevo, o pregunta en {SUPPORT_CHAT} por ayuda.")
                    elif excp.message == "Mensaje de respuesta no encontrado":
                        bot.send_message(
                            chat.id,
                            filt.reply,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True,
                            reply_markup=keyboard)
                    else:
                        message.reply_text(
                            "Esta nota no se pudo enviar porque tiene un formato incorrecto. Entra a "
                            f"{SUPPORT_CHAT} si no puedes entender por qué!")
                        LOGGER.warning("Message %s could not be parsed",
                                       str(filt.reply))
                        LOGGER.exception("Could not parse filter %s in chat %s",
                                         str(filt.keyword), str(chat.id))

            else:
                # LEGACY - all new filters will have has_markdown set to True.
                message.reply_text(filt.reply)
            break


def __stats__():
    return "{} triggers, en {} chats.".format(sql.num_filters(),
                                                 sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "Actualmente hay '{}' triggers personalizados aquí.".format(
        len(cust_filters))


__help__ = """
•`/filters`*:* Lista todos los triggers activos en este chat.

*Solo administradores:*
•`/filter <palabra clave> <mensaje de respuesta>`*:* Agrega un trigger a este chat. El bot ahora responderá ese mensaje siempre que una 'palabra clave' \
sea mencionada. Si responde a una pegatina con una palabra clave, el bot responderá con esa pegatina. \
Si desea que su palabra clave sea una oración, use comillas.
*Ejemplo:*`/filter" Hola allí "¿Cómo estás?`
•`/stop <palabra clave de trigger>`*: * Detiene ese trigger.
Nota: Los triggers ahora tienen expresiones regulares, por lo que cualquier trigger existente que tenga no distingue entre mayúsculas y minúsculas de forma predeterminada. \
Para guardar expresiones regulares que no distinguen entre mayúsculas y minúsculas, utilice \
`/filter" (?i) mi oracion de respuesta" mi respuesta que ignora el caso` \
En caso de que necesite ayuda de expresiones regulares más avanzada, comuníquese con nosotros en {SUPPORT_CHAT}. 
"""

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter)
LIST_HANDLER = DisableAbleCommandHandler(
    "filters", list_handlers, admin_ok=True)
CUST_FILTER_HANDLER = MessageHandler(CustomFilters.has_text, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)

__mod_name__ = "Filters"
__handlers__ = [
    FILTER_HANDLER, STOP_HANDLER, LIST_HANDLER,
    (CUST_FILTER_HANDLER, HANDLER_GROUP)
]
