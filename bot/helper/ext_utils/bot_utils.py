import re
from re import match as re_match, findall as re_findall
from threading import Thread, Event
from time import time
from math import ceil
from html import escape
from psutil import cpu_percent, disk_usage, net_io_counters, virtual_memory
from requests import head as rhead
from urllib.request import urlopen

from bot import download_dict, download_dict_lock, botStartTime, DOWNLOAD_DIR, user_data, config_dict
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker

import shutil
import psutil
from telegram.error import RetryAfter
from telegram.ext import CallbackQueryHandler
from telegram.message import Message
from telegram.update import Update
from bot import *

MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"

URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"

COUNT = 0
PAGE_NO = 1
PAGES = 0


class MirrorStatus:
     STATUS_UPLOADING = "📤 Upload"
     STATUS_DOWNLOADING = "📥 Download"
     STATUS_CLONING = "♻️ Clone"
     STATUS_WAITING = "💤 Queue"
     STATUS_PAUSED = "⛔️ Pause"
     STATUS_ARCHIVING = "🔐 Archive"
     STATUS_EXTRACTING = "📂 Extract"
     STATUS_SPLITTING = "✂️ Split"
     STATUS_CHECKING = "📝 CheckUp"
     STATUS_SEEDING = "🌧 Seed"
    
class EngineStatus:
    STATUS_ARIA = "<b>Aria2c📶</b>"
    STATUS_GD = "<b>Google Api♻️</b>"
    STATUS_MEGA = "<b>MegaSDK⭕️</b>"
    STATUS_QB = "<b>qBittorrent🦠</b>"
    STATUS_TG = "<b>Pyrogram💥</b>"
    STATUS_YT = "<b>YT-dlp🌟</b>"
    STATUS_EXT = "<b>Extract | pExtract⚔️</b>"
    STATUS_SPLIT = "<b>FFmpeg✂️</b>"
    STATUS_ZIP = "<b>p7zip🛠</b>"
     
PROGRESS_MAX_SIZE = 100 // 9
PROGRESS_INCOMPLETE = ['◔', '◔', '◑', '◑', '◑', '◕', '◕']
# PROGRESS_INCOMPLETE = ['◌', '◌', '◎', '◎', '◎', '◍', '◍', '◍']
# PROGRESS_INCOMPLETE = ['▤', '▤', '▦', '▦', '▦', '▩', '▩']

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = Event()
        thread = Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time() + self.interval
        while not self.stopEvent.wait(nextTime - time()):
            self.action()
            nextTime = time() + self.interval

    def cancel(self):
        self.stopEvent.set()

def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'

def getDownloadByGid(gid):
    with download_dict_lock:
        for dl in list(download_dict.values()):
            if dl.gid() == gid:
                return dl
    return None

def progress_bar(percentage):
    """Returns a progress bar for download"""
    if isinstance(percentage, str):
        return "NaN"
    try:
        percentage = int(percentage)
    except Exception:
        percentage = 0
    comp = "▰"
    ncomp = "▱"
    return "".join(comp if i <= percentage // 10 else ncomp for i in range(1, 11))

def editMessage(text: str, message: Message, reply_markup=None):	
    try:	
        bot.editMessageText(text=text, message_id=message.message_id,	
                              chat_id=message.chat.id,reply_markup=reply_markup,	
                              parse_mode='HTMl', disable_web_page_preview=True)	
    except RetryAfter as r:	
        LOGGER.warning(str(r))	
        sleep(r.retry_after * 1.5)	
        return editMessage(text, message, reply_markup)	
    except Exception as e:	
        LOGGER.error(str(e))	
        return str(e)	
def deleteMessage(bot, message: Message):	
    try:	
        bot.deleteMessage(chat_id=message.chat.id,	
                           message_id=message.message_id)	
    except Exception as e:	
        LOGGER.error(str(e))	
def delete_all_messages():	
    with status_reply_dict_lock:	
        for data in list(status_reply_dict.values()):	
            try:	
                deleteMessage(bot, data[0])	
                del status_reply_dict[data[0].chat.id]	
            except Exception as e:	
                LOGGER.error(str(e))	
def update_all_messages(force=False):	
    with status_reply_dict_lock:	
        if not force and (not status_reply_dict or not Interval or time() - list(status_reply_dict.values())[0][1] < 3):	
            return	
        for chat_id in status_reply_dict:	
            status_reply_dict[chat_id][1] = time()	
    msg, buttons = get_readable_message()	
    if msg is None:	
        return	
    with status_reply_dict_lock:	
        for chat_id in status_reply_dict:	
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id][0].text:	
                if buttons == "":	
                    rmsg = editMessage(msg, status_reply_dict[chat_id][0])	
                else:	
                    rmsg = editMessage(msg, status_reply_dict[chat_id][0], buttons)	
                if rmsg == "Message to edit not found":	
                    del status_reply_dict[chat_id]	
                    return	
                status_reply_dict[chat_id][0].text = msg	
                status_reply_dict[chat_id][1] = time()



