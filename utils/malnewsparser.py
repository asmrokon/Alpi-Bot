import asyncio
import json
import aiohttp
from html import unescape
import xml.etree.ElementTree as ET


rss_link = "https://myanimelist.net/rss/news.xml"


async def get_latest_mal_news():
    news = await fetch_latest_news()
    last_news_title = get_last_news_title()

    if news and (news["title"] != last_news_title):
        update_news(news)

        return news
    else:
        return ""


async def fetch_latest_news():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_link) as html:
                text = await html.text()
    except aiohttp.ClientConnectorDNSError:
        print("DNS resolution failed")
        return None
    except aiohttp.ClientConnectionError:
        print("Connection failed")
        return None
    except asyncio.TimeoutError:
        print("Request timed out")
        return None
    
    try:
        feed = ET.fromstring(text)
    except ET.ParseError:
        print("Invalid RSS XML")
        return None
    
    item = feed.find(".//item")
    if item is None:
        return None
                
    # category = str(item.findtext("category",""))

    title = item.findtext("title","")

    description = unescape(item.findtext("description",""))
                
    namespaces = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "media": "http://search.yahoo.com/mrss/"
                }

                   


    news_url = item.findtext("link","https://myanimelist.net/news")

    image_url = item.findtext("media:thumbnail","",namespaces)

    news = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "news_url": news_url
            }


    return news



def update_news(news):
    with open("last_news.json","r") as f:
        data = json.load(f)
        data["mal"] = news
    with open("last_news.json","w") as f:
        json.dump(data,f,indent=4)


def get_last_news_title():
    try:
        with open("last_news.json","r") as f:
            data = json.load(f)
        if data and data["mal"]["title"]:
            return data["mal"]["title"]
        else:
            return "aa"
    except Exception as e:
        return e


