# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Helper Module containing various sites direct links generators. This module is copied and modified as per need
from https://github.com/AvinashReddy3108/PaperplaneExtended . I hereby take no credit of the following code other
than the modifications. See https://github.com/AvinashReddy3108/PaperplaneExtended/commits/master/userbot/modules/direct_links.py
for original authorship. """

from requests import get as rget, head as rhead, post as rpost, Session as rsession
from re import findall as re_findall, sub as re_sub, match as re_match, search as re_search
from urllib.parse import urlparse, unquote, parse_qs
from json import loads as jsonloads
from lk21 import Bypass
from base64 import b64decode
from cfscrape import create_scraper
from bs4 import BeautifulSoup
from base64 import standard_b64encode
from time import sleep
import requests
import re
import os
import base64
import cloudscraper
from lxml import etree

from bot import LOGGER, config_dict
from bot.helper.ext_utils.bot_utils import *
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException

fmed_list = ['fembed.net', 'fembed.com', 'femax20.com', 'fcdn.stream', 'feurl.com', 'layarkacaxxi.icu',
             'naniplay.nanime.in', 'naniplay.nanime.biz', 'naniplay.com', 'mm9842.com']


def direct_link_generator(link: str):
    """ direct links generator """
    if 'youtube.com' in link or 'youtu.be' in link:
        raise DirectDownloadLinkException("ERROR: Use ytdl cmds for Youtube links")
    elif 'yadi.sk' in link or 'disk.yandex.com' in link:
        return yandex_disk(link)
    elif 'mediafire.com' in link:
        return mediafire(link)
    elif 'uptobox.com' in link:
        return uptobox(link)
    elif 'osdn.net' in link:
        return osdn(link)
    elif 'github.com' in link:
        return github(link)
    elif 'hxfile.co' in link:
        return hxfile(link)
    elif 'anonfiles.com' in link:
        return anonfiles(link)
    elif 'letsupload.io' in link:
        return letsupload(link)
    elif '1drv.ms' in link:
        return onedrive(link)
    elif 'pixeldrain.com' in link:
        return pixeldrain(link)
    elif 'antfiles.com' in link:
        return antfiles(link)
    elif 'streamtape.com' in link:
        return streamtape(link)
    elif 'bayfiles.com' in link:
        return anonfiles(link)
    elif 'racaty.net' in link:
        return racaty(link)
    elif '1fichier.com' in link:
        return fichier(link)
    elif 'solidfiles.com' in link:
        return solidfiles(link)
    elif 'krakenfiles.com' in link:
        return krakenfiles(link)
    elif 'upload.ee' in link:
        return uploadee(link)
    elif is_gdtot_link(link):
        return gdtot(link)
    elif is_unified_link(link):
        return unified(link)
    elif is_udrive_link(link):
        return udrive(link)
    elif is_sharer_link(link):
        return sharer_pw_dl(link)
    elif is_sharedrive_link(link):
        return shareDrive(link)
    elif any(x in link for x in fmed_list):
        return fembed(link)
    elif any(x in link for x in ['sbembed.com', 'watchsb.com', 'streamsb.net', 'sbplay.org']):
        return sbembed(link)
    else:
        raise DirectDownloadLinkException(f'No Direct link function found for {link}')

def yandex_disk(url: str) -> str:
    """ Yandex.Disk direct link generator
    Based on https://github.com/wldhx/yadisk-direct """
    try:
        link = re_findall(r'\b(https?://(yadi.sk|disk.yandex.com)\S+)', url)[0][0]
    except IndexError:
        return "No Yandex.Disk links found\n"
    api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}'
    try:
        return rget(api.format(link)).json()['href']
    except KeyError:
        raise DirectDownloadLinkException("ERROR: File not found/Download limit reached")

