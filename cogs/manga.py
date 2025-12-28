from discord.ext import commands
from discord import Embed, Color, ButtonStyle, app_commands
from discord.ui import Button, View
from discord import ui
import discord
from typing import Literal
from os import getenv
import asyncio


from utils.small_funcs import check_link_and_get_comick_slug 
from utils.comickparser import get_manga_info_from_comick
from utils.coverupdater import update_cover_url
from utils.db import (
    get_manga_list_of_a_user_from_comick,
    write_info_comick,
    get_title_from_slug,
    get_cover_url_using_slug,
    is_duplicate,
    remove_manga_from_comick,
)
from utils.feedchecker import get_new_chapters_info, has_new_chapter
from utils.comicksearch import get_comick_search_result



#* channel ID
error_log_channel_id = int(getenv("error_log_channel_id"))

# Emojies
ongoing_emoji = "<:ongoing:1453695986311499890>"
cancelled_emoji = "<:cancelled:1453695978157899863>"
hiatus_emoji = "<:hiatus:1453695980355457225>"
completed_emoji = "<:completed:1453695983245590661>"
bookmark_emoji = "<:bookmark:1453666289003270310>"
star_emoji = "<:star:1453667947070357646>"
bin_emoji = "<:bin:1453439435973857513>"
leftarrow_emoji = "<:leftarrow:1453438612774326304>"
rightarrow_emoji = "<:rightarrow:1453438615362338847>"
chapter_emoji = "<:chapter:1453761149542858772>"
cursor_emoji = "<:cursor:1453762353505112097>"
#* Predefined embed messages for various bot responses
embed_messages = {
    "adding": Embed(
        title="Adding Treat 🐾",
        description="Paw... I am adding your treat! Meow~",
        color=Color.light_gray(),
    ),
    "added": Embed(
        title="Treat Added 🐾",
        description="Nyaa~ Added! Your treat is safe in my paws.",
        color=Color.green(),
    ),
    "400": Embed(
        title="Broken Link 🐾",
        description="Paw... messy link. Fix it, human.",
        color=Color.red(),
    ),
    "401": Embed(
        title="No Key 🐾",
        description="Scratch! That place says no entry for you.",
        color=Color.red(),
    ),
    "403": Embed(
        title="Locked Yard 🐾",
        description="Hisss... gate is locked. I can not sneak in there.",
        color=Color.red(),
    ),
    "404": Embed(
        title="Ghost Link 🐾",
        description="Meow? I looked everywhere, no such page!",
        color=Color.red(),
    ),
    "not_comick": Embed(
    title="Wrong Treat 🐾",
    description="Hiss... I only chase Comick and  treats, not this weird thing.",
    color=Color.red(),
    ),
    "else": Embed(
        title="Weird Magic🐾",
        description="Scratch! Something odd happened. I can not fetch it.",
        color=Color.red(),
    ),
    "command_options": Embed(
        title="🐾 Command Time!",
        description="Meow? Pick a play:",
        color=Color.light_gray(),
    ).add_field(
        name="Options",
        value="`add`, `remove`, `list`, or `search`",
    ),
    "no_link": Embed(
        title="😿 Missing Treat!",
        description="Paw... you forgot the treat! Give me a link",
        color=Color.orange(),
    ),
    "not_manga": Embed(
        title="Wrong Treat 🐾",
        description="Paw... this isn't a manga page. Feed me a real one!",
        color=Color.red(),
    ),
    "duplicate_manga": Embed(
        title="Duplicate Treat 🐾",
        description="Nyaa~ I already caught this one! It's in my paws already.",
        color=Color.red(),
    ),
    "no_manga_to_show": Embed(
        title="Empty Basket 🐾",
        description="Meow... the list is empty. Feed me some treats first!",
        color=Color.red(),
    ),
    "all_removed": Embed(
        title="Empty Basket 🐾",
        description="Nyaa... all your treats have been removed from the basket!",
        color=Color.light_gray(),
    ),
    "no_manga_to_remove": Embed(
        title="Empty Basket 🐾",
        description="Nyaa... nothing here to take out. Feed me some treats first!",
        color=Color.red(),
    ),
    "max_manga_limit": Embed(
        title="List Overflow 🐾",
        description="Nyaa... your basket is full! You can not add more mangas.",
        color=Color.red(),
    ),
}
def cooldown_for_everyone_but_me(interaction: discord.Interaction):
    if interaction.user.id == 743831396874846229:
        return None
    return app_commands.Cooldown(rate=2,per=5)