def getAllDownload(req_status: str):
    with download_dict_lock:
        for dl in list(download_dict.values()):
            status = dl.status()
            if req_status in ['all', status]:
                return dl
    return None

def bt_selection_buttons(id_: str):
    gid = id_[:12] if len(id_) > 20 else id_
    pincode = ""
    for n in id_:
        if n.isdigit():
            pincode += str(n)
        if len(pincode) == 4:
            break

    buttons = ButtonMaker()
    BASE_URL = config_dict['BASE_URL']
    if config_dict['WEB_PINCODE']:
        buttons.buildbutton("Select Files", f"{BASE_URL}/app/files/{id_}")
        buttons.sbutton("Pincode", f"btsel pin {gid} {pincode}")
    else:
        buttons.buildbutton("Select Files", f"{BASE_URL}/app/files/{id_}?pin_code={pincode}")
    buttons.sbutton("Done Selecting", f"btsel done {gid} {id_}")
    return buttons.build_menu(2)

def get_progress_bar_string(status):
    completed = status.processed_bytes() / 8
    total = status.size_raw() / 8
    p = 0 if total == 0 else round(completed * 100 / total)
    p = min(max(p, 0), 100)
    cFull = p // 8
    cPart = p % 8 - 1
   # p_str = '■' * cFull
    p_str = '⬤' * cFull
    if cPart >= 0:
        p_str += PROGRESS_INCOMPLETE[cPart]
    p_str += '○' * (PROGRESS_MAX_SIZE - cFull)
    p_str = f" ⠧{p_str}⠹"
    return p_str