def uptobox(url: str) -> str:
    """ Uptobox direct link generator
    based on https://github.com/jovanzers/WinTenCermin and https://github.com/sinoobie/noobie-mirror """
    try:
        link = re_findall(r'\bhttps?://.*uptobox\.com\S+', url)[0]
    except IndexError:
        raise DirectDownloadLinkException("No Uptobox links found")
    if UPTOBOX_TOKEN := config_dict['UPTOBOX_TOKEN']:
        LOGGER.error('UPTOBOX_TOKEN not provided!')
        dl_url = link
    else:
        try:
            link = re_findall(r'\bhttp?://.*uptobox\.com/dl\S+', url)[0]
            dl_url = link
        except:
            file_id = re_findall(r'\bhttps?://.*uptobox\.com/(\w+)', url)[0]
            file_link = f'https://uptobox.com/api/link?token={UPTOBOX_TOKEN}&file_code={file_id}'
            req = rget(file_link)
            result = req.json()
            if result['message'].lower() == 'success':
                dl_url = result['data']['dlLink']
            elif result['message'].lower() == 'waiting needed':
                waiting_time = result["data"]["waiting"] + 1
                waiting_token = result["data"]["waitingToken"]
                sleep(waiting_time)
                req2 = rget(f"{file_link}&waitingToken={waiting_token}")
                result2 = req2.json()
                dl_url = result2['data']['dlLink']
            elif result['message'].lower() == 'you need to wait before requesting a new download link':
                cooldown = divmod(result['data']['waiting'], 60)
                raise DirectDownloadLinkException(f"ERROR: Uptobox is being limited please wait {cooldown[0]} min {cooldown[1]} sec.")
            else:
                LOGGER.info(f"UPTOBOX_ERROR: {result}")
                raise DirectDownloadLinkException(f"ERROR: {result['message']}")
    return dl_url

def mediafire(url: str) -> str:
    """ MediaFire direct link generator """
    try:
        link = re_findall(r'\bhttps?://.*mediafire\.com\S+', url)[0]
    except IndexError:
        raise DirectDownloadLinkException("No MediaFire links found")
    page = BeautifulSoup(rget(link).content, 'lxml')
    info = page.find('a', {'aria-label': 'Download file'})
    return info.get('href')

def osdn(url: str) -> str:
    """ OSDN direct link generator """
    osdn_link = 'https://osdn.net'
    try:
        link = re_findall(r'\bhttps?://.*osdn\.net\S+', url)[0]
    except IndexError:
        raise DirectDownloadLinkException("No OSDN links found")
    page = BeautifulSoup(
        rget(link, allow_redirects=True).content, 'lxml')
    info = page.find('a', {'class': 'mirror_link'})
    link = unquote(osdn_link + info['href'])
    mirrors = page.find('form', {'id': 'mirror-select-form'}).findAll('tr')
    urls = []
    for data in mirrors[1:]:
        mirror = data.find('input')['value']
        urls.append(re_sub(r'm=(.*)&f', f'm={mirror}&f', link))
    return urls[0]

def github(url: str) -> str:
    """ GitHub direct links generator """
    try:
        re_findall(r'\bhttps?://.*github\.com.*releases\S+', url)[0]
    except IndexError:
        raise DirectDownloadLinkException("No GitHub Releases links found")
    download = rget(url, stream=True, allow_redirects=False)
    try:
        return download.headers["location"]
    except KeyError:
        raise DirectDownloadLinkException("ERROR: Can't extract the link")

def hxfile(url: str) -> str:
    """ Hxfile direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    return Bypass().bypass_filesIm(url)

def anonfiles(url: str) -> str:
    """ Anonfiles direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    return Bypass().bypass_anonfiles(url)

def letsupload(url: str) -> str:
    """ Letsupload direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    try:
        link = re_findall(r'\bhttps?://.*letsupload\.io\S+', url)[0]
    except IndexError:
        raise DirectDownloadLinkException("No Letsupload links found\n")
    return Bypass().bypass_url(link)

def fembed(link: str) -> str:
    """ Fembed direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    dl_url= Bypass().bypass_fembed(link)
    count = len(dl_url)
    lst_link = [dl_url[i] for i in dl_url]
    return lst_link[count-1]

def sbembed(link: str) -> str:
    """ Sbembed direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    dl_url= Bypass().bypass_sbembed(link)
    count = len(dl_url)
    lst_link = [dl_url[i] for i in dl_url]
    return lst_link[count-1]

def onedrive(link: str) -> str:
    """ Onedrive direct link generator
    Based on https://github.com/UsergeTeam/Userge """
    link_without_query = urlparse(link)._replace(query=None).geturl()
    direct_link_encoded = str(standard_b64encode(bytes(link_without_query, "utf-8")), "utf-8")
    direct_link1 = f"https://api.onedrive.com/v1.0/shares/u!{direct_link_encoded}/root/content"
    resp = rhead(direct_link1)
    if resp.status_code != 302:
        raise DirectDownloadLinkException("ERROR: Unauthorized link, the link may be private")
    return resp.next.url

