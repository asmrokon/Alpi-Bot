import asyncio
import json
import aiohttp
from html import unescape
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


crunchyroll_rss_link = "https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss"

categories = ["latest news","announcements","news"]

ph_title = "Naoki Urasawa's 20th Century Boys Wins Eisner Award"
ph_description = "Suspense Manga Picks Up Prestigious North American Comics Honor"
ph_content = """Naoki Urasawa's 20th Century Boys has been honored with this year's award for "Best U.S. Edition of International Material - Asia" in North American comic industry's prestigious Eisner Awards.  The series follows Kenji Endo, who abandoned his rock n' roll dreams to run the family liquor store, which he converted to a franchise convenience store and take care of his sister's abandoned daughter, only to find himself drawn into a mystery in which the games he played as a boy are apparently being used to try to take over the world.  The 20th Century Boys manga and its live action adaptations are released in North America by VIZ Media.



Other nominees for this year's "Best U.S. Edition of International Material - Asia"  included Osamu Tezuka's Ayako, Yumi Unita's Bunny Drop, Moto Hagio's A Drunken Dream and Other Stories and Natsume Ono's House of Five Leaves. 

Urasawa was also nominated for Best Writer/Artist, which went to Darwyn Cooke, and 20th Century Boys was also nominated for Best Continuing Series, which went to Rob Guillory's Chew.



Nobuaki Tadano's manga 7 Billion Needles was nominated for Best Adaptation, which went to Eric Shanower and Skottie Young's Marvelous Land of Oz."""

ph_news_url = "https://www.crunchyroll.com/news/latest/2011/7/23/naoki-urasawas-20-century-boys-wins-eisner-award"
ph_image_url = "https://a.storyblok.com/f/178900/200x200/c4696332d1/1f19ab3b88328aeb80d8dba6dd8da9fb1565316727_large.png"


async def get_latest_croll_news_list_from_source():
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



async def get_latest_croll_news_list():
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


async def fetch_latest_news_list():
    namespaces = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "media": "http://search.yahoo.com/mrss/"
                }

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
    
    items = feed.findall(".//item")[:10]
    if items is None:
        return None
                
    news_list = []
    
    for item in items:
        category = str(item.findtext("category",""))
        if category:
            if category.lower() in categories:
                pass
            else:
                continue
        else:
            pass

        title = item.findtext("title",ph_title)

        description = item.findtext("description",ph_description)

        date = item.findtext("pubDate","Sun, 21 Dec 1100 17:00:00 GMT")
        timestamp = get_timestamp(date)
                    

        full_content = unescape(item.findtext("content:encoded", ph_content, namespaces))     
                    
        if len(full_content) > 500:
            content = f"{full_content[:500]}..." 
        else:
            content = full_content

        news_url = item.findtext("link",ph_news_url)

        image_item = item.find("media:thumbnail", namespaces)

        if image_item is not None:
            image_url = image_item.attrib.get("url",ph_image_url)
        else:
            image_url = ph_image_url
                    
        news = {
            "title": title,
            "description": description,
            "content": content,
            "image_url": image_url,
            "news_url": news_url,
            "timestamp": timestamp
                }

        news_list.append(news)
    
    return news_list

        

def update_news_list(news_list):
    with open("last_croll_news.json","w") as f:
        json.dump(news_list,f,indent=4)


def get_seen_news_titles_list():
    title_list = []
    try:
        with open("last_croll_news.json","r") as f:
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
        with open("last_croll_news.json","r") as f:
            news_list = json.load(f)
        if news_list:
            for news in news_list:                
                seen_list.append(news)
            return seen_list

        else:
            return []
    except Exception as e:  # noqa: F841
        return []
    


def get_timestamp(date):
    dt = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")

    dt = dt.replace(tzinfo=timezone.utc)
    timestamp = int(dt.timestamp())

    return timestamp
