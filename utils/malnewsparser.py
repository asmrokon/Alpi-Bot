import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape

import aiohttp

rss_link = "https://myanimelist.net/rss/news.xml"


async def get_latest_mal_news_list_from_source():
    fetched_news_list = await fetch_latest_news_list()
    seen_news = get_seen_news_list()
    seen_news_titles = get_seen_news_titles_list()

    if fetched_news_list and is_new_news(seen_news_titles,fetched_news_list):        
        return {"new_news": True,"news": fetched_news_list}
    elif fetched_news_list:
        return {"new_news": False,"news": fetched_news_list}
    else:
        return {"new_news": False,"news": seen_news}



def is_new_news(seen_news_titles,latest_news_list):
    is_new = []
    for news in latest_news_list:
        if news["title"] not in seen_news_titles:
            is_new.append(news)                    

    if is_new:
        return True
    else:
        False



def get_timestamp(date):
    dt = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
    timestamp = int(dt.timestamp())

    return timestamp



async def fetch_latest_news_list():
    namespaces = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "media": "http://search.yahoo.com/mrss/"
                }

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
    
    items = feed.findall(".//item")[:10]
    if items is None:
        return None
    
    news_list = []

    for number, item in enumerate(items,start=1):

        title = item.findtext("title","Title")
        date = item.findtext("pubDate","Sun, 20 Dec 1456 08:24:44 -0800")
        timestamp = get_timestamp(date)
        description = unescape(item.findtext("description","Description"))
        news_url = item.findtext("link","https://myanimelist.net/news")
        image_url = item.findtext("media:thumbnail","",namespaces)

        news = {
                "title": title,
                "description": description,
                "image_url": image_url,
                "news_url": news_url,
                "timestamp": timestamp
                }
                
        news_list.append(news)
        
    return news_list
    # category = str(item.findtext("category",""))


async def get_latest_mal_news_list():
    latest_news_list = []
    fetched_news_list = await fetch_latest_news_list()
    last_news_titles = get_seen_news_titles_list()

    if fetched_news_list:
        if last_news_titles:
            for news in fetched_news_list:
                if news["title"] not in last_news_titles:
                    latest_news_list.append(news)        
            update_news_list(fetched_news_list)
            return latest_news_list

        else:
            update_news_list(fetched_news_list)
            
            return fetched_news_list
    else:
        return []
    
    




def update_news_list(news_list):
    with open("last_mal_news.json","w") as f:
        json.dump(news_list,f,indent=4)


def get_seen_news_titles_list():
    title_list = []
    try:
        with open("last_mal_news.json","r") as f:
            news_list = json.load(f)
        if news_list:
            for news in news_list:                
                title_list.append(news["title"])
            return title_list

        else:
            return []
    except Exception as e:  # noqa: F841
        return []



def get_seen_news_list():
    seen_list = []
    try:
        with open("last_mal_news.json","r") as f:
            news_list = json.load(f)
        if news_list:
            for news in news_list:                
                seen_list.append(news)
            return seen_list

        else:
            return []
    except Exception as e:  # noqa: F841
        return []


# asyncio.run(get_latest_mal_news_list())

# get_last_news_titles_list()