def get_readable_message():
    with download_dict_lock:
        msg = ""
        if STATUS_LIMIT := config_dict['STATUS_LIMIT']:
            tasks = len(download_dict)
            globals()['PAGES'] = ceil(tasks/STATUS_LIMIT)
            if PAGE_NO > PAGES and PAGES != 0:
                globals()['COUNT'] -= STATUS_LIMIT
                globals()['PAGE_NO'] -= 1
        for index, download in enumerate(list(download_dict.values())[COUNT:], start=1):
            msg += f"<b>╭ <a href='{download.message.link}'>{download.status()}</a>: </b>"
            msg += f"<code>{escape(str(download.name()))}</code>"
            if download.status() not in [MirrorStatus.STATUS_SPLITTING, MirrorStatus.STATUS_SEEDING]:
                msg += f"\n<b>├</b>{get_progress_bar_string(download)} {download.progress()}"
                msg += f"\n<b>├ Process:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                msg += f"\n<b>├ Speed:</b> {download.speed()}"
                msg += f"\n<b>├ ETA:</b> {download.eta()}"
                msg += f"<b> | Elapsed: </b>{get_readable_time(time() - download.message.date.timestamp())}"
                msg += f"\n<b>├ Engine :</b> {download.eng()}"
                
                if hasattr(download, 'seeders_num'):
                    try:
                        msg += f"\n<b>├ Seeders:</b> {download.seeders_num()} | <b>Leechers:</b> {download.leechers_num()}"
                    except:
                        pass
            elif download.status() == MirrorStatus.STATUS_SEEDING:
                    msg += f"\n<b>├ Size: </b>{download.size()}"
                    msg += f"\n<b>├ Engine:</b> <code>qBittorrent v4.4.2</code>"
                    msg += f"\n<b>├ Speed: </b>{download.upload_speed()}"
                    msg += f"\n<b>├ Uploaded: </b>{download.uploaded_bytes()}"
                    msg += f"\n<b>├ Ratio: </b>{download.ratio()}"
                    msg += f" | <b> Time: </b>{download.seeding_time()}"
                    msg += f"\n<b>├ Elapsed: </b>{get_readable_time(time() - download.message.date.timestamp())}"
                    msg += f"\n<b>╰ </b><code>/{BotCommands.CancelMirror} {download.gid()}</code>"
            else:
                msg += f"\n<b>╰ Size: </b>{download.size()}"
            msg += f'\n<b>├ User:</b> ️<code>{download.message.from_user.first_name}</code> | <b>Id:</b> <code>{download.message.from_user.id}</code>'
            msg += f"\n<b>╰ Cancel: </b><code>/{BotCommands.CancelMirror} {download.gid()}</code>"
            msg += f"\n<b>_________________________________</b>"
            msg += "\n\n"
            if index == STATUS_LIMIT:
                break
        if len(msg) == 0:
            return None, None
        dl_speed = 0
        up_speed = 0
        for download in list(download_dict.values()):
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                spd = download.speed()
                if 'K' in spd:
                    dl_speed += float(spd.split('K')[0]) * 1024
                elif 'M' in spd:
                    dl_speed += float(spd.split('M')[0]) * 1048576
            elif download.status() == MirrorStatus.STATUS_UPLOADING:
                spd = download.speed()
                if 'KB/s' in spd:
                    up_speed += float(spd.split('K')[0]) * 1024
                elif 'MB/s' in spd:
                    up_speed += float(spd.split('M')[0]) * 1048576
            elif download.status() == MirrorStatus.STATUS_SEEDING:
                spd = download.upload_speed()
                if 'K' in spd:
                    up_speed += float(spd.split('K')[0]) * 1024
                elif 'M' in spd:
                    up_speed += float(spd.split('M')[0]) * 1048576
        bmsg = f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)}"
        bmsg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(time() - botStartTime)}"
        bmsg += f"\n<b>🔻 DL:</b> {get_readable_file_size(dl_speed)}/s | <b>🔺 UL:</b> {get_readable_file_size(up_speed)}/s"
        
        buttons = ButtonMaker()
        buttons.sbutton("Refresh", "status refresh")
        buttons.sbutton("Statistics", str(THREE))
        buttons.sbutton("Close", "status close")
        sbutton = buttons.build_menu(3)
        
        if STATUS_LIMIT and tasks > STATUS_LIMIT:
            msg += f"<b>Page:</b> {PAGE_NO}/{PAGES} | <b>Tasks:</b> {tasks}\n"
            buttons = ButtonMaker()
            buttons.sbutton("⏪Previous", "status pre")
            buttons.sbutton(f"{PAGE_NO}/{PAGES}", str(THREE))
            buttons.sbutton("Next⏩", "status nex")
            buttons.sbutton("Refresh", "status refresh")
            buttons.sbutton("Close", "status close")
            button = buttons.build_menu(3)
            return msg + bmsg, button
        return msg + bmsg, sbutton

def turn(data):
    STATUS_LIMIT = config_dict['STATUS_LIMIT']
    try:
        global COUNT, PAGE_NO
        with download_dict_lock:
            if data[1] == "nex":
                if PAGE_NO == PAGES:
                    COUNT = 0
                    PAGE_NO = 1
                else:
                    COUNT += STATUS_LIMIT
                    PAGE_NO += 1
            elif data[1] == "pre":
                if PAGE_NO == 1:
                    COUNT = STATUS_LIMIT * (PAGES - 1)
                    PAGE_NO = PAGES
                else:
                    COUNT -= STATUS_LIMIT
                    PAGE_NO -= 1
        return True
    except:
        return False

def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result

def is_url(url: str):
    url = re_findall(URL_REGEX, url)
    return bool(url)

def is_gdrive_link(url: str):
    return "drive.google.com" in url

def is_gdtot_link(url: str):
    url = re_match(r'https?://.+\.gdtot\.\S+', url)
    return bool(url)