def pixeldrain(url: str) -> str:
    """ Based on https://github.com/yash-dk/TorToolkit-Telegram """
    url = url.strip("/ ")
    file_id = url.split("/")[-1]
    if url.split("/")[-2] == "l":
        info_link = f"https://pixeldrain.com/api/list/{file_id}"
        dl_link = f"https://pixeldrain.com/api/list/{file_id}/zip"
    else:
        info_link = f"https://pixeldrain.com/api/file/{file_id}/info"
        dl_link = f"https://pixeldrain.com/api/file/{file_id}"
    resp = rget(info_link).json()
    if resp["success"]:
        return dl_link
    else:
        raise DirectDownloadLinkException(f"ERROR: Cant't download due {resp['message']}.")

def antfiles(url: str) -> str:
    """ Antfiles direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    return Bypass().bypass_antfiles(url)

def streamtape(url: str) -> str:
    """ Streamtape direct link generator
    Based on https://github.com/zevtyardt/lk21
    """
    return Bypass().bypass_streamtape(url)

def racaty(url: str) -> str:
    """ Racaty direct link generator
    based on https://github.com/SlamDevs/slam-mirrorbot"""
    dl_url = ''
    try:
        re_findall(r'\bhttps?://.*racaty\.net\S+', url)[0]
    except IndexError:
        raise DirectDownloadLinkException("No Racaty links found")
    scraper = create_scraper()
    r = scraper.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    op = soup.find("input", {"name": "op"})["value"]
    ids = soup.find("input", {"name": "id"})["value"]
    rapost = scraper.post(url, data = {"op": op, "id": ids})
    rsoup = BeautifulSoup(rapost.text, "lxml")
    dl_url = rsoup.find("a", {"id": "uniqueExpirylink"})["href"].replace(" ", "%20")
    return dl_url

def fichier(link: str) -> str:
    """ 1Fichier direct link generator
    Based on https://github.com/Maujar
    """
    regex = r"^([http:\/\/|https:\/\/]+)?.*1fichier\.com\/\?.+"
    gan = re_match(regex, link)
    if not gan:
      raise DirectDownloadLinkException("ERROR: The link you entered is wrong!")
    if "::" in link:
      pswd = link.split("::")[-1]
      url = link.split("::")[-2]
    else:
      pswd = None
      url = link
    try:
      if pswd is None:
        req = rpost(url)
      else:
        pw = {"pass": pswd}
        req = rpost(url, data=pw)
    except:
      raise DirectDownloadLinkException("ERROR: Unable to reach 1fichier server!")
    if req.status_code == 404:
      raise DirectDownloadLinkException("ERROR: File not found/The link you entered is wrong!")
    soup = BeautifulSoup(req.content, 'lxml')
    if soup.find("a", {"class": "ok btn-general btn-orange"}) is not None:
        dl_url = soup.find("a", {"class": "ok btn-general btn-orange"})["href"]
        if dl_url is None:
          raise DirectDownloadLinkException("ERROR: Unable to generate Direct Link 1fichier!")
        else:
          return dl_url
    elif len(soup.find_all("div", {"class": "ct_warn"})) == 3:
        str_2 = soup.find_all("div", {"class": "ct_warn"})[-1]
        if "you must wait" in str(str_2).lower():
            numbers = [int(word) for word in str(str_2).split() if word.isdigit()]
            if not numbers:
                raise DirectDownloadLinkException("ERROR: 1fichier is on a limit. Please wait a few minutes/hour.")
            else:
                raise DirectDownloadLinkException(f"ERROR: 1fichier is on a limit. Please wait {numbers[0]} minute.")
        elif "protect access" in str(str_2).lower():
          raise DirectDownloadLinkException(f"ERROR: This link requires a password!\n\n<b>This link requires a password!</b>\n- Insert sign <b>::</b> after the link and write the password after the sign.\n\n<b>Example:</b> https://1fichier.com/?smmtd8twfpm66awbqz04::love you\n\n* No spaces between the signs <b>::</b>\n* For the password, you can use a space!")
        else:
            print(str_2)
            raise DirectDownloadLinkException("ERROR: Failed to generate Direct Link from 1fichier!")
    elif len(soup.find_all("div", {"class": "ct_warn"})) == 4:
        str_1 = soup.find_all("div", {"class": "ct_warn"})[-2]
        str_3 = soup.find_all("div", {"class": "ct_warn"})[-1]
        if "you must wait" in str(str_1).lower():
            numbers = [int(word) for word in str(str_1).split() if word.isdigit()]
            if not numbers:
                raise DirectDownloadLinkException("ERROR: 1fichier is on a limit. Please wait a few minutes/hour.")
            else:
                raise DirectDownloadLinkException(f"ERROR: 1fichier is on a limit. Please wait {numbers[0]} minute.")
        elif "bad password" in str(str_3).lower():
          raise DirectDownloadLinkException("ERROR: The password you entered is wrong!")
        else:
            raise DirectDownloadLinkException("ERROR: Error trying to generate Direct Link from 1fichier!")
    else:
        raise DirectDownloadLinkException("ERROR: Error trying to generate Direct Link from 1fichier!")

