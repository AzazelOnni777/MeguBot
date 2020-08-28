import datetime
from typing import List

import requests
from MeguBot import TIME_API_KEY, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async


def generate_time(to_find: str, findtype: List[str]) -> str:
    data = requests.get(
        f"https://api.timezonedb.com/v2.1/list-time-zone"
        f"?key={TIME_API_KEY}"
        f"&format=json"
        f"&fields=countryCode,countryName,zoneName,gmtOffset,timestamp,dst"
    ).json()

    for zone in data["zones"]:
        for eachtype in findtype:
            if to_find in zone[eachtype].lower():
                country_name = zone['countryName']
                country_zone = zone['zoneName']
                country_code = zone['countryCode']

                if zone['dst'] == 1:
                    daylight_saving = "Yes"
                else:
                    daylight_saving = "No"

                date_fmt = r"%d-%m-%Y"
                time_fmt = r"%H:%M:%S"
                day_fmt = r"%A"
                gmt_offset = zone['gmtOffset']
                timestamp = datetime.datetime.now(
                    datetime.timezone.utc) + datetime.timedelta(
                        seconds=gmt_offset)
                current_date = timestamp.strftime(date_fmt)
                current_time = timestamp.strftime(time_fmt)
                current_day = timestamp.strftime(day_fmt)

                break

    try:
        result = (
            f'<b>Pais:</b> <code>{country_name}</code>\n'
            f'<b>Nombre de zona:</b> <code>{country_zone}</code>\n'
            f'<b>Código de Pais:</b> <code>{country_code}</code>\n'
            f'<b>Horario de verano:</b> <code>{daylight_saving}</code>\n'
            f'<b>Día:</b> <code>{current_day}</code>\n'
            f'<b>Tiempo actual:</b> <code>{current_time}</code>\n'
            f'<b>Fecha actual:</b> <code>{current_date}</code>\n'
            '<b>Zonas horarias:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">Lista aquí</a>'
        )
    except:
        result = None

    return result


@run_async
def gettime(update: Update, context: CallbackContext):
    message = update.effective_message

    try:
        query = message.text.strip().split(" ", 1)[1]
    except:
        message.reply_text(
            "Dame un nombre/abreviatura/zona horaria del país para buscar.")
        return
    send_message = message.reply_text(
        f"Buscando información de zona horaria para <b>{query}</b>", parse_mode=ParseMode.HTML)

    query_timezone = query.lower()
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["countryCode"])
    else:
        result = generate_time(query_timezone, ["zoneName", "countryName"])

    if not result:
        send_message.edit_text(
            f'La información de zona horaria no está disponible para <b>{query}</b>\n'
            '<b>Todas las zonas horarias:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">Lista aquí</a>',
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
        return

    send_message.edit_text(
        result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


__help__ = """
 • `/time <lugar>`*:* Da información sobre una zona horaria.

*Lugares disponibles:* Código de país/Nombre de país/Nombre de zona horaria.
• 🕐 [Lista de Zonas Horarias](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
"""

TIME_HANDLER = DisableAbleCommandHandler("time", gettime)

dispatcher.add_handler(TIME_HANDLER)

__mod_name__ = "Tiempo"
__command_list__ = ["time"]
__handlers__ = [TIME_HANDLER]
