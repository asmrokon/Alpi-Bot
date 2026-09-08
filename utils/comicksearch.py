from aiohttp import ClientSession

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


async def api_search_comick(params):
    async with ClientSession(headers=headers) as session:
        async with session.get("https://api.comick.dev/v1.0/search/",params=params) as rsp:
            if rsp.status == 200:
                data = await rsp.json()
                return data
            else:
                return {}

           

async def get_comick_search_result(params):
    raw_json_list = await api_search_comick(params)
    if not raw_json_list:
        return {}
    manga_list = extract_manga_info(raw_json_list)
    if not manga_list:
        return {}
    
    return manga_list

    
    
def extract_manga_info(raw_manga_data_list):
    manga_list = []
    for manga_data in raw_manga_data_list:
        try:
            hid = manga_data.get("hid","None") or "None"
            slug = manga_data.get("slug","None") or "None"
            title = manga_data.get("title","None") or "None"
            description = manga_data.get("desc","None") or "None"
            status = manga_data.get("status",5) or 5
            rating = manga_data.get("bayesian_rating",0) or 0
            followers = manga_data.get("user_follow_count",0) or 0
            year = manga_data.get("year",0) or 0
            latest_chapter = manga_data.get("last_chapter",0) or 0
            cover_filename_list = manga_data.get("md_covers",[])            
            cover_filename = "x7gMkp.jpg"

            if cover_filename_list:
                cover_filename = cover_filename_list[0].get("b2key","") 
            
            cover_url = f"https://meo.comick.pictures/{cover_filename}"

            short_desc = ""
            if description:
                short_desc = f"{description[:1000]}..." if len(description) > 1000 else description

            manga_list.append({
                "title": title,
                "hid": hid,
                "slug": slug,
                "latest_chapter": latest_chapter,
                "cover_url": cover_url,
                "description": short_desc,
                "status": status,
                "rating": rating,
                "followers": followers,
                "year": year,
            })


        except Exception as e:
            print(f"Error extracting manga info: {e}\n{manga_data}\n")
            pass
    
    
    return manga_list
