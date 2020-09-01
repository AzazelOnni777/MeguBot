import html

import MeguBot.modules.sql.userinfo_sql as sql
from MeguBot import DEV_USERS, SUDO_USERS, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.extraction import extract_user
from telegram import MAX_MESSAGE_LENGTH, ParseMode, Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown


@run_async
def about_me(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(
            f"{username} aún no ha establecido un mensaje de información sobre el!")
    else:
        update.effective_message.reply_text(
            "Aún no estableciste un mensaje de información sobre ti!")


@run_async
def set_about_me(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id
    bot = context.bot
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id == bot.id and (user_id in SUDO_USERS or
                                       user_id in DEV_USERS):
            user_id = repl_user_id

    text = message.text
    info = text.split(None, 1)

    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id == bot.id:
                message.reply_text("Actualicé mi información!")
            else:
                message.reply_text("Actualicé tu información!")
        else:
            message.reply_text(
                "La información debe tener menos de {} caracteres! Tu tienes {}.".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
def about_bio(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text(
            f"{username} aún no ha establecido un mensaje sobre sí mismo!")
    else:
        update.effective_message.reply_text(
            "Aún no tienes una biografía sobre ti!")


@run_async
def set_about_bio(update: Update, context: CallbackContext):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == message.from_user.id:
            message.reply_text(
                "No puedes establecer tu propia biografía! Estás a merced de los demás aquí..."
            )
            return

        if user_id == bot.id and sender_id not in SUDO_USERS and sender_id not in DEV_USERS:
            message.reply_text(
                "Erm..., solo confío en los usuarios sudo y desarrolladores para configurar mi biografía."
            )
            return

        text = message.text
        bio = text.split(
            None, 1
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("Updated {}'s bio!".format(
                    repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "Una biografía debe tener menos de {} caracteres! Intentaste configurar {}."
                    .format(MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Responde al mensaje de alguien para establecer su biografía!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return f"<b>Acerca del usuario:</b>\n{me}\n<b>Lo que otros dicen:</b>\n{bio}"
    elif bio:
        return f"<b>Lo que otros dicen:</b>\n{bio}\n"
    elif me:
        return f"<b>Acerca del usuario:</b>\n{me}"
    else:
        return ""


__help__ = """
 • `/setbio <text>`*:* Mientras responde, guardará la biografía de otro usuario.
 • `/bio`*:* Obtendrá tu biografía o la de otro usuario. Esto no lo puede configurar usted mismo.
 • `/setme <text>`*:* Establecerá su información.
 •` /me`*:* Obtendrá tu información o la de otro usuario.
"""

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

__mod_name__ = "Bios e info"
__command_list__ = ["setbio", "bio", "setme", "me"]
__handlers__ = [
    SET_BIO_HANDLER, GET_BIO_HANDLER, SET_ABOUT_HANDLER, GET_ABOUT_HANDLER
]