def solidfiles(url: str) -> str:
    """ Solidfiles direct link generator
    Based on https://github.com/Xonshiz/SolidFiles-Downloader
    By https://github.com/Jusidama18 """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
    }
    pageSource = rget(url, headers = headers).text
    mainOptions = str(re_search(r'viewerOptions\'\,\ (.*?)\)\;', pageSource).group(1))
    return jsonloads(mainOptions)["downloadUrl"]

def krakenfiles(page_link: str) -> str:
    """ krakenfiles direct link generator
    Based on https://github.com/tha23rd/py-kraken
    By https://github.com/junedkh """
    page_resp = rsession().get(page_link)
    soup = BeautifulSoup(page_resp.text, "lxml")
    try:
        token = soup.find("input", id="dl-token")["value"]
    except:
        raise DirectDownloadLinkException(f"Page link is wrong: {page_link}")

    hashes = [
        item["data-file-hash"]
        for item in soup.find_all("div", attrs={"data-file-hash": True})
    ]
    if not hashes:
        raise DirectDownloadLinkException(f"ERROR: Hash not found for : {page_link}")

    dl_hash = hashes[0]

    payload = f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name="token"\r\n\r\n{token}\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--'
    headers = {
        "content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        "cache-control": "no-cache",
        "hash": dl_hash,
    }

    dl_link_resp = rsession().post(
        f"https://krakenfiles.com/download/{hash}", data=payload, headers=headers)

    dl_link_json = dl_link_resp.json()

    if "url" in dl_link_json:
        return dl_link_json["url"]
    else:
        raise DirectDownloadLinkException(f"ERROR: Failed to acquire download URL from kraken for : {page_link}")

def uploadee(url: str) -> str:
    """ uploadee direct link generator
    By https://github.com/iron-heart-x"""
    try:
        soup = BeautifulSoup(rget(url).content, 'lxml')
        sa = soup.find('a', attrs={'id':'d_l'})
        return sa['href']
    except:
        raise DirectDownloadLinkException(f"ERROR: Failed to acquire download URL from upload.ee for : {url}")


def gdtot(url: str) -> str:
    if config_dict['GDTOT_CRYPT'] is None:
        raise DirectDownloadLinkException("GDTOT_CRYPT env var not provided")
    client = requests.Session()
    client.cookies.update({"crypt": config_dict['GDTOT_CRYPT']})
    res = client.get(url)
    base_url = re.match('^.+?[^\/:](?=[?\/]|$\n)', url).group(0)
    res = client.get(f"{base_url}/dld?id={url.split('/')[-1]}")
    url = re.findall(r'URL=(.*?)"', res.text)[0]
    info = {}
    info["error"] = False
    params = parse_qs(urlparse(url).query)
    if "gd" not in params or not params["gd"] or params["gd"][0] == "false":
        info["error"] = True
        if "msgx" in params:
            info["message"] = params["msgx"][0]
        else:
            info["message"] = "Invalid link"
    else:
        decoded_id = base64.b64decode(str(params["gd"][0])).decode("utf-8")
        drive_link = f"https://drive.google.com/open?id={decoded_id}"
        info["gdrive_link"] = drive_link
    if not info["error"]:
        return info["gdrive_link"]
    else:
        raise DirectDownloadLinkException(f"{info['message']}")


