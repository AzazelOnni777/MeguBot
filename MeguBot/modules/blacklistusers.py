# Module to blacklist users and prevent them from using commands by @TheRealPhoenix

import MeguBot.modules.sql.blacklistusers_sql as sql
from MeguBot import (DEV_USERS, OWNER_ID, SUDO_USERS, SUPPORT_USERS,
                          WHITELIST_USERS, dispatcher)
from MeguBot.modules.helper_funcs.chat_status import dev_plus
from MeguBot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from MeguBot.modules.log_channel import gloggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

BLACKLISTWHITELIST = [
    OWNER_ID
] + DEV_USERS + SUDO_USERS + WHITELIST_USERS + SUPPORT_USERS
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@run_async
@dev_plus
@gloggable
def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return ""

    if user_id == bot.id:
        message.reply_text(
            "¿Cómo se supone que debo hacer mi trabajo si me ignoro a mí misma?")
        return ""

    if user_id in BLACKLISTWHITELIST:
        message.reply_text("No!\nNotar los desastres es mi trabajo.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            raise

    sql.blacklist_user(user_id, reason)
    message.reply_text("Ignoraré la existencia de este usuario.!")
    log_message = (
        f"#BlackList\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(target_user.id, target_user.first_name)}")
    if reason:
        log_message += f"\n<b>Razón:</b> {reason}"

    return log_message


@run_async
@dev_plus
@gloggable
def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return ""

    if user_id == bot.id:
        message.reply_text("Siempre me doy cuenta de mi misma.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        message.reply_text("*Notifica al usuario*")
        log_message = (
            f"#UnBlackList\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(target_user.id, target_user.first_name)}"
        )

        return log_message

    else:
        message.reply_text("Sin embargo, no lo estoy ignorando en absoluto!")
        return ""


@run_async
@dev_plus
def bl_users(update: Update, context: CallbackContext):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = bot.get_chat(each_user)
        reason = sql.get_reason(each_user)

        if reason:
            users.append(
                f"• {mention_html(user.id, user.first_name)} :- {reason}")
        else:
            users.append(f"• {mention_html(user.id, user.first_name)}")

    message = "<b>Usuarios incluidos en la BlackList</b>\n"
    if not users:
        message += "Nadie está siendo ignorado por el momento."
    else:
        message += '\n'.join(users)

    update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "En la BlackList: <b>{}</b>"

    if is_blacklisted:
        text = text.format("Si")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\nRazón: <code>{reason}</code>"
    else:
        text = text.format("No")

    return text


BL_HANDLER = CommandHandler("ignore", bl_user)
UNBL_HANDLER = CommandHandler("notice", unbl_user)
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users)

dispatcher.add_handler(BL_HANDLER)
dispatcher.add_handler(UNBL_HANDLER)
dispatcher.add_handler(BLUSERS_HANDLER)

__mod_name__ = "BlackList de Usuarios"
__handlers__ = [BL_HANDLER, UNBL_HANDLER, BLUSERS_HANDLER]
