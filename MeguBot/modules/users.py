from io import BytesIO
from time import sleep

import MeguBot.modules.sql.users_sql as sql
from MeguBot import DEV_USERS, LOGGER, OWNER_ID, dispatcher
from MeguBot.modules.helper_funcs.chat_status import dev_plus, sudo_plus
from MeguBot.modules.sql.users_sql import get_all_users
from telegram import TelegramError, Update
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)

USERS_GROUP = 4
CHAT_GROUP = 5
DEV_AND_MORE = DEV_USERS.append(int(OWNER_ID))


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith('@'):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == 'Chat not found':
                    pass
                else:
                    LOGGER.exception("Error al extraer el ID de usuario")

    return None


@run_async
@dev_plus
def broadcast(update: Update, context: CallbackContext):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        to_group = to_user = False
        if to_send[0] == '/broadcastgroup':
            to_group = True
        if to_send[0] == '/broadcastuser':
            to_user = True
        else:
            to_group = to_user = True
        chats = sql.get_all_chats() or []
        users = get_all_users()
        failed = 0
        failed_user = 0
        if to_group:
            for chat in chats:
                try:
                    context.bot.sendMessage(int(chat.chat_id), to_send[1])
                    sleep(0.1)
                except TelegramError:
                    failed += 1
                    LOGGER.warning(
                        "Couldn't send broadcast to %s, group name %s",
                        str(chat.chat_id), str(chat.chat_name))
        if to_user:
            for user in users:
                try:
                    context.bot.sendMessage(int(user.user_id), to_send[1])
                    sleep(0.1)
                except TelegramError:
                    failed_user += 1
                    LOGGER.warning("Couldn't send broadcast to %s",
                                   str(user.user_id))

        update.effective_message.reply_text(
            f"Transmisión completa. {failed} grupos no pudieron recibir el mensaje, probablemente debido a que fueron expulsados. {failed_user} no pudo recibir el mensaje, probablemente debido a que estaba bloqueado"
        )


@run_async
def log_user(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    sql.update_user(msg.from_user.id, msg.from_user.username, chat.id,
                    chat.title)

    if msg.reply_to_message:
        sql.update_user(msg.reply_to_message.from_user.id,
                        msg.reply_to_message.from_user.username, chat.id,
                        chat.title)

    if msg.forward_from:
        sql.update_user(msg.forward_from.id, msg.forward_from.username)


@run_async
@sudo_plus
def chats(update: Update, context: CallbackContext):
    all_chats = sql.get_all_chats() or []
    chatfile = 'Lista de chats.\n0. Nombre del chat | ID de chat | Cantidad de Miembros\n'
    P = 1
    for chat in all_chats:
        try:
            curr_chat = bot.getChat(chat.chat_id)
            bot_member = curr_chat.get_member(bot.id)
            chat_members = curr_chat.get_members_count(bot.id)
            chatfile += "{}. {} | {} | {}\n".format(P, chat.chat_name,
                                                    chat.chat_id, chat_members)
            P = P + 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="chatlist.txt",
            caption="Aquí está la lista de chats en mi base de datos.")


@run_async
def chat_checker(update: Update, context: CallbackContext):
    bot = context.bot
    if update.effective_message.chat.get_member(
            bot.id).can_send_messages is False:
        bot.leaveChat(update.effective_message.chat.id)


def __user_info__(user_id):
    if user_id == dispatcher.bot.id:
        return """Los he visto en... Wow. Me están acechando? Están en los mismos lugares que yo... oh. Soy yo."""
    num_chats = sql.get_user_num_chats(user_id)
    return f"""Los he visto en <code>{num_chats}</code> chats en total."""


def __stats__():
    return f"Usuarios de {sql.num_users()} en los chats de {sql.num_chats()}"


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

BROADCAST_HANDLER = CommandHandler(
    ["broadcastall", "broadcastuser", "broadcastgroup"], broadcast)
USER_HANDLER = MessageHandler(Filters.all & Filters.group, log_user)
CHAT_CHECKER_HANDLER = MessageHandler(Filters.all & Filters.group, chat_checker)
CHATLIST_HANDLER = CommandHandler("chatlist", chats)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)

__mod_name__ = "Users"
__handlers__ = [(USER_HANDLER, USERS_GROUP), BROADCAST_HANDLER,
                CHATLIST_HANDLER]
