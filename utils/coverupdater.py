from asyncio import create_task, sleep

from .comickparser import get_manga_info_from_comick
from .db import (
    get_all_manga_list_from_db,
    update_comick_cover_db,
)


# * Entry point to get new cover links
async def update_cover_url():
    await create_task_for_cover_update("comick")

# * Creates and runs feed checking tasks for all manga in the database for the given source
async def create_task_for_cover_update(source):
    if source == "comick":
        manga_list = await get_all_manga_list_from_db("comick")
        if manga_list:
            for manga in manga_list:
                if manga:
                    create_task(update_comick_cover(manga))
                    await sleep(2)



async def update_comick_cover(manga):
    success, latest_data = await get_manga_info_from_comick(manga["slug"])

    if success and (latest_data["cover_url"] != manga["cover_url"]):
        await update_comick_cover_db(manga["slug"],latest_data["cover_url"])

