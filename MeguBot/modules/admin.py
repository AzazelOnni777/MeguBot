import html

from MeguBot import SUDO_USERS, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import (bot_admin, can_pin,
                                                           can_promote,
                                                           connection_status,
                                                           user_admin)
from MeguBot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from MeguBot.modules.log_channel import loggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    log_message = ""

    promoter = chat.get_member(user.id)

    if not (promoter.can_promote_members or
            promoter.status == "creator") and not user.id in SUDO_USERS:
        message.reply_text("No tienes los derechos necesarios para hacer eso!")
        return log_message

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto.."
        )
        return log_message

    try:
        user_member = chat.get_member(user_id)
    except:
        return log_message

    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text(
            "¿Cómo se supone que debo promover a alguien que ya es administrador?")
        return log_message

    if user_id == bot.id:
        message.reply_text(
            "¡No puedo promoverme! Consiga un administrador para que lo haga por mí.")
        return log_message

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages)
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text(
                "No puedo promover a alguien que no está en el grupo..")
            return log_message
        else:
            message.reply_text("Ocurrió un error al promoverlo.")
            return log_message

    bot.sendMessage(
        chat.id,
        f"Sucessfully promoted <b>{user_member.user.first_name or user_id}</b>!",
        parse_mode=ParseMode.HTML)

    log_message += (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#Promovido\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    log_message = ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto.."
        )
        return log_message

    try:
        user_member = chat.get_member(user_id)
    except:
        return log_message

    if user_member.status == 'creator':
        message.reply_text(
            "Este men CREÓ el chat, ¿cómo lo rebajaria?")
        return log_message

    if not user_member.status == 'administrator':
        message.reply_text("No puedo rebajar a quien no promoví!")
        return log_message

    if user_id == bot.id:
        message.reply_text(
            "¡No puedo rebajarme! Consiga a un admin para que lo haga por mí.")
        return log_message

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False)

        bot.sendMessage(
            chat.id,
            f"Haz sido rebajado <b>{user_member.user.first_name or user_id}</b>! :)",
            parse_mode=ParseMode.HTML)

        log_message += (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Rebajado\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "No se pudo rebajar. Puede que no sea administrador o que el admin fue designado por otro"
            " usuario, por lo que no puedo actuar sobre ellos!")
        return log_message


# Until the library releases the method
@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto.."
        )
        return

    if user_member.status == 'creator':
        message.reply_text(
            "Este men CREÓ el chat, ¿cómo puedo configurar un título personalizado para él??")
        return

    if not user_member.status == 'administrator':
        message.reply_text(
            "¡No se puede establecer un título para no administradores!\nPromuevalo primero para establecer un título personalizado!"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "¡No puedo establecer mi propio título! Haz que el que me dio admin lo haga por mí."
        )
        return

    if not title:
        message.reply_text("Establecer un título en blanco no hace nada!")
        return

    if len(title) > 16:
        message.reply_text(
            "La longitud del título es superior a 16 caracteres. \nTruncalo a 16 caracteres."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text(
            "No puedo establecer un título personalizado para administradores que no promoví!")
        return

    bot.sendMessage(
        chat.id,
        f"Se estableció correctamente el título para <code>{user_member.user.first_name or user_id}</code> "
        f"a <code>{title[:16]}</code>!",
        parse_mode=ParseMode.HTML)


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower()
                         == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id,
                prev_message.message_id,
                disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Fijado\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}")

        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#Desfijado\n"
                   f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}")

    return log_message


@run_async
@bot_admin
@user_admin
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "No tengo acceso al enlace de invitación, intente cambiar mis permisos!"
            )
    else:
        update.effective_message.reply_text(
            "Solo puedo darte enlaces de invitación para supergrupos y canales, lo siento!"
        )


@run_async
@connection_status
def adminlist(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    chat_id = chat.id
    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    administrators = bot.getChatAdministrators(chat_id)

    if update_chat_title == message_chat_title:
        chat_name = "this chat"
    else:
        chat_name = update_chat_title

    text = f"Administradores en *{chat_name}*:"

    for admin in administrators:
        user = admin.user
        name = f"[{user.first_name + (user.last_name or '')}](tg://user?id={user.id})"
        text += f"\n - {name}"

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return "Eres *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in (
            "administrator", "creator"))


__help__ = """
• `/adminlist`*:* Lista de administradores en el chat

*Solo administradores:*
 • `/pin`*:* Fija silenciosamente el mensaje al que respondió - agregue` 'loud'` o `' notify'` para dar notificaciones a los usuarios.
 • `/unpin`*:* Quita el mensaje anclado actualmente.
 • `/invitelink`*:* Obtén el link del grupo.
 • `/promote`*:* Promueve el usuario al que respondió.
 • `/demote`*:* Rebaja al usuario al que respondió.
 • `/settitle`*:* Establece un título personalizado para un administrador que promovió el bot.
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "admins"],
                                              adminlist)

PIN_HANDLER = CommandHandler("pin", pin, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler(
    "invitelink", invite, filters=Filters.group)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote)

SET_TITLE_HANDLER = CommandHandler("settitle", set_title)

dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)

__mod_name__ = "Admin"
__command_list__ = ["adminlist", "admins", "invitelink", "promote", "demote"]
__handlers__ = [
    ADMINLIST_HANDLER, PIN_HANDLER, UNPIN_HANDLER, INVITE_HANDLER,
    PROMOTE_HANDLER, DEMOTE_HANDLER, SET_TITLE_HANDLER
]
