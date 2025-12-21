import asyncio
import cloudscraper
import requests


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
    data = await asyncio.to_thread(fetch_comick, url)
    if data:
        manga_dict = extract_manga_info(data)
        return manga_dict

def fetch_comick(url):
    try:
        scraper = cloudscraper.create_scraper()  # handles Cloudflare
        response = scraper.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed: {response.status_code}, {response.text[:200]}")
    except requests.exceptions.Timeout:
        print("Timeout, retry later.")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Server unreachable: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError:
        print("Invalid JSON in response.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def extract_manga_info(manga_data):
    try:
        slug = manga_data.get("comic",{}).get("slug","")
        hid = manga_data.get("comic",{}).get("hid","")

        title = manga_data.get("comic",{}).get("title","")

        cover_filename = manga_data.get("comic",{}).get("md_covers",[])[0].get("b2key","")

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
        description = manga_data.get("comic",{}).get("desc","")

        cover_url = ""
        if cover_filename:
            cover_url = f"https://meo.comick.pictures/{cover_filename}"

        latest_chapter = manga_data.get("comic",{}).get("last_chapter")

        return {
            "title": title,
            "hid": hid,
            "slug": slug,
            "authors": authors,
            "artists": artists,
            "latest_chapter": latest_chapter,
            "cover_url": cover_url,
            "description": f"{description[:350]}...", # type: ignore
        }

    except Exception as e:
        print(f"Error extracting manga info: {e}")
        return None
    



