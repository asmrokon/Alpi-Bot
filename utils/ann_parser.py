import asyncio
import json
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

rss_link = "https://www.animenewsnetwork.com/news/atom.xml?ann-edition=w"


async def get_latest_ann_news_list_from_source():
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

    return bool(is_new)



def get_timestamp(date):
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    return int(dt.timestamp())



async def fetch_latest_news_list():
    namespaces = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "media": "http://search.yahoo.com/mrss/",
            "atom": "http://www.w3.org/2005/Atom"
                }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_link) as html:
                text = await html.text()
    
            try:
                feed = ET.fromstring(text)
            except ET.ParseError:
                print("Invalid RSS XML")
                return None 
            
            entries = feed.findall(".//atom:entry",namespaces=namespaces)[:25]    
            if not entries:
                return None  
            news_list = []

            for number, entry in enumerate(entries,start=1):

                title = entry.findtext("atom:title","Title", namespaces=namespaces)
                date = entry.findtext("atom:published","2026-09-09T10:01:22Z",namespaces=namespaces)
                timestamp = get_timestamp(date)
                description_raw = entry.findtext("atom:summary","Description", namespaces=namespaces)
                description = BeautifulSoup(unescape(description_raw), "html.parser").get_text()
                news_url = entry.findtext("atom:id","https://www.animenewsnetwork.com/",namespaces=namespaces)

                ctg = entry.find("atom:category",namespaces=namespaces)
                category = (
                            ctg.get("term")
                            if ctg is not None
                            else "Anime"
                        )
                
                if category.lower() not in {"anime", "manga"}:
                    continue

                news = {
                        "title": title,
                        "category":category,
                        "description": description,                        
                        "news_url": news_url,
                        "timestamp": timestamp,                
                        }
                        
                news_list.append(news)



            image_urls = await asyncio.gather(
                *(
                    fetch_image_url(session, news["news_url"])
                    for news in news_list
                )
            )

            # Attach images to their corresponding articles
            for news, image_url in zip(news_list, image_urls, strict=True):
                news["image_url"] = image_url
            
            return news_list        
    

    except aiohttp.ClientConnectorDNSError:
        print("DNS resolution failed")
        return None
    except aiohttp.ClientConnectionError:
        print("Connection failed")
        return None
    except asyncio.TimeoutError:
        print("Request timed out")
        return None



async def fetch_image(image_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()

                suffix = Path(image_url).suffix or ".jpg"

                with tempfile.NamedTemporaryFile(
                    suffix=suffix,
                    delete=False
                ) as temp:
                    temp.write(await response.read())
                    return Path(temp.name)

    except aiohttp.ClientError:
        print(f"Failed to download image: {image_url}")
        return None

    except asyncio.TimeoutError:
        print(f"Image download timed out: {image_url}")
        return None



async def fetch_image_url(session, news_url):
    placeholder = "https://i.ytimg.com/vi/zuk_UJIRnik/maxresdefault.jpg"

    try:
        async with session.get(news_url) as response:
            html = await response.text()

    except aiohttp.ClientConnectorDNSError:
        print("DNS resolution failed")
        return placeholder

    except aiohttp.ClientConnectionError:
        print("Connection failed")
        return placeholder

    except asyncio.TimeoutError:
        print("Request timed out")
        return placeholder

    soup = BeautifulSoup(html, "html.parser")

    image = soup.find("link", rel="image_src")

    if not image:
        print(f"Image not found: {news_url}")
        return placeholder

    return image.get("href")





async def get_latest_ann_news_list():
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
    with open("last_ann_news.json","w") as f:
        json.dump(news_list,f,indent=4)


def get_seen_news_titles_list():
    title_list = []
    try:
        with open("last_ann_news.json","r") as f:
            news_list = json.load(f)
        if news_list:
            for news in news_list:                
                title_list.append(news["title"])
            return title_list

        else:
            return []
    except Exception as e:  # noqa: BLE001, F841
        return []



def get_seen_news_list():
    seen_list = []
    try:
        with open("last_ann_news.json","r") as f:
            news_list = json.load(f)
        if news_list:
            for news in news_list:                
                seen_list.append(news)
            return seen_list

        else:
            return []
    except Exception as e:  # noqa: BLE001, F841
        return []




