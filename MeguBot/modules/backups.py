import json, time, os
from io import BytesIO

from telegram import ParseMode, Message
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

import MeguBot.modules.sql.notes_sql as sql
from MeguBot import dispatcher, LOGGER, OWNER_ID, MESSAGE_DUMP
from MeguBot.__main__ import DATA_IMPORT
from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.helper_funcs.alternate import typing_action

# from MeguBot.modules.rules import get_rules
import MeguBot.modules.sql.rules_sql as rulessql

# from MeguBot.modules.sql import warns_sql as warnssql
import MeguBot.modules.sql.blacklist_sql as blacklistsql
from MeguBot.modules.sql import disable_sql as disabledsql

# from MeguBot.modules.sql import cust_filters_sql as filtersql
# import MeguBot.modules.sql.welcome_sql as welcsql
import MeguBot.modules.sql.locks_sql as locksql
from MeguBot.modules.connection import connected


@run_async
@user_admin
@typing_action
def import_data(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text("Este es un comando solo para grupos!")
            return ""

        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = context.bot.get_file(
                msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text(
                "Intente descargar y cargar el archivo usted mismo nuevamente, este me aparece roto!"
            )
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text(
                "Hay más de un grupo en este archivo y el chat.id no es el mismo. ¿Cómo se supone que debo importarlo??"
            )
            return

        # Check if backup is this chat
        try:
            if data.get(str(chat.id)) == None:
                if conn:
                    text = "La copia de seguridad proviene de otro chat, no puedo devolver otro chat al chat *{}*".format(
                        chat_name)
                else:
                    text = "La copia de seguridad proviene de otro chat, no puedo devolver otro chat a este chat"
                return msg.reply_text(text, parse_mode="markdown")
        except Exception:
            return msg.reply_text(
                "Hubo un problema al importar los datos!")
        # Check if backup is from self
        try:
            if str(context.bot.id) != str(data[str(chat.id)]["bot"]):
                return msg.reply_text(
                    "La copia de seguridad de otro bot que no se sugiere puede causar el problema, los documentos, las fotos, los videos, los audios, los registros pueden no funcionar como deberían.."
                )
        except Exception:
            pass
        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]["hashes"]
        else:
            data = data[list(data.keys())[0]]["hashes"]

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text(
                "Se produjo un error al recuperar sus datos. El proceso falló. Si tiene algún problema con esto, llévelo a @MeguSupport"
            )

            LOGGER.exception(
                "Falló la importación para el chat %s con el nombre %s.",
                str(chat.id),
                str(chat.title),
            )
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        if conn:

            text = "Copia de seguridad completamente restaurada en *{}*.".format(chat_name)
        else:
            text = "Copia de seguridad completamente restaurada"
        msg.reply_text(text, parse_mode="markdown")


@run_async
@user_admin
def export_data(update, context):
    chat_data = context.chat_data
    msg = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    current_chat_id = update.effective_chat.id
    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        # chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text("Este es un comando solo para grupos!")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        # chat_name = update.effective_message.chat.title

    jam = time.time()
    new_jam = jam + 10800
    checkchat = get_chat(chat_id, chat_data)
    if checkchat.get("status"):
        if jam <= int(checkchat.get("value")):
            timeformatt = time.strftime("%H:%M:%S %d/%m/%Y",
                                        time.localtime(checkchat.get("value")))
            update.effective_message.reply_text(
                "Solo puedes hacer una copia de seguridad una vez al día!\nPuedes hacer una copia de seguridad de nuevo en aproximadamente `{}`"
                .format(timeformatt),
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        else:
            if user.id != OWNER_ID:
                put_chat(chat_id, new_jam, chat_data)
    else:
        if user.id != OWNER_ID:
            put_chat(chat_id, new_jam, chat_data)

    note_list = sql.get_all_chat_notes(chat_id)
    backup = {}
    notes = {}
    # button = ""
    buttonlist = []
    namacat = ""
    isicat = ""
    rules = ""
    count = 0
    countbtn = 0
    # Notes
    for note in note_list:
        count += 1
        # getnote = sql.get_note(chat_id, note.name)
        namacat += "{}<###splitter###>".format(note.name)
        if note.msgtype == 1:
            tombol = sql.get_buttons(chat_id, note.name)
            # keyb = []
            for btn in tombol:
                countbtn += 1
                if btn.same_line:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), True))
                else:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), False))
            isicat += "###button###: {}<###button###>{}<###splitter###>".format(
                note.value, str(buttonlist))
            buttonlist.clear()
        elif note.msgtype == 2:
            isicat += "###sticker###:{}<###splitter###>".format(note.file)
        elif note.msgtype == 3:
            isicat += "###file###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value)
        elif note.msgtype == 4:
            isicat += "###photo###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value)
        elif note.msgtype == 5:
            isicat += "###audio###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value)
        elif note.msgtype == 6:
            isicat += "###voice###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value)
        elif note.msgtype == 7:
            isicat += "###video###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value)
        elif note.msgtype == 8:
            isicat += "###video_note###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value)
        else:
            isicat += "{}<###splitter###>".format(note.value)
    for x in range(count):
        notes["#{}".format(namacat.split("<###splitter###>")[x])] = "{}".format(
            isicat.split("<###splitter###>")[x])
    # Rules
    rules = rulessql.get_rules(chat_id)
    # Blacklist
    bl = list(blacklistsql.get_chat_blacklist(chat_id))
    # Disabled command
    disabledcmd = list(disabledsql.get_all_disabled(chat_id))
    # Filters (TODO)
    """
	all_filters = list(filtersql.get_chat_triggers(chat_id))
	export_filters = {}
	for filters in all_filters:
		filt = filtersql.get_filter(chat_id, filters)
		# print(vars(filt))
		if filt.is_sticker:
			tipefilt = "sticker"
		elif filt.is_document:
			tipefilt = "doc"
		elif filt.is_image:
			tipefilt = "img"
		elif filt.is_audio:
			tipefilt = "audio"
		elif filt.is_voice:
			tipefilt = "voice"
		elif filt.is_video:
			tipefilt = "video"
		elif filt.has_buttons:
			tipefilt = "button"
			buttons = filtersql.get_buttons(chat.id, filt.keyword)
			print(vars(buttons))
		elif filt.has_markdown:
			tipefilt = "text"
		if tipefilt == "button":
			content = "{}#=#{}|btn|{}".format(tipefilt, filt.reply, buttons)
		else:
			content = "{}#=#{}".format(tipefilt, filt.reply)
		print(content)
		export_filters[filters] = content
	print(export_filters)
	"""
    # Welcome (TODO)
    # welc = welcsql.get_welc_pref(chat_id)
    # Locked
    curr_locks = locksql.get_locks(chat_id)
    curr_restr = locksql.get_restr(chat_id)

    if curr_locks:
        locked_lock = {
            "sticker": curr_locks.sticker,
            "audio": curr_locks.audio,
            "voice": curr_locks.voice,
            "document": curr_locks.document,
            "video": curr_locks.video,
            "contact": curr_locks.contact,
            "photo": curr_locks.photo,
            "gif": curr_locks.gif,
            "url": curr_locks.url,
            "bots": curr_locks.bots,
            "forward": curr_locks.forward,
            "game": curr_locks.game,
            "location": curr_locks.location,
            "rtl": curr_locks.rtl,
        }
    else:
        locked_lock = {}

    if curr_restr:
        locked_restr = {
            "messages":
                curr_restr.messages,
            "media":
                curr_restr.media,
            "other":
                curr_restr.other,
            "previews":
                curr_restr.preview,
            "all":
                all([
                    curr_restr.messages,
                    curr_restr.media,
                    curr_restr.other,
                    curr_restr.preview,
                ]),
        }
    else:
        locked_restr = {}

    locks = {"locks": locked_lock, "restrict": locked_restr}
    # Warns (TODO)
    # warns = warnssql.get_warns(chat_id)
    # Backing up
    backup[chat_id] = {
        "bot": context.bot.id,
        "hashes": {
            "info": {
                "rules": rules
            },
            "extra": notes,
            "blacklist": bl,
            "disabled": disabledcmd,
            "locks": locks,
        },
    }
    baccinfo = json.dumps(backup, indent=4)
    f = open("MeguBot{}.backup".format(chat_id), "w")
    f.write(str(baccinfo))
    f.close()
    context.bot.sendChatAction(current_chat_id, "upload_document")
    tgl = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime(time.time()))
    try:
        context.bot.sendMessage(
            MESSAGE_DUMP,
            "*Copia de seguridad importada con éxito:*\nChat: `{}`\nChat ID: `{}`\nEn: `{}`"
            .format(chat.title, chat_id, tgl),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest:
        pass
    context.bot.sendDocument(
        current_chat_id,
        document=open("MeguBot{}.backup".format(chat_id), "rb"),
        caption="*Copia de seguridad exportada con éxito:*\nChat: `{}`\nChat ID: `{}`\nEn: `{}`\n\nNota: Este `MeguBot-Backup`fue hecho especialmente para mensajes."
        .format(chat.title, chat_id, tgl),
        timeout=360,
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )
    os.remove("MeguBot{}.backup".format(chat_id))  # Cleaning file


# Temporary data
def put_chat(chat_id, value, chat_data):
    # print(chat_data)
    if value == False:
        status = False
    else:
        status = True
    chat_data[chat_id] = {"backups": {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # print(chat_data)
    try:
        value = chat_data[chat_id]["backups"]
        return value
    except KeyError:
        return {"status": False, "value": False}


__mod_name__ = "Backups"

__help__ = """
*Solo para propietario de grupo:*

 × /import: Responde al archivo de respaldo para que el grupo mayordomo importe tanto como sea posible, haciendo que las transferencias sean muy fáciles! \
 Tenga en cuenta que los archivos/fotos no se pueden importar debido a restricciones de telegram.

 × /export: Los datos del grupo de exportación, que se exportarán son: reglas, mensajes (documentos, imágenes, música, video, audio, voz, texto, botones de texto) \

"""

IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data, pass_chat_data=True)

dispatcher.add_handler(IMPORT_HANDLER)
dispatcher.add_handler(EXPORT_HANDLER)