def is_unified_link(url: str):
    url1 = re.match(r'https?://(anidrive|driveroot|driveflix|indidrive|drivehub)\.in/\S+', url)
    url = re.match(r'https?://(appdrive|driveapp|driveace|gdflix|drivelinks|drivebit|drivesharer|drivepro)\.\S+', url)
    if bool(url1) == True:
        return bool(url1)
    elif bool(url) == True:
        return bool(url)
    else:
        return False

def is_udrive_link(url: str):
    if 'drivehub.ws' in url:
        return 'drivehub.ws' in url
    else:
        url = re.match(r'https?://(hubdrive|katdrive|kolop|drivefire|drivebuzz)\.\S+', url)
        return bool(url)
    
def is_sharer_link(url: str):
    url = re.match(r'https?://(sharer)\.pw/\S+', url)
    return bool(url)

def is_sharedrive_link(url: str):
    url = re.match(r'https?://(sharedrive)\.\S+', url)
    return bool(url)

def is_mega_link(url: str):
    return "mega.nz" in url or "mega.co.nz" in url

def get_mega_link_type(url: str):
    if "folder" in url:
        return "folder"
    elif "file" in url:
        return "file"
    elif "/#F!" in url:
        return "folder"
    return "file"

def is_magnet(url: str):
    magnet = re_findall(MAGNET_REGEX, url)
    return bool(magnet)

def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""

    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper

def get_content_type(link: str) -> str:
    try:
        res = rhead(link, allow_redirects=True, timeout=5, headers = {'user-agent': 'Wget/1.12'})
        content_type = res.headers.get('content-type')
    except:
        try:
            res = urlopen(link, timeout=5)
            info = res.info()
            content_type = info.get_content_type()
        except:
            content_type = None
    return content_type

def update_user_ldata(id_, key, value):
    if id_ in user_data:
        user_data[id_][key] = value
    else:
        user_data[id_] = {key: value}
        
ONE, TWO, THREE = range(3)

def refresh(update, context):
    query = update.callback_query
    query.edit_message_text(text="Refreshing Status...⏳")
    sleep(5)
    update_all_messages()

def close(update, context):
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    bot = context.bot
    query = update.callback_query
    admins = bot.get_chat_member(chat_id, user_id).status in [
        "creator",
        "administrator",
    ] or user_id in [OWNER_ID]
    if admins:
        delete_all_messages()
    else:
        query.answer(text="Only Admins can Close !", show_alert=True)

def pop_up_stats(update, context):
    query = update.callback_query
    stats = bot_sys_stats()
    query.answer(text=stats, show_alert=True)
def bot_sys_stats():
    sent = get_readable_file_size(net_io_counters().bytes_recv)
    recv = get_readable_file_size(net_io_counters().bytes_sent)
    num_active = 0
    num_upload = 0
    num_seeding = 0
    num_zip = 0
    num_unzip = 0
    num_split = 0
    tasks = len(download_dict)
    cpu = cpu_percent()
    mem = virtual_memory().percent
    disk = disk_usage("/").percent
    for stats in list(download_dict.values()):
        if stats.status() == MirrorStatus.STATUS_DOWNLOADING:
            num_active += 1
        if stats.status() == MirrorStatus.STATUS_UPLOADING:
            num_upload += 1
        if stats.status() == MirrorStatus.STATUS_SEEDING:
            num_seeding += 1
        if stats.status() == MirrorStatus.STATUS_ARCHIVING:
            num_zip += 1
        if stats.status() == MirrorStatus.STATUS_EXTRACTING:
            num_unzip += 1
        if stats.status() == MirrorStatus.STATUS_SPLITTING:
            num_split += 1
    return f"""
Made with ❤️ by Ajay

Tasks: {tasks}

CPU: {progress_bar(cpu)} {cpu}%
RAM: {progress_bar(mem)} {mem}%
DISK: {progress_bar(disk)} {disk}%

SENT: {sent} | RECV: {recv}

DLs: {num_active} | ULs: {num_upload} | SEEDING: {num_seeding}
ZIP: {num_zip} | UNZIP: {num_unzip} | SPLIT: {num_split}
"""
    return stats
dispatcher.add_handler(
    CallbackQueryHandler(pop_up_stats, pattern="^" + str(THREE) + "$")
)
