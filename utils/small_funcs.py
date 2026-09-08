import aiohttp

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

   
async def check_link_and_get_comick_slug(link):
    if ("https://comick.io/" not in link) and ("https://comick.dev/" not in link):
        return "not_comick", "a"
    if "https://comick.io" in link:
        link = link.replace("comick.io","comick.dev")
    if "/comic/" in link:
        slug = link.split("https://comick.dev/comic/")[1]
        if slug:
            status = await get_comick_status(link)
            return status, slug
        else:
            return 404, "a"
    else:
        return "not_manga", "a"
    

async def get_comick_status(url):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            return response.status