account = {"email": config_dict['UNIFIED_EMAIL'], "passwd": config_dict['UNIFIED_PASS']}


def account_login(client, url, email, password):
    data = {"email": email, "password": password}
    client.post(f"https://{urlparse(url).netloc}/login", data=data)


def gen_payload(data, boundary=f'{"-"*6}_'):
    data_string = ""
    for item in data:
        data_string += f"{boundary}\r\n"
        data_string += (
            f'Content-Disposition: form-data; name="{item}"\r\n\r\n{data[item]}\r\n'
        )
    data_string += f"{boundary}--\r\n"
    return data_string


def parse_infou(data):
    info = re.findall(">(.*?)<\/li>", data)
    info_parsed = {}
    for item in info:
        kv = [s.strip() for s in item.split(":", maxsplit=1)]
        info_parsed[kv[0].lower()] = kv[1]
    return info_parsed


def unified(url: str) -> str:
    if (config_dict['UNIFIED_EMAIL'] or config_dict['UNIFIED_PASS']) is None:
        raise DirectDownloadLinkException(
            "UNIFIED_EMAIL and UNIFIED_PASS env vars not provided"
        )
    client = cloudscraper.create_scraper(delay=10, browser='chrome')
    client.headers.update(
        {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
        }
    )

    account_login(client, url, account["email"], account["passwd"])

    res = client.get(url)
    key = re.findall('"key",\s+"(.*?)"', res.text)[0]

    ddl_btn = etree.HTML(res.content).xpath("//button[@id='drc']")

    info_parsed = parse_infou(res.text)
    info_parsed["error"] = False
    info_parsed["link_type"] = "login"  # direct/login

    headers = {
        "Content-Type": f"multipart/form-data; boundary={'-'*4}_",
    }

    data = {"type": 1, "key": key, "action": "original"}

    if len(ddl_btn):
        info_parsed["link_type"] = "direct"
        data["action"] = "direct"

    while data["type"] <= 3:
        try:
            response = client.post(url, data=gen_payload(data), headers=headers).json()
            break
        except:
            data["type"] += 1

    if "url" in response:
        info_parsed["gdrive_link"] = response["url"]
    elif "error" in response and response["error"]:
        info_parsed["error"] = True
        info_parsed["error_message"] = response["message"]
    else:
        info_parsed["error"] = True
        info_parsed["error_message"] = "Something went wrong :("

    if info_parsed["error"]:
        raise DirectDownloadLinkException(f"ERROR! {info_parsed['error_message']}")

    if urlparse(url).netloc == "appdrive.info":
        flink = info_parsed["gdrive_link"]
        return flink

    elif urlparse(url).netloc == "driveapp.in":
        res = client.get(info_parsed["gdrive_link"])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn')]/@href")[
            0
        ]
        flink = drive_link
        return flink

    else:
        res = client.get(info_parsed["gdrive_link"])
        drive_link = etree.HTML(res.content).xpath(
            "//a[contains(@class,'btn btn-primary')]/@href"
        )[0]
        flink = drive_link
        return flink
    

def parse_info(res, url):
    info_parsed = {}
    if 'drivebuzz' in url:
        info_chunks = re.findall('<td\salign="right">(.*?)<\/td>', res.text)
    else:
        info_chunks = re.findall(">(.*?)<\/td>", res.text)
    for i in range(0, len(info_chunks), 2):
        info_parsed[info_chunks[i]] = info_chunks[i + 1]
    return info_parsed


