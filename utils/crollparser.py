import asyncio
import json
import aiohttp
from html import unescape
import xml.etree.ElementTree as ET


crunchyroll_rss_link = "https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss"

categories = ["latest news","announcements","news"]

async def get_latest_croll_news():
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
            async with session.get(crunchyroll_rss_link) as html:
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
                
    category = str(item.findtext("category",""))

    title = item.findtext("title","")

    description = item.findtext("description","")
                
    namespaces = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "media": "http://search.yahoo.com/mrss/"
                }

    full_content = unescape(item.findtext("content:encoded", "", namespaces))     
                
    if len(full_content) > 500:
        content = f"{full_content[:500]}..." 
    else:
        content = full_content

    news_url = item.findtext("link","https://www.crunchyroll.com/news")

    image_item = item.find("media:thumbnail", namespaces)

    if image_item is not None:
        image_url = image_item.attrib.get("url","")
    else:
        image_url = ""
                
    news = {
        "title": title,
        "description": description,
        "content": content,
        "image_url": image_url,
        "news_url": news_url
            }

    if category:
        if category.lower() in categories:
            return news
        else:
            return ""
    else:
        return news
        

def update_news(news):
    with open("last_news.json","r") as f:
        data = json.load(f)
        data["croll"] = news
    with open("last_news.json","w") as f:
        json.dump(data,f,indent=4)


def get_last_news_title():
    with open("last_news.json","r") as f:
        data = json.load(f)
    if data and data["croll"]["title"]:
        return data["croll"]["title"]
    else:
        return ""
    

