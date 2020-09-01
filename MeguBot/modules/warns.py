import html
import re
from typing import Optional

import telegram
from MeguBot import BAN_STICKER, TIGER_USERS, WHITELIST_USERS, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import (bot_admin,
                                                           can_restrict,
                                                           is_user_admin,
                                                           user_admin,
                                                           user_admin_no_reply)
from MeguBot.modules.helper_funcs.extraction import (extract_text,
                                                          extract_user,
                                                          extract_user_and_text)
from MeguBot.modules.helper_funcs.filters import CustomFilters
from MeguBot.modules.helper_funcs.misc import split_message
from MeguBot.modules.helper_funcs.string_handling import split_quotes
from MeguBot.modules.log_channel import loggable
from MeguBot.modules.sql import warns_sql as sql
from telegram import (CallbackQuery, Chat, InlineKeyboardButton,
                      InlineKeyboardMarkup, Message, ParseMode, Update, User)
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          DispatcherHandlerStop, Filters, MessageHandler,
                          run_async)
from telegram.utils.helpers import mention_html

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Filtros de advertencia actuales en este chat:</b>\n"


# Not async
def warn(user: User,
         chat: Chat,
         reason: str,
         message: Message,
         warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        # message.reply_text("Damn admins, They are too far to be One Punched!")
        return

    if user.id in TIGER_USERS:
        if warner:
            message.reply_text("Los tigres no pueden ser advertidos.")
        else:
            message.reply_text(
                "El tigre activó un filtro de advertencia automática!\nNo puedo advertir a los tigres, pero deben evitar abusar de esto.."
            )
        return

    if user.id in WHITELIST_USERS:
        if warner:
            message.reply_text("Los lobos son inmunes a las advertencias.")
        else:
            message.reply_text(
                "El lobo activó un filtro de advertencia automática!\nNo puedo advertir a los lobos, pero deben evitar abusar de esto.."
            )
        return

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Filtro de advertencia automatizado."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # punch
            chat.unban_member(user.id)
            reply = f"{limit} advertencia's, *Hace volar a {mention_html(user.id, user.first_name)} con una explosion de bajo nivel!* "

        else:  # ban
            chat.kick_member(user.id)
            reply = f"{limit} advertencia's, *Hace volar a {mention_html(user.id, user.first_name)} con una explosion de nivel serio* "

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)  # megu's sticker
        keyboard = []
        log_reason = (f"<b>{html.escape(chat.title)}:</b>\n"
                      f"#WARN_BAN\n"
                      f"<b>Administrador:</b> {warner_tag}\n"
                      f"<b>Usuario:</b> {mention_html(user.id, user.first_name)}\n"
                      f"<b>Razón:</b> {reason}\n"
                      f"<b>Cuenta:</b> <code>{num_warns}/{limit}</code>")

    else:
        keyboard = InlineKeyboardMarkup([{
            InlineKeyboardButton(
                "Quitar Advertencia", callback_data="rm_warn({})".format(user.id))
        }])

        reply = f"{mention_html(user.id, user.first_name)} tiene {num_warns}/{limit} advertencias... cuidado!"
        if reason:
            reply += f"\nRazón de la última advertencia:\n{html.escape(reason)}"

        log_reason = (f"<b>{html.escape(chat.title)}:</b>\n"
                      f"#WARN\n"
                      f"<b>Administrador:</b> {warner_tag}\n"
                      f"<b>Usuario:</b> {mention_html(user.id, user.first_name)}\n"
                      f"<b>Razón:</b> {reason}\n"
                      f"<b>Cuenta:</b> <code>{num_warns}/{limit}</code>")

    try:
        message.reply_text(
            reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                reply,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                quote=False)
        else:
            raise
    return log_reason


@run_async
@user_admin_no_reply
@bot_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Advertencia eliminada por {}.".format(
                    mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML)
            user_member = chat.get_member(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNWARN\n"
                f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Usuario:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
            )
        else:
            update.effective_message.edit_text(
                "El usuario ya no tiene advertencias.", parse_mode=ParseMode.HTML)

    return ""