def udrive(url: str) -> str:
    if 'katdrive' or 'hubdrive' in url:
        client = requests.Session()
    else:
        client = cloudscraper.create_scraper(delay=10, browser='chrome')
        
    if "hubdrive" in url:
        if "hubdrive.in" in url:
            url = url.replace(".in",".pro")
        client.cookies.update({"crypt": config_dict['HUBDRIVE_CRYPT']})
    if "drivehub" in url:
        client.cookies.update({"crypt": config_dict['KATDRIVE_CRYPT']})
    if "katdrive" in url:
        client.cookies.update({"crypt": config_dict['KATDRIVE_CRYPT']})
    if "kolop" in url:
        client.cookies.update({"crypt": config_dict['KATDRIVE_CRYPT']})
    if "drivefire" in url:
        client.cookies.update({"crypt": config_dict['DRIVEFIRE_CRYPT']})
    if "drivebuzz" in url:
        client.cookies.update({"crypt": config_dict['DRIVEFIRE_CRYPT']})
    res = client.get(url)
    info_parsed = parse_info(res, url)
    info_parsed["error"] = False

    up = urlparse(url)
    req_url = f"{up.scheme}://{up.netloc}/ajax.php?ajax=download"

    file_id = url.split("/")[-1]

    data = {"id": file_id}

    headers = {"x-requested-with": "XMLHttpRequest"}

    try:
        res = client.post(req_url, headers=headers, data=data).json()["file"]
    except:
        raise DirectDownloadLinkException(
            "ERROR! File Not Found or User rate exceeded !!"
        )

    if 'drivefire' in url:
        decoded_id = res.rsplit('/', 1)[-1]
        flink = f"https://drive.google.com/file/d/{decoded_id}"
        return flink
    elif 'drivehub' in url:
        gd_id = res.rsplit("=", 1)[-1]
        flink = f"https://drive.google.com/open?id={gd_id}"
        return flink
    elif 'drivebuzz' in url:
        gd_id = res.rsplit("=", 1)[-1]
        flink = f"https://drive.google.com/open?id={gd_id}"
        return flink
    else:
        gd_id = re.findall('gd=(.*)', res, re.DOTALL)[0]

    info_parsed["gdrive_url"] = f"https://drive.google.com/open?id={gd_id}"
    info_parsed["src_url"] = url
    flink = info_parsed['gdrive_url']

    return flink
    

def sharer_pw_dl(url: str)-> str:
    
    client = cloudscraper.create_scraper(delay=10, browser='chrome')
    client.cookies["XSRF-TOKEN"] = config_dict['XSRF_TOKEN']
    client.cookies["laravel_session"] = config_dict['laravel_session']
    
    res = client.get(url)
    token = re.findall("_token\s=\s'(.*?)'", res.text, re.DOTALL)[0]
    data = { '_token': token, 'nl' :1}
    headers={ 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'x-requested-with': 'XMLHttpRequest'}

    try:
        response = client.post(url+'/dl', headers=headers, data=data).json()
        drive_link = response
        return drive_link['url']
    
    except:
        if drive_link["message"] == "OK":
            raise DirectDownloadLinkException("Something went wrong. Could not generate GDrive URL for your Sharer Link")
        else:
            finalMsg = BeautifulSoup(drive_link["message"], "lxml").text
            raise DirectDownloadLinkException(finalMsg)
        
def shareDrive(url,directLogin=True):

    successMsgs = ['success', 'Success', 'SUCCESS']

    scrapper = requests.Session()

    #retrieving session PHPSESSID
    cook = scrapper.get(url)
    cookies = cook.cookies.get_dict()
    config_dict['PHPSESSID'] = cookies['PHPSESSID']

    headers = {
        'authority' : urlparse(url).netloc,
        'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin' : f'https://{urlparse(url).netloc}/',
        'referer' : url,
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.35',
        'X-Requested-With	' : 'XMLHttpRequest'
    }

    if directLogin==True:
        cookies = {
            'PHPSESSID' : config_dict['PHPSESSID']
        }

        data = {
            'id' : url.rsplit('/',1)[1],
            'key' : 'direct'
        }
    else:
        cookies = {
            'PHPSESSID' : config_dict['PHPSESSID'],
            'PHPCKS' : config_dict['SHAREDRIVE_PHPCKS']
        }

        data = {
            'id' : url.rsplit('/',1)[1],
            'key' : 'original'
        }
    
    resp = scrapper.post(f'https://{urlparse(url).netloc}/post', headers=headers, data=data, cookies=cookies)
    toJson = resp.json()

    if directLogin==True:
        if toJson['message'] in successMsgs:
            driveUrl = toJson['redirect']
            return driveUrl
        else:
            shareDrive(url,directLogin=False)
    else:
        if toJson['message'] in successMsgs:
            driveUrl = toJson['redirect']
            return driveUrl
        else:
            raise DirectDownloadLinkException("ERROR! File Not Found or User rate exceeded !!")
