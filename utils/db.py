from aiosqlite import connect, Row
from pathlib import Path

from asyncio import run


#* Return the Path object for the database file with the given filename (no extension).
def get_db_path(filename):
    db_path = Path(__file__).parent.parent / "database" / f"{filename}.db"
    return db_path



async def get_subscribers_list(source: str):
    db_path = get_db_path("news_subscribers")
    dc_ids = []
    async with connect(db_path) as db:
        async with db.execute(f"select dc_id from users where {source} = ?",(1,)) as cursor: 
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    dc_ids.append(int(row[0]))
                return dc_ids

            else:
                return dc_ids


async def update_subscribscription(dc_id: str,source: str, num: int):
    db_path = get_db_path("news_subscribers")
    async with connect(db_path) as db:
        await db.execute(
"""
insert or ignore into users
(dc_id,croll, mal)
values (?,?,?)
""",(dc_id,0,0))
        await db.commit()

        await db.execute(f"update users set {source} = ? where dc_id = ?",(num,dc_id))
        await db.commit()



async def create_table_for_news_db():
    db_path = get_db_path("news_subscribers")
    async with connect(db_path) as db:
        await db.execute(
"""
create table if not exists users (
    dc_id integer primary key,
    crunchyroll integer,
    mal_news integer
)
""")


#* Updates comick cover link
async def update_comick_cover_db(slug,cover_url): 
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        #* writes in mangas table        
        await db.execute("update mangas set cover_url = ? where slug = ?",(cover_url,slug))
        await db.commit()



#* Check whether a (dc_id, manga_id/slug) pair already exists in `user_manga`.
async def is_duplicate(source,dc_id,manga_id):
    db_path = get_db_path(source)
    
    if source == "comick":
        slug = manga_id

        async with connect(db_path) as db:
            async with db.execute("select 1 from user_manga where dc_id = ? and slug = ?",(dc_id,slug)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return True
                else:
                    return False

    else:
        async with connect(db_path) as db:
            async with db.execute("select 1 from user_manga where dc_id = ? and manga_id = ?",(dc_id,manga_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return True
                else:
                    return False



#* Remove a user's subscription to a manga (by slug) and delete the manga
#* from `mangas` if no users remain subscribed.
async def remove_manga_from_comick(dc_id,slug):
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        await db.execute("delete from user_manga where dc_id = ? and slug = ?",(dc_id,slug))
        await db.commit()

        #* delete manga from mangas table if there is none
        async with db.execute("select * from user_manga where slug = ?",(slug,)) as cursor:
            rows = await cursor.fetchall()
            if not rows:
                await db.execute("delete from mangas where slug = ?",(slug,))
                await db.commit()




#* Return a list of manga records (as dicts) that a user (dc_id) is subscribed to.
async def get_manga_list_of_a_user_from_comick(dc_id):
    slugs = []
    manga_dicts = []
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        async with db.execute("select slug from user_manga where dc_id = ?",(dc_id,)) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                slugs.append(row[0])
    
    async with connect(db_path) as db:
        db.row_factory = Row
        for slug in slugs:
            async with db.execute("select * from mangas where slug = ?",(slug,)) as cursor:
                row = await cursor.fetchone()
                manga_dicts.append(dict(row)) #* type: ignore
    return manga_dicts



#* Retrieve all manga records from the given source database as a list of dicts.
async def get_all_manga_list_from_db(source):
    manga_dicts = []
    db_path = get_db_path(source)
    async with connect(db_path) as db:
        db.row_factory = Row
        async with db.execute("select * from mangas") as cursor:
            async for row in cursor:
                manga_dicts.append(dict(row)) #* type: ignore
    return manga_dicts



#* Update the `latest_chapter` value for a manga identified by slug (comick DB).
async def update_latest_chapter_comick(slug,latest_chapter):
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        await db.execute("update mangas set latest_chapter = ? where slug = ?",(latest_chapter,slug))
        await db.commit()



#* Return a list of Discord IDs (`dc_id`) that are subscribed to the given slug.
async def get_dc_ids_using_slug(slug):
    db_path = get_db_path("comick")
    dc_ids=[]
    async with connect(db_path) as db:
        async with db.execute("select dc_id from user_manga where slug = ?",(slug,)) as cursor:
            async for row in cursor:
                dc_ids.append(row[0])
    return dc_ids



#* Return the title for a given slug, or a default string if not found.
async def get_title_from_slug(slug):
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        async with db.execute("select title from mangas where slug = ?",(slug,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                return "No Title"




#* Return the cover URL for a slug, or a fallback default image if missing.
async def get_cover_url_using_slug(slug):
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        async with db.execute("select cover_url from mangas where slug = ?",(slug,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                return "https://meo.comick.pictures/0xDy1.jpg"




#* Reset `latest_chapter` to 1 for all mangas in the comick database.
async def reset_chapters_to_1():
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        await db.execute("update mangas set latest_chapter = ?",(1,))
        await db.commit()





#* Insert or ignore manga metadata into `mangas`, and ensure `user_manga` and
#* `users` have corresponding entries for the provided `dc_id` and `manga`.
async def write_info_comick(dc_id,manga):
    db_path = get_db_path("comick")
    async with connect(db_path) as db:
        #* writes in mangas table        
        await db.execute(
"""
insert or ignore into mangas
(slug,hid,title,authors,artists,latest_chapter,cover_url,description)
values (?,?,?,?,?,?,?,?)
""",(manga["slug"],manga["hid"],manga["title"],manga["authors"],manga["artists"],manga["latest_chapter"],manga["cover_url"],manga["description"]))
        
        #* writes in user_manga table
        await db.execute(
"""
insert or ignore into user_manga
(dc_id,slug)
values (?,?)""",(dc_id,manga["slug"]))
        await db.commit()

        #* writes in users table
        await db.execute(
"""
insert or ignore into users
(dc_id)
values (?)""",(dc_id,))
        await db.commit()






#*run(change_latest_chapter())
# run(create_table_for_news_db())