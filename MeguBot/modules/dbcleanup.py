from time import sleep

import MeguBot.modules.sql.global_bans_sql as gban_sql
import MeguBot.modules.sql.users_sql as user_sql
from MeguBot import DEV_USERS, OWNER_ID, dispatcher
from MeguBot.modules.helper_funcs.chat_status import dev_plus
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          run_async)


def get_invalid_chats(update: Update,
                      context: CallbackContext,
                      remove: bool = False):
    bot = context.bot
    chat_id = update.effective_chat.id
    chats = user_sql.get_all_chats()
    kicked_chats, progress = 0, 0
    chat_list = []
    progress_message = None

    for chat in chats:

        if ((100 * chats.index(chat)) / len(chats)) > progress:
            progress_bar = f"{progress}% completado para obtener chats no válidos."
            if progress_message:
                try:
                    bot.editMessageText(progress_bar, chat_id,
                                        progress_message.message_id)
                except:
                    pass
            else:
                progress_message = bot.sendMessage(chat_id, progress_bar)
            progress += 5

        cid = chat.chat_id
        sleep(0.1)
        try:
            bot.get_chat(cid, timeout=60)
        except (BadRequest, Unauthorized):
            kicked_chats += 1
            chat_list.append(cid)
        except:
            pass

    try:
        progress_message.delete()
    except:
        pass

    if not remove:
        return kicked_chats
    else:
        for muted_chat in chat_list:
            sleep(0.1)
            user_sql.rem_chat(muted_chat)
        return kicked_chats


def get_invalid_gban(update: Update,
                     context: CallbackContext,
                     remove: bool = False):
    bot = context.bot
    banned = gban_sql.get_gban_list()
    ungbanned_users = 0
    ungban_list = []

    for user in banned:
        user_id = user["user_id"]
        sleep(0.1)
        try:
            bot.get_chat(user_id)
        except BadRequest:
            ungbanned_users += 1
            ungban_list.append(user_id)
        except:
            pass

    if not remove:
        return ungbanned_users
    else:
        for user_id in ungban_list:
            sleep(0.1)
            gban_sql.ungban_user(user_id)
        return ungbanned_users


@run_async
@dev_plus
def dbcleanup(update: Update, context: CallbackContext):
    msg = update.effective_message

    msg.reply_text("Obteniendo un recuento de chats no válidos ...")
    invalid_chat_count = get_invalid_chats(context, update)

    msg.reply_text("Obteniendo un recuento de baneados globalmente no válido")
    invalid_gban_count = get_invalid_gban(context, update)

    reply = f"Total de chats no válidos - {invalid_chat_count}\n"
    reply += f"Total de usuarios de baneados globalmente no válidos - {invalid_gban_count}"

    buttons = [[InlineKeyboardButton("Limpiar BD", callback_data="db_cleanup")]]

    update.effective_message.reply_text(
        reply, reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def callback_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    message = query.message
    chat_id = update.effective_chat.id
    query_type = query.data

    admin_list = [OWNER_ID] + DEV_USERS

    bot.answer_callback_query(query.id)

    if query_type == "db_leave_chat":
        if query.from_user.id in admin_list:
            bot.editMessageText("Dejando chats ...", chat_id,
                                message.message_id)
            chat_count = get_muted_chats(update, context, True)
            bot.sendMessage(chat_id, f"Chats abandonados: {chat_count}.")
        else:
            query.answer("No tienes permitido usar esto.")
    elif query_type == "db_cleanup":
        if query.from_user.id in admin_list:
            bot.editMessageText("Limpiando BD ...", chat_id,
                                message.message_id)
            invalid_chat_count = get_invalid_chats(update, context, True)
            invalid_gban_count = get_invalid_gban(update, context, True)
            reply = "Se limpiaron {} chats y {} usuarios bloqueados globalmente de la BD.".format(
                invalid_chat_count, invalid_gban_count)
            bot.sendMessage(chat_id, reply)
        else:
            query.answer("No tienes permitido usar esto.")


DB_CLEANUP_HANDLER = CommandHandler("dbcleanup", dbcleanup)
BUTTON_HANDLER = CallbackQueryHandler(callback_button, pattern='db_.*')

dispatcher.add_handler(DB_CLEANUP_HANDLER)
dispatcher.add_handler(BUTTON_HANDLER)

__mod_name__ = "DB Cleanup"
__handlers__ = [DB_CLEANUP_HANDLER, BUTTON_HANDLER]
