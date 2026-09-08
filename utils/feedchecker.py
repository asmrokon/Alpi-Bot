from asyncio import sleep

from .comickparser import get_latest_chapter_comick

#* Import functions to get latest chapters and manage manga/user data
from .db import (
    get_all_manga_list_from_db,
    get_all_manga_list_from_db_with_same_slugs,
    get_dc_ids_using_slug,
    update_latest_chapter_comick,
)


#* Entry point to get new chapters info for a given source
async def get_new_chapters_info(source):
    return await create_task_for_check_feed(source)

#* Creates and runs feed checking tasks for all manga in the database for the given source
async def create_task_for_check_feed(source):
    if source == "comick":
        manga_list = await get_all_manga_list_from_db("comick")
        if not manga_list:
            return
        ids_n_slugs_list = []
        for manga in manga_list:
            if manga:
                if int(manga["status"]) in [1,4]:
                    id_n_slug = await check_comick_feed(manga)
                    if id_n_slug:
                        ids_n_slugs_list.append(id_n_slug)
                    await sleep(1)
                
        return ids_n_slugs_list



async def check_comick_feed(manga):
    latest_chapter = await get_latest_chapter_comick(manga["slug"])
    last_seen_latest_chapter = manga["latest_chapter"]

    if latest_chapter:
        if int(latest_chapter) > int(last_seen_latest_chapter):
            await update_latest_chapter_comick(manga["slug"],latest_chapter)
            to_notify_users_ids = await get_dc_ids_using_slug(manga["slug"]) 
            return {"slug": manga["slug"],"dc_ids": to_notify_users_ids,"latest_chapter":latest_chapter}
        else:
            return {}
    else:
        return {}





async def has_new_chapter(manga):
    if not manga:
        return {}
    stored_manga_list = await get_all_manga_list_from_db_with_same_slugs([manga["slug"]])
    
    for stored_manga in stored_manga_list:
        if manga["slug"] == stored_manga["slug"]:
            if manga["latest_chapter"]:
                if int(manga["latest_chapter"]) > int(stored_manga["latest_chapter"]):                    
                    to_notify_users_ids = await get_dc_ids_using_slug(manga["slug"]) 
                    if to_notify_users_ids:
                        await update_latest_chapter_comick(slug=manga["slug"],latest_chapter=manga["latest_chapter"])
                        return {"slug": manga["slug"],"dc_ids": to_notify_users_ids,"latest_chapter": manga["latest_chapter"]}
