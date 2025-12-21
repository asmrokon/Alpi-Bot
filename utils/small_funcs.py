import aiohttp
import asyncio
import cloudscraper

    
   
async def check_link_and_get_comick_slug(link):
    if "https://comick.io" not in link and "https://comick.dev" not in link:
        return "not_comick", "a"
    if "/comic/" in link:
        slug = link.split("https://comick.dev/comic/")[1]
        if slug:
            status = await asyncio.to_thread(get_comick_status,link)
            return status, slug
        else:
            return 404, "a"
    else:
        return "not_manga", "a"
    

def get_comick_status(url):
    scraper = cloudscraper.create_scraper() 
    response = scraper.get(url)
    return response.status_code
