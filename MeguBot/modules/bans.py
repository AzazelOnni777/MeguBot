import html

from MeguBot import (DEV_USERS, LOGGER, OWNER_ID, SUDO_USERS,
                          SUPPORT_USERS, TIGER_USERS, WHITELIST_USERS,
                          dispatcher)
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import (
    bot_admin, can_restrict, connection_status, is_user_admin,
    is_user_ban_protected, is_user_in_chat, user_admin, user_can_ban)
from MeguBot.modules.helper_funcs.extraction import extract_user_and_text
from MeguBot.modules.helper_funcs.string_handling import extract_time
from MeguBot.modules.log_channel import gloggable, loggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a esta persona.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Oh sí, banéame, noob!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("Tratando de oponerme en contra de mi creador, eh?")
            return log_message
        elif user_id in DEV_USERS:
            message.reply_text("Estas loco?")
            return log_message
        elif user_id in SUDO_USERS:
            message.reply_text(
                "Usaria toda la magia existente para hacerl@ explotar pero no valdria la pena..."
            )
            return log_message
        elif user_id in SUPPORT_USERS:
            message.reply_text(
                "Lo haria explotar pero es mi soporte.¿Que haria si me quedo sin magia?"
            )
            return log_message
        elif user_id in TIGER_USERS:
            message.reply_text(
                "Lo haria explotar pero es inmune a las explosiones,¿de que estará hecho?"
            )
            return log_message
        elif user_id in WHITELIST_USERS:
            message.reply_text(
                "Lo haria explotar pero es inmune a las explosiones,¿de que estará hecho?"
            )
            return log_message
        else:
            message.reply_text("Este usuario tiene inmunidad - No puedo banearlo..")
            return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Baneado\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}")
    if reason:
        log += "\n<b>Razón:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            "Usuario baneado: {}.".format(
                mention_html(member.user.id, member.user.first_name)),
            parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no funciona":
            # Do not reply
            message.reply_text('Baneado!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR baneando al usuario %s en el chat %s (% s) debido a %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Uhm ... eso no funcionó...")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Yo no voy a PROHIBIR, estás loco?")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("No me apetece.")
        return log_message

    if not reason:
        message.reply_text("No has especificado un momento para prohibir a este usuario.!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP Baneado\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Tiempo:</b> {time_val}")
    if reason:
        log += "\n<b>Razón:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"Banned! User {mention_html(member.user.id, member.user.first_name)} "
            f"will be banned for {time_val}.",
            parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text(
                f"Baneado! El usuario será baneado por {time_val}.", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR baneando al usuario %s en el chat %s (% s) debido a %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Bueno maldita sea, no puedo prohibir a ese usuario.")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def exploit(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Siiii, no voy a hacer eso.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Realmente desearía poder hacer explotar a este usuario....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"Explotado! {mention_html(member.user.id, member.user.first_name)} :3",
            parse_mode=ParseMode.HTML)
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            log += f"\n<b>Razón:</b> {reason}"

        return log

    else:
        message.reply_text("Bueno maldita sea, no puedo hacer volar a ese usuario.")

    return log_message


@run_async
@bot_admin
@can_restrict
def exploitme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            "Desearía poder... pero eres un admin.")
        return

    res = update.effective_chat.unban_member(
        user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("*te saca del grupo*")
    else:
        update.effective_message.reply_text("¿Eh? No puedo :/")


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("¿Cómo me desharía del ban si no estuviera aquí ...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("¿No está esta persona ya aquí??")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("Sí, este usuario puede unirse!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UnBan\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}")
    if reason:
        log += f"\n<b>Razón:</b> {reason}"

    return log


@run_async
@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(context: CallbackContext, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in SUDO_USERS or user.id not in TIGER_USERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Dame un ID de chat válido.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("No estás ya en el chat?")
        return

    chat.unban_member(user.id)
    message.reply_text("Yup, te he desbaneado.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UnBan\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}")

    return log


__help__ = """
• `/exploitme`*:* Explota al usuario que emitió el comando

*Solo administradores:*
 • `/ban <userhandle>`*: * Prohíbe a un usuario. (a través de manejar o responder)
 • `/tban <userhandle> x (m / h / d)`*: * Prohíbe a un usuario durante el tiempo `x`. (a través del identificador o respuesta). `m` =` minutos`, `h` =` horas`, `d` =` días`.
 • `/unban <userhandle>`*: * Desbloquea a un usuario. (a través de manejar o responder)
 • `/exploit <userhandle>`*: * Saca a un usuario del grupo, (a través del identificador o respuesta)
"""

BAN_HANDLER = CommandHandler("ban", ban)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban)
EXPLOIT_HANDLER = CommandHandler("exploit", exploit)
UNBAN_HANDLER = CommandHandler("unban", unban)
ROAR_HANDLER = CommandHandler("roar", selfunban)
EXPLOITME_HANDLER = DisableAbleCommandHandler(
    "exploitme", exploitme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(EXPLOIT_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(EXPLOITME_HANDLER)

__mod_name__ = "Bans"
__handlers__ = [
    BAN_HANDLER, TEMPBAN_HANDLER, EXPLOIT_HANDLER, UNBAN_HANDLER, ROAR_HANDLER,
    EXPLOITME_HANDLER
]