#* MangaCog class for manga management commands
@app_commands.user_install()
class MangaCog(commands.GroupCog, name="manga", description="Manga management"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self): 
        asyncio.create_task(self.check_feed_comick())
        asyncio.create_task(self.UpdateCoverLink())
    """
                                            ///     SUB CLASSES      ///
    """


    #* View for displaying and interacting with a single manga
    class SingleMangaView(ui.LayoutView):
        def __init__(self, manga_dicts, dc_id, source):
            super().__init__()
            self.manga_dicts = manga_dicts
            self.dc_id = dc_id
            self.cur_page = 1
            self.source = source

        #* Generate embed for current manga page
        async def single_manga_view(self):
            num = self.cur_page - 1

            self.clear_items()

            container = ui.Container()

            title = ui.TextDisplay(f"# {self.manga_dicts[num]['title']}")
            container.add_item(title)

            title_separator = ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small)
            container.add_item(title_separator)

            infos = ui.TextDisplay(
            f"**Latest Chapter**: {self.manga_dicts[num]["latest_chapter"]}\n**Authors**: {self.manga_dicts[num]["authors"]}\n**Artists**: {self.manga_dicts[num]["artists"]}\n{self.manga_dicts[num]["description"]}")
            container.add_item(infos)

            cover = ui.MediaGallery(discord.MediaGalleryItem(self.manga_dicts[num]["cover_url"]))
            container.add_item(cover)

            footer = ui.TextDisplay(f"-# **{self.cur_page}/{len(self.manga_dicts)}**")
            container.add_item(footer)

            buttons_row = ui.ActionRow()

            previous_button = Button(emoji="<:leftarrow:1453438612774326304>", style=ButtonStyle.secondary)
            previous_button.callback = self.previous_manga

            remove_button = Button(emoji="<:bin:1453439435973857513>", style=ButtonStyle.secondary)
            remove_button.callback = self.remove_manga

            next_button = Button(emoji="<:rightarrow:1453438615362338847>", style=ButtonStyle.secondary)
            next_button.callback = self.next_manga

            buttons_row.add_item(previous_button)
            buttons_row.add_item(remove_button)
            buttons_row.add_item(next_button)

            self.add_item(container)
            self.add_item(buttons_row)

        #* Remove manga from user's list
        async def remove_manga(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return

            await remove_manga_from_comick(self.dc_id, self.manga_dicts[(self.cur_page - 1)]["slug"])

            
            title = self.manga_dicts[self.cur_page - 1]["title"]
            del self.manga_dicts[self.cur_page - 1]
            if len(self.manga_dicts) == 0:
                for item in self.children:
                    self.remove_item(item)
                await interaction.response.edit_message(
                    embed=embed_messages["all_removed"], view=self
                )
                await interaction.followup.send(
                    f"Nyaa... the treat **{title}** has been removed.",
                    ephemeral=True,
                )
            else:
                self.cur_page -= 1
                await self.next_manga(interaction)
                await interaction.followup.send(
                    f"Nyaa... the treat **{title}** has been removed.",
                    ephemeral=True,
                )

        #* Go to previous manga in the list
        async def previous_manga(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            total_page = len(self.manga_dicts)

            if (self.cur_page - 1) == 0:
                self.cur_page = total_page
                await self.single_manga_view()
                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page -= 1
                await self.single_manga_view()
                
                await interaction.response.edit_message(view=self)

        #* Go to next manga in the list
        async def next_manga(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            total_page = len(self.manga_dicts)
            if (self.cur_page + 1) > total_page:
                self.cur_page = 1
                await self.single_manga_view()
                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page += 1
                await self.single_manga_view()
                
                await interaction.response.edit_message(view=self)


    class CompactMangaView(ui.LayoutView):
        def __init__(self, manga_dicts, dc_id, name, source,limit):
            super().__init__()
            self.manga_dicts = manga_dicts
            self.name = name
            self.source = source
            self.dc_id = dc_id

            self.limit_per_page = limit
            self.cur_page = 0
            self.total_page = ((len(manga_dicts) - 1) // self.limit_per_page) + 1

        #* Generate embed for current manga page
        async def single_page_view(self):
            self.clear_items()

            start_index = self.limit_per_page * self.cur_page
            last_index = start_index + self.limit_per_page            

            container = ui.Container()

            container.add_item(ui.TextDisplay(f"## {self.name}'s Manga List"))
            container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))

            for manga in self.manga_dicts[start_index:last_index]:
                section = ui.Section(
                    ui.TextDisplay(f"### {manga['title']}\n**Latest Chapter**: {manga["latest_chapter"]}\n**Authors**: {manga["authors"]}\n**Artists**: {manga["artists"]}"),
                    accessory=ui.Thumbnail(manga["cover_url"])
                )
                container.add_item(section)
                container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))                

            footer = ui.TextDisplay(f"-# **{self.cur_page+1}/{self.total_page}  ·  Total {len(self.manga_dicts)} Mangas**")
            container.add_item(footer)

            
            buttons_row = ui.ActionRow()

            previous_button = Button(emoji="<:leftarrow:1453438612774326304>", style=ButtonStyle.secondary)
            previous_button.callback = self.previous_page

            next_button = Button(emoji="<:rightarrow:1453438615362338847>", style=ButtonStyle.secondary)
            next_button.callback = self.next_page

            buttons_row.add_item(previous_button)
            buttons_row.add_item(next_button)

            self.add_item(container)
            self.add_item(buttons_row)

        
        #* Go to next manga in the list
        async def next_page(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            

            if (self.cur_page + 1) == self.total_page:
                self.cur_page = 0

                await self.single_page_view()
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page += 1

                await self.single_page_view()
                await interaction.response.edit_message(view=self)

        #* Go to previous manga page
        async def previous_page(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return


            if (self.cur_page) == 0:
                self.cur_page = self.total_page - 1

                await self.single_page_view()                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page -= 1

                await self.single_page_view()
                await interaction.response.edit_message(view=self)


    class RemoveMangaView(ui.LayoutView):
        def __init__(self, manga_dicts, dc_id, name, source,limit):
            super().__init__()
            self.manga_dicts = manga_dicts
            self.name = name
            self.source = source
            self.dc_id = dc_id

            self.limit_per_page = limit
            self.cur_page = 0
            self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

        #* Generate embed for current manga page
        async def single_page_view(self):
            self.clear_items()

            self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

            start_index = self.limit_per_page * self.cur_page
            last_index = start_index + self.limit_per_page            

            container = ui.Container()

            container.add_item(ui.TextDisplay(f"## {self.name}'s Manga List"))
            container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))

            for idx, manga in enumerate(self.manga_dicts[start_index:last_index],start=0):
                section = ui.Section(
                    ui.TextDisplay(f"### {manga['title']}\n**Latest Chapter**: {manga["latest_chapter"]}\n**Authors**: {manga["authors"]}\n**Artists**: {manga["artists"]}"),
                    accessory=ui.Thumbnail(manga["cover_url"])
                )
                container.add_item(section)
                
                custom_id = f"{self.cur_page * self.limit_per_page + idx}_{len(self.manga_dicts[start_index:last_index])}"
                remove_button = Button(label="Remove",style=ButtonStyle.gray,custom_id=custom_id)
                remove_button.callback = self.remove_manga

                remove_button_section = ui.Section(
                    ui.TextDisplay("-# **Remove from Library **"),
                    accessory=remove_button)

                container.add_item(remove_button_section)

                container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))  

            footer = ui.TextDisplay(f"-# **{self.cur_page+1}/{self.total_page}  ·  Total {len(self.manga_dicts)} Mangas**")
            container.add_item(footer)

            
            buttons_row = ui.ActionRow()

            previous_button = Button(emoji="<:leftarrow:1453438612774326304>", style=ButtonStyle.secondary)
            previous_button.callback = self.previous_page

            next_button = Button(emoji="<:rightarrow:1453438615362338847>", style=ButtonStyle.secondary)
            next_button.callback = self.next_page

            buttons_row.add_item(previous_button)
            buttons_row.add_item(next_button)

            self.add_item(container)
            self.add_item(buttons_row)


        async def remove_manga(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return

            custom_id, total_manga = str(interaction.data['custom_id']).split("_")
            custom_id = int(custom_id)
            total_manga = int(total_manga)
            

            await remove_manga_from_comick(self.dc_id, self.manga_dicts[custom_id]["slug"])

            
            title = self.manga_dicts[custom_id]["title"]

            del self.manga_dicts[custom_id]
            if len(self.manga_dicts) == 0:

                self.clear_items()

                self.add_item(ui.TextDisplay("Removed all manga"))

                await interaction.response.edit_message(view=self)
                await interaction.followup.send(
                    f"Nyaa... the treat **{title}** has been removed.",
                    ephemeral=True,
                )
            else:
                
                if total_manga == 1:
                    await self.previous_page(interaction)
                else:
                    await self.single_page_view()
                    await interaction.response.edit_message(view=self)

                await interaction.followup.send(
                    f"Nyaa... the treat **{title}** has been removed.",
                    ephemeral=True,
                )

        
        async def next_page(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            

            if (self.cur_page + 1) == self.total_page:
                self.cur_page = 0

                await self.single_page_view()
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page += 1

                await self.single_page_view()
                await interaction.response.edit_message(view=self)

        #* Go to previous manga page
        async def previous_page(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return


            if (self.cur_page) == 0:
                self.cur_page = self.total_page - 1

                await self.single_page_view()                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page -= 1

                await self.single_page_view()
                await interaction.response.edit_message(view=self)


    class SearchResultView(ui.LayoutView):
        def __init__(self, manga_dicts, dc_id, source, limit, searched_name,bot):
            super().__init__()
            self.manga_dicts = manga_dicts
            self.source = source
            self.dc_id = dc_id
            self.searched_name = searched_name     
            self.bot = bot       

            self.limit_per_page = limit
            self.cur_page = 0
            self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

        #* Generate embed for current manga page
        async def single_page_view(self):
            status_conv = {1:f"{ongoing_emoji} Ongoing", 2:f"{completed_emoji} Completed",3:f"{cancelled_emoji} Cancelled", 4:f"{hiatus_emoji} Hiatus"}  
            self.clear_items()

            self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

            start_index = self.limit_per_page * self.cur_page
            last_index = start_index + self.limit_per_page            

            container = ui.Container()
            

            for idx, manga in enumerate(self.manga_dicts[start_index:last_index],start=0):
                short_desc = f"{manga["description"][:180]}..." if len(manga["description"]) > 180 else manga["description"]

                section = ui.Section(
                    ui.TextDisplay(f"### {manga['title']}\n{chapter_emoji} Ch. {manga["latest_chapter"]}   •   {status_conv[int(manga["status"])]}   •   {star_emoji} {manga["rating"]}\n{short_desc}"),
                    accessory=ui.Thumbnail(manga["cover_url"])
                )
                container.add_item(section)
                
                custom_id = f"{self.cur_page * self.limit_per_page + idx}_{len(self.manga_dicts[start_index:last_index])}"

                if manga["status"] and (int(manga["status"]) == 1):
                    add_button = Button(label="Add",emoji=bookmark_emoji,style=ButtonStyle.gray,custom_id=custom_id)
                else:
                    add_button = Button(label="Add",emoji=bookmark_emoji,style=ButtonStyle.gray,custom_id=custom_id,disabled=True)
                add_button.callback = self.add_manga

                web_view_button = Button(label="View on web",style=ButtonStyle.link,url=f"https://comick.dev/comic/{manga["slug"]}")
                
                section_buttons_row = ui.ActionRow()

                section_buttons_row.add_item(add_button)
                section_buttons_row.add_item(web_view_button)
                container.add_item(section_buttons_row)

                if idx != (self.limit_per_page - 1):
                    container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))  

                
            buttons_row = ui.ActionRow()

            previous_button = Button(emoji="<:leftarrow:1453438612774326304>", style=ButtonStyle.secondary)
            previous_button.callback = self.previous_page

            next_button = Button(emoji="<:rightarrow:1453438615362338847>", style=ButtonStyle.secondary)
            next_button.callback = self.next_page

            footer_button = Button(label=f"Page {self.cur_page+1} of {self.total_page}",style=ButtonStyle.secondary,disabled=True)
            
            navigate_row = ui.ActionRow()
            navigate_select = ui.Select(placeholder="Navigate to...",)
            
            for i in range(self.total_page):                
                navigate_select.append_option(discord.SelectOption(label=f"Page {i + 1}",value=str(i)))
                                    
            navigate_select.callback = self.navigate_to

            buttons_row.add_item(previous_button)
            buttons_row.add_item(footer_button)
            buttons_row.add_item(next_button)
            navigate_row.add_item(navigate_select)

            self.add_item(container)
            self.add_item(buttons_row)
            self.add_item(navigate_row)


        async def navigate_to(self,interaction: discord.Interaction):
            page_num = int(interaction.data["values"][0])
            self.cur_page = page_num

            await self.single_page_view()
            await interaction.response.edit_message(view=self)


        async def add_manga(self, interaction: discord.Interaction):
            await interaction.response.defer()
            if interaction.user.id != self.dc_id:
                await interaction.followup.send(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return

            custom_id, total_manga = str(interaction.data['custom_id']).split("_")
            custom_id = int(custom_id)
            
            
            slug = self.manga_dicts[custom_id]["slug"]        

            #* checks if it is already in the list or not and then add it if not in list
            if not await is_duplicate("comick",interaction.user.id, slug):    
                success, manga = await get_manga_info_from_comick(slug)                
                if success and isinstance(manga,dict):                 
                    dc_ids_n_slug = await has_new_chapter(manga=manga)
                    if dc_ids_n_slug:
                        await self.notify_users(dc_ids_n_slug,manga)
                    await write_info_comick(dc_id=interaction.user.id, manga=manga)
                    await interaction.followup.send(content=f"Nyaa... the treat **{self.manga_dicts[custom_id]["title"]}** has been added.",ephemeral=True)
                else:
                    #* sends error msg in chat
                    embed = Embed(
                        title="Data Fetch Failed 🐾",
                        description="Paw... I tried, but the data will not come. Tell the owner!",
                        color=Color.red(),
                    )
                    await interaction.followup.send(embed=embed,ephemeral=True)                               
            else:
                await interaction.followup.send(embed=embed_messages["duplicate_manga"],ephemeral=True)


        async def notify_users(self,dc_ids_n_slug_list,manga):            
            title = manga["title"]
            latest_chapter = dc_ids_n_slug_list["latest_chapter"]
            cover_url = manga["cover_url"]
            slug = manga["slug"]
            
            layout_view = MangaCog.ChapterNotification(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

            await layout_view.notification()
            
            dc_ids = dc_ids_n_slug_list["dc_ids"]

            for dc_id in dc_ids:                            
                try:
                    user = self.bot.get_user(dc_id)                    
                    if user is None:
                        try:
                            user = await self.bot.fetch_user(dc_id)
                        except discord.NotFound:
                            await print(f"User `{dc_id} does not exist at all.")
                        except discord.HTTPException:
                            await print(
                                f"Could not fetch {dc_id}'s user info to send Notification"
                            )   

                    await user.send(view=layout_view)                
                except Exception as e:
                    await print(
                        f"Could not send notification to `{dc_id}`\nError:```{e}```"
                    ) 

        
        async def next_page(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            

            if (self.cur_page + 1) == self.total_page:
                self.cur_page = 0

                await self.single_page_view()
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page += 1

                await self.single_page_view()
                await interaction.response.edit_message(view=self)

        #* Go to previous manga page
        async def previous_page(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return


            if (self.cur_page) == 0:
                self.cur_page = self.total_page - 1

                await self.single_page_view()                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page -= 1

                await self.single_page_view()
                await interaction.response.edit_message(view=self)


#*                                            ///     SLASH COMMANDS (ADD,REMOVE,LIST)     ///


    @app_commands.command(name="search",description="Search Comick.io for manga with optional filters")
    @app_commands.describe(
    title="Manga title or keywords to search on Comick.io",
    status="Publication status filter (default: all statuses)",
    demographic="Target demographic filter (default: all demographics)",
    content_rating="Content rating filter (default: Safe and Suggestive)",
    limit="Number of results to return per request (default: 15)",
    sort="Result sorting method (currently not functional)")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def search(
                self,
                interaction: discord.Interaction,
                title: str,
                status: Literal["Ongoing","Completed","Cancelled","Hiatus"] = None,
                demographic: Literal["Shounen","Shoujo","Seinen","Josei"] = None,
                content_rating: Literal["All","Safe","Suggestive","Erotica"] = None,
                limit: Literal[5,10,15,20] = 15,
                sort: Literal["follow","view","created_at","user_follow_count","uploaded","rating"] = None
                    ):
        title = title.lower()
        status_conv = {"ongoing": 1, "completed": 2, "cancelled": 3, "hiatus": 4}   
        demographic_conv = {"shounen": 1,"shoujo": 2,"seinen": 3,"josei": 4}
        params= {
                "type": "comic",                
                "page": 1,
                "limit": limit,                                
                "q": title,
                "content_rating": ["safe","suggestive"]
                }
        if status:
            status = str(status).lower()
            params["status"] = status_conv[status]
        if demographic:
            demographic = str(demographic).lower()
            params["demographic"] = demographic_conv[demographic]   
        if content_rating: 
            if content_rating != "All":
                params["content_rating"] = str(content_rating).lower()
            elif content_rating == "All":                
                del params["content_rating"]
        if sort:
            params["sort"] = str(sort).lower()

        await interaction.response.defer()
        
        manga_list = await get_comick_search_result(params)        

        if manga_list:            
                view = self.SearchResultView(manga_dicts=manga_list,dc_id=interaction.user.id,source="comick",limit=3,searched_name=title,bot=self.bot)
                await view.single_page_view()            
                await interaction.followup.send(view=view)  
        else:
            await interaction.followup.send(content="Couldnt search")


    #* Slash command to add a manga to user's list
    @app_commands.command(name="add", description="Add a manga to your list")
    @app_commands.describe(link="Paste the manga comick.io URL you want to add")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def add(self, interaction: discord.Interaction, link: str):
        link = link.lower()
        await self.add_comick(interaction,link)

    #* Slash command to show user's manga list
    @app_commands.command(name="list", description="Show your Manga list")
    @app_commands.describe(mode="Choose how you want the list to be displayed")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def list_manga(self, interaction: discord.Interaction,mode: Literal["Compact", "Detailed"]):
        await self.list_comick(interaction,mode)

    #* Slash command to remove manga from user's list
    @app_commands.command(name="remove", description="Remove a manga from your list")
    @app_commands.describe(mode="Choose whether to remove selected manga or all")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def remove_manga(
        self,
        interaction: discord.Interaction,
        mode: Literal["Select", "All"] = "Select",
    ):
        await self.remove_comick(interaction,mode)



    """
                                            ///     COMICK      ///
    """     

    #* comick manga add function
    async def add_comick(self,interaction,link):
        
        #* checks if the given link is valid or not.
        await interaction.response.send_message(embed=embed_messages["adding"])
        status, slug = await check_link_and_get_comick_slug(link)
        msg = await interaction.original_response()

        if status == 200:            
            #* checks if it is already in the list or not and then add it if not in list
            if not await is_duplicate("comick",interaction.user.id, slug):    
                #* gets manga info in dict  
                success, manga = await get_manga_info_from_comick(slug)
                if success and isinstance(manga,dict):
                    dc_ids_n_slug = await has_new_chapter(manga=manga)
                    if dc_ids_n_slug:
                        await self.notify_users(dc_ids_n_slug,manga)
                    await write_info_comick(dc_id=interaction.user.id, manga=manga)
                    await msg.edit(embed=embed_messages["added"])
                else:
                    #* sends error msg in chat
                    embed = Embed(
                        title="Data Fetch Failed 🐾",
                        description="Paw... I tried, but the data will not come. Tell the owner!",
                        color=Color.red(),
                    )
                    await msg.edit(embed=embed)

                    excep_error_channel = self.bot.get_channel(error_log_channel_id)

                    #* send error message in log
                    fetch_error_embed = Embed(
                        title="Data Fetch Failed (Slash Command)", color=Color.red()
                    )
                    fetch_error_embed.add_field(
                        name="User",
                        value=f"Name: {interaction.user}\nID: `{interaction.user.id}`",
                        inline=False,
                    )
                    fetch_error_embed.add_field(name="Command", value=f"{interaction.command.name}", inline=False)  # type: ignore
                    fetch_error_embed.add_field(name="Channel", value=f"{interaction.channel}\nID: {interaction.channel.id}", inline=False)  # type: ignore
                    fetch_error_embed.add_field(
                        name="Fetch Target", value=f"```{manga}```", inline=False
                    )
                    fetch_error_embed.timestamp = interaction.created_at
                    await excep_error_channel.send(embed=fetch_error_embed)
            else:
                await msg.edit(embed=embed_messages["duplicate_manga"])

        elif status in [400, 401, 403, 404]:
            await msg.edit(embed=embed_messages[f"{status}"])
            return
        elif status in ["not_comick", "not_manga"]:
            await msg.edit(embed=embed_messages[status])
            return
        else:
            await msg.edit(embed=embed_messages["else"])
            return



    async def list_comick(self,interaction,mode):

        #* checks if user has manga in list if not then return with a no manga msg
        dc_id = interaction.user.id
        manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)
        if manga_dicts == []:
            await interaction.response.send_message(
                embed=embed_messages["no_manga_to_show"]
            )
            return

        #* shows manga in compact mode
        if mode == "Compact":
            name = interaction.user.display_name

            # layout_view = self.CompactMangaView(limit=3,manga_dicts=manga_dicts,dc_id=dc_id,name=name,source="comick")

            layout_view = self.CompactMangaView(limit=3,manga_dicts=manga_dicts,dc_id=dc_id,name=name,source="comick")

            await layout_view.single_page_view()
          
            await interaction.response.send_message(view=layout_view)

        #* shows manga in detailed mode
        elif mode == "Detailed":
            layout_view = self.SingleMangaView(manga_dicts, dc_id, "comick")

            await layout_view.single_manga_view()
            
            await interaction.response.send_message(view=layout_view)



    async def remove_comick(self,interaction,mode):

        if mode == "Select":
            dc_id = interaction.user.id
            manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)

            if manga_dicts == []:
                await interaction.response.send_message(
                    embed=embed_messages["no_manga_to_remove"]
                )
                return

            display_name = interaction.user.display_name

            layout_view = self.RemoveMangaView(limit=3,manga_dicts=manga_dicts,dc_id=dc_id,name=display_name,source="comick")
            await layout_view.single_page_view()

            await interaction.response.send_message(view=layout_view)

        else:
            dc_id = interaction.user.id
            manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)
            embed_confirmation = Embed(
                title="⚠️ Confirm Deletion",
                description="You are about to delete **all** manga from your list. This action cannot be undone.\n\nDo you want to proceed?",
                color=Color.red(),
            )

            view_confirmation = View()

            #* Callback for proceeding with removal of all manga
            async def remove_all_manga(interaction):
                if interaction.user.id != dc_id:
                    await interaction.response.send_message(
                        "Scratch! This button is not yours to play with!",
                        ephemeral=True,
                    )
                    return
                await interaction.response.defer()
                for item in view_confirmation.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                await interaction.edit_original_response(
                    embed=embed_confirmation, view=view_confirmation
                )
                msg = await interaction.followup.send(
                    "Removing...", ephemeral=False, wait=True
                )
                for manga in manga_dicts:
                    await remove_manga_from_comick(dc_id, manga["slug"])
                await msg.edit(content="Removed all Manga's from your list")

            #* Callback for canceling removal
            async def cancel_remove_manga(interaction):
                if interaction.user.id != dc_id:
                    await interaction.response.send_message(
                        "Scratch! This button is not yours to play with!",
                        ephemeral=True,
                    )
                    return
                await interaction.response.defer()
                for item in view_confirmation.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                await interaction.edit_original_response(
                    embed=embed_confirmation, view=view_confirmation
                )
                await interaction.followup.send("Canceled", ephemeral=False)

            proceed_button = Button(label="Proceed", style=ButtonStyle.danger)
            proceed_button.callback = remove_all_manga
            view_confirmation.add_item(proceed_button)

            cancel_button = Button(label="Cancel", style=ButtonStyle.secondary)
            cancel_button.callback = cancel_remove_manga
            view_confirmation.add_item(cancel_button)

            await interaction.response.send_message(
                embed=embed_confirmation, view=view_confirmation
            )




    """
                                            ///     FEED CHECKER      ///
    """     
  

    class ChapterNotification(ui.LayoutView):
        def __init__(self,title,latest_chapter,cover_url,slug):
            super().__init__()

            self.title = title
            self.latest_chapter = latest_chapter
            self.cover_url = cover_url
            self.slug = slug

        async def notification(self):
            container = ui.Container()

            title = ui.TextDisplay(f"### Purr! **{self.title}** just dropped a new chapter!\nCan you believe it's chapter **{self.latest_chapter}** already?")
            container.add_item(title)

            cover = ui.MediaGallery(discord.MediaGalleryItem(self.cover_url))
            container.add_item(cover)

            self.add_item(container)

            button_row = ui.ActionRow()
            link_button = Button(label="Link", style=ButtonStyle.link, url=f"https://comick.dev/comic/{self.slug}")

            button_row.add_item(link_button)

            self.add_item(button_row)


    #* Background task to check comick manga feeds for updates
    async def check_feed_comick(self):
        await self.bot.wait_until_ready()

        #* starts loop
        while True:
            #* gets manga and dc list to notify
            slugs_and_dc_ids_and_latest_chap_list = await get_new_chapters_info("comick")

            #* channels
            excep_error_channel = self.bot.get_channel(error_log_channel_id)

            if slugs_and_dc_ids_and_latest_chap_list:
                for slug_and_dc_ids_and_latest_chap in slugs_and_dc_ids_and_latest_chap_list:
                    if slug_and_dc_ids_and_latest_chap:
                        slug = slug_and_dc_ids_and_latest_chap["slug"]
                        title = await get_title_from_slug(slug)

                        dc_ids = slug_and_dc_ids_and_latest_chap["dc_ids"]
                        latest_chapter = slug_and_dc_ids_and_latest_chap["latest_chapter"]
                        cover_url = await get_cover_url_using_slug(slug)

                        layout_view = self.ChapterNotification(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

                        await layout_view.notification()


                        for dc_id in dc_ids:                            
                            try:
                                user = self.bot.get_user(dc_id)
                                if user is None:
                                    try:
                                        user = await self.bot.fetch_user(dc_id)
                                    except discord.NotFound:
                                        await excep_error_channel.send(f"User `{dc_id} does not exist at all.")
                                    except discord.HTTPException:
                                        await excep_error_channel.send(
                                            f"Could not fetch {dc_id}'s user info to send Notification"
                                        )   

                                await user.send(view=layout_view)
                            except discord.Forbidden:
                                await excep_error_channel.send(
                                    f"Could not DM. {user.name}'s DM is locked. DISCORD ID: `{user.id}`"
                                    )
                            except discord.NotFound:
                                await excep_error_channel.send(
                                    f"Could not send notification: User with ID `{dc_id}` not found (may have deleted their account or been banned)."
                                )
                            except discord.HTTPException:
                                await excep_error_channel.send(
                                    f"Could not fetch {dc_id}'s user info to send notification"
                                )
                            except Exception as e:
                                await excep_error_channel.send(
                                    f"Could not send notification to `{dc_id}`\nError:```{e}```"
                                )                                                                                                        
            await asyncio.sleep(3600)

                         


    """
                                            ///     AUTO COVER LINK UPDATER      ///
    """     
    async def UpdateCoverLink(self):
        await self.bot.wait_until_ready()
        while True:
            await update_cover_url()
            await asyncio.sleep(86400)



    """
                                            ///     HELPER FUNCTIONS      ///
    """     

    async def notify_users(self,dc_ids_n_slug_list,manga):            
        title = manga["title"]
        latest_chapter = dc_ids_n_slug_list["latest_chapter"]
        cover_url = manga["cover_url"]
        slug = manga["slug"]
        
        layout_view = MangaCog.ChapterNotification(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

        await layout_view.notification()
        
        dc_ids = dc_ids_n_slug_list["dc_ids"]

        for dc_id in dc_ids:                            
            try:
                user = self.bot.get_user(dc_id)                    
                if user is None:
                    try:
                        user = await self.bot.fetch_user(dc_id)
                    except discord.NotFound:
                        await print(f"User `{dc_id} does not exist at all.")
                    except discord.HTTPException:
                        await print(
                            f"Could not fetch {dc_id}'s user info to send Notification"
                        )   

                await user.send(view=layout_view)                
            except Exception as e:
                await print(
                    f"Could not send notification to `{dc_id}`\nError:```{e}```"
                ) 


    """
                                        ///     APP COMMAND ERROR HANDLER      ///
    """ 
    @search.error
    async def on_search_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error,app_commands.CommandOnCooldown):
            await interaction.response.send_message(content=f"{error}",ephemeral=True)

    @list_manga.error
    async def on_list_manga_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error,app_commands.CommandOnCooldown):
            await interaction.response.send_message(content=f"{error}",ephemeral=True)

    @add.error
    async def on_add_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error,app_commands.CommandOnCooldown):
            await interaction.response.send_message(content=f"{error}",ephemeral=True)

    @remove_manga.error
    async def on_remove_manga_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error,app_commands.CommandOnCooldown):
            await interaction.response.send_message(content=f"{error}",ephemeral=True)


#* Setup function to add MangaCog to the bot
async def setup(bot):
    await bot.add_cog(MangaCog(bot))
