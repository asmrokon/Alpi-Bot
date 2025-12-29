from asyncio import run as async_run
from aiohttp import ClientSession
import json

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


async def get_manga_info_from_comick(slug):
    url = f"https://api.comick.dev/comic/{slug}"
    try:
        data = await get_comick_data(url)
        return True, data
    except Exception as e:
        return False, e



async def get_latest_chapter_comick(slug):
    url = f"https://api.comick.dev/comic/{slug}"
    data = await get_comick_data(url)
    if data:
        return data["latest_chapter"]
    else:
        return ""


async def get_comick_data(url):
    data = await fetch_comick(url)
    if data:
        manga_dict = extract_manga_info(data)
        return manga_dict if manga_dict else {}
    else:
        return {}


async def fetch_comick(url):
    try:
        async with ClientSession(headers=headers) as session:
            async with session.get(url) as rsp:
                if rsp.status == 200:
                    data = await rsp.json()
                    return data
                else:
                    raise Exception(f"Failed: {rsp.status}\n{rsp.text[:200]}")
                    return {}    
    except ValueError:
        print("Invalid JSON in response.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def extract_manga_info(manga_data):
    try:
        comic = manga_data.get("comic",{})
        if comic:
            slug = comic.get("slug","")
            hid = comic.get("hid","")
            title = comic.get("title","")
            status = comic.get("status",5)
            bayesian_rating = comic.get("bayesian_rating",0)
            follow_rank = comic.get("follow_rank",10000000)
            content_rating = comic.get("content_rating","")
            demographic = comic.get("demographic",None)
            start_year = comic.get("year",1200)
            cover_filename_list = comic.get("md_covers",[])

            # Get authors and artists name
            authors_list = []
            for author in manga_data.get("authors",""):
                authors_list.append(author["name"])
            authors = ", ".join(authors_list)

            artists_list = []
            for artist in manga_data.get("artists",""):
                artists_list.append(artist["name"])
            artists = ", ".join(artists_list)

            # Get description
            description = comic.get("desc","")
            short_desc = ""
            if description:
                short_desc = f"{description[:350]}..."

            cover_url = ""
            if cover_filename_list:            
                cover_filename = cover_filename_list[0].get("b2key","")                
                cover_url = f"https://meo.comick.pictures/{cover_filename}"

            latest_chapter = comic.get("last_chapter")

            return {
                "title": title,
                "source": "comick",
                "hid": hid,
                "slug": slug,
                "authors": authors,
                "artists": artists,
                "latest_chapter": latest_chapter,
                "cover_url": cover_url,
                "description": short_desc,
                "status": status,
                "bayesian_rating": bayesian_rating,
                "follow_rank": follow_rank,
                "content_rating": content_rating,
                "demographic": demographic,
                "start_year": start_year,
            }
        else:
            return {}
    except Exception as e:
        print(f"Error extracting manga info: {e}")
        return None
    
