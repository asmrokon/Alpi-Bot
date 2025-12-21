from asyncio import sleep, create_task, gather

#* Import functions to get latest chapters and manage manga/user data
from .db import get_all_manga_list_from_db, update_latest_chapter_comick, get_dc_ids_using_slug
from .comickparser import get_latest_chapter_comick

#* Entry point to get new chapters info for a given source
async def get_new_chapters_info(source):
    return await create_task_for_check_feed(source)

#* Creates and runs feed checking tasks for all manga in the database for the given source
async def create_task_for_check_feed(source):
    if source == "comick":
        manga_list = await get_all_manga_list_from_db("comick")
        if not manga_list:
            return
        tasks = []
        for manga in manga_list:
            if manga:
                task = create_task(check_comick_feed(manga))
                tasks.append(task)
                await sleep(2)
        
        results = await gather(*tasks)
        return results



async def check_comick_feed(manga):
    latest_chapter = await get_latest_chapter_comick(manga["slug"])
    last_seen_latest_chapter = manga["latest_chapter"]

    if int(latest_chapter) > int(last_seen_latest_chapter):
        await update_latest_chapter_comick(manga["slug"],latest_chapter)
        to_notify_users_ids = await get_dc_ids_using_slug(manga["slug"]) 
        return {"slug": manga["slug"],"dc_ids": to_notify_users_ids,"latest_chapter":latest_chapter}
    else:
        return None