@run_async
@user_admin
@can_restrict
@loggable
def warn_user(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    warner: Optional[User] = update.effective_user

    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            return warn(message.reply_to_message.from_user, chat, reason,
                        message.reply_to_message, warner)
        else:
            return warn(
                chat.get_member(user_id).user, chat, reason, message, warner)
    else:
        message.reply_text("Eso me parece un ID de usuario no válida.")
    return ""


@run_async
@user_admin
@bot_admin
@loggable
def reset_warns(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Las advertencias se han restablecido!")
        warned = chat.get_member(user_id).user
        return (f"<b>{html.escape(chat.title)}:</b>\n"
                f"#RESETWARNS\n"
                f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Usuario:</b> {mention_html(warned.id, warned.first_name)}")
    else:
        message.reply_text("Ningún usuario ha sido designado!")
    return ""


@run_async
def warns(update: Update, context: CallbackContext):
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = f"Este usuario tiene {num_warns}/{limit} advertencias, por las siguientes razones:"
            for reason in reasons:
                text += f"\n - {reason}"

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                f"El usuario tiene {num_warns}/{limit} advertencias, pero no hay motivos para ninguna de ellas."
            )
    else:
        update.effective_message.reply_text("Este usuario no tiene advertencias!")


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(f"Controlador de advertencias agregado para '{keyword}'!")
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("No hay filtros de advertencia activos aquí!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Está bien, dejaré de advertir a la gente por eso.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "Ese no es un filtro de advertencia actual: Escribe /warnlist para ver todos los filtros de advertencia activos."
    )


@run_async
def list_warn_filters(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text(
            "No hay filtros de advertencia activos aquí!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(
            filter_list, parse_mode=ParseMode.HTML)


@run_async
@loggable
def reply_filter(update: Update, context: CallbackContext) -> str:
    chat: Optional[Chat] = update.effective_chat
    message: Optional[Message] = update.effective_message

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user: Optional[User] = update.effective_user
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@run_async
@user_admin
@loggable
def set_warn_limit(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("El límite mínimo de advertencias es 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Se actualizó el límite de advertencias a {}".format(args[0]))
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SET_WARN_LIMIT\n"
                    f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Set the warn limit to <code>{args[0]}</code>")
        else:
            msg.reply_text("Dame un número como argumento!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("El límite de advertencias actual es  {}".format(limit))
    return ""


@run_async
@user_admin
def set_warn_strength(update: Update, context: CallbackContext):
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Demasiadas advertencias ahora resultarán en un BAN!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has enabled strong warns. Users will be seriously punched.(banned)"
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text(
                "¡Demasiadas advertencias ahora resultarán en una explosion de bajo nivel! Los usuarios podrán unirse nuevamente después."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Ha desactivado las explosiones fuertes. Usaré una explosion de bajo nivel en los usuarios.."
            )

        else:
            msg.reply_text("Solo entiendo on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text(
                "Las advertencias están configuradas actualmente para hacer *volar* a los usuarios cuando exceden los límites.",
                parse_mode=ParseMode.MARKDOWN)
        else:
            msg.reply_text(
                "Las advertencias están configuradas actualmente para *explotar*(ban) a los usuarios cuando superan los límites.",
                parse_mode=ParseMode.MARKDOWN)
    return ""


def __stats__():
    return (
        f"{sql.num_warns()} advertencias generales en los chats de {sql.num_warn_chats()}.\n"
        f"{sql.num_warn_filters()} filtros de advertencia, en los chats de {sql.num_warn_filter_chats()}."
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get('warns', {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        f"Este chat tiene `{num_warn_filters}` filtros de advertencia. "
        f"Se necesitan `{limit}` advertencias antes de que el usuario reciba *{'kicked' if soft_warn else 'banned'}*."
    )


__help__ = """
• `/warns <userhandle>`*:* Obtiene el número de usuario y el motivo de las advertencias.
  • `/warnlist`*:* Lista de todos los filtros de advertencia actuales

*Solo administradores:*
  • `/warn <ID o alias de usuario>`*:* Advertir a un usuario. Después de 3 advertencias, el usuario será expulsado del grupo. También se puede utilizar como respuesta.
  • `/resetwarn <ID o alias de usuraio>`*:* Restablece las advertencias para un usuario. También se puede utilizar como respuesta.
  • `/addwarn <palabra clave> <mensaje de respuesta>`*:* Establece un filtro de advertencia en una determinada palabra clave. Si desea que su palabra clave\ser una oración, incluirla entre comillas, como tal: `/addwarn" Muy enojado "Este es un usuario enojado`.
  • `/nowarn <palabra clave>`*:* Detener un filtro de advertencia.
  • `/warnlimit <número>` *:* Establece el límite de advertencias.
  • `/strongwarn <on/yes/off/no>`*:* Si se activa, exceder el límite de advertencia resultará en un ban. De lo contrario, solo kickeará.
"""

__mod_name__ = "Advertencias"

WARN_HANDLER = CommandHandler("warn", warn_user, filters=Filters.group)
RESET_WARN_HANDLER = CommandHandler(["resetwarn", "resetwarns"],
                                    reset_warns,
                                    filters=Filters.group)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler(
    "warns", warns, filters=Filters.group)
ADD_WARN_HANDLER = CommandHandler(
    "addwarn", add_warn_filter, filters=Filters.group)
RM_WARN_HANDLER = CommandHandler(["nowarn", "stopwarn"],
                                 remove_warn_filter,
                                 filters=Filters.group)
LIST_WARN_HANDLER = DisableAbleCommandHandler(["warnlist", "warnfilters"],
                                              list_warn_filters,
                                              filters=Filters.group,
                                              admin_ok=True)
WARN_FILTER_HANDLER = MessageHandler(CustomFilters.has_text & Filters.group,
                                     reply_filter)
WARN_LIMIT_HANDLER = CommandHandler(
    "warnlimit", set_warn_limit, filters=Filters.group)
WARN_STRENGTH_HANDLER = CommandHandler(
    "strongwarn", set_warn_strength, filters=Filters.group)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
