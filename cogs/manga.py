from discord.ext import commands
from discord import Embed, Color, ButtonStyle, app_commands
from discord.ui import Button, View
from discord import ui
import discord
from typing import Literal
from os import getenv
import asyncio
import traceback
import random
from urllib.parse import quote


from utils.small_funcs import check_link_and_get_comick_slug 
from utils.comickparser import get_manga_info_from_comick, get_trending_manga_from_comick
from utils.coverupdater import update_cover_url
from utils.db import (
    get_manga_list_of_a_user_from_comick,
    write_info_comick,
    get_title_from_slug,
    get_cover_url_using_slug,
    is_duplicate,
    remove_manga_from_comick,
    get_manga_limit_of_a_user,
    get_manga_from_db,
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
previous_emoji = "<:previous:1457434026435547352>"
next_emoji = "<:next:1457434023344476160>"
chapter_emoji = "<:chapter:1453761149542858772>"
cursor_emoji = "<:cursor:1453762353505112097>"
paint_emoji = "<:paintpalette:1455488871730249839>"
calender_emoji = "<:calendar:1455488760778330112>"
rank_emoji = "<:rank:1455488758341304458>"
pen_emoji = "<:pen:1455488756172718213>"
checked_emoji = "<:checked:1455488754243600416>"
blueshield_emoji = "<:blueshield:1455488752205172756>"
warning_emoji = "<:warning:1455488750128861237>"
redshield_emoji = "<:accessdenied:1455488748166053909>"
sword_emoji = "<:sword:1455488745762459780>"
flower_emoji = "<:flower:1455488743627821137>"
moon_emoji = "<:moon:1455488741325144085>"
coffee_emoji = "<:coffee:1455488739181858932>"
percent_emoji = "<:percent:1455530697417560085>"
status_emoji = "<:status:1455530488067526758>"
demographic_emoji = "<:demographics:1455530485634695294>"
click_emoji = "<:click:1457434566477353083>"
search_emoji = "<:research:1457434865057267858>"
pages_emoji = "<:pages:1457439201753829537>"
info_emoji = "<:info:1457442292842365213>"

status_conv_with_emoji = {1:f"Ongoing  {ongoing_emoji}", 2:f"Completed  {completed_emoji}",3:f"Cancelled  {cancelled_emoji}", 4:f"Hiatus  {hiatus_emoji}"}  
content_rating_conv = {"safe": f"Safe  {checked_emoji}","suggestive":f"Suggestive  {blueshield_emoji}","erotica":f"Erotica  {warning_emoji}","pornographic":f"Pornographic  {redshield_emoji}"}
demographic_conv_with_emoji = {1:f"Shonen  {sword_emoji}",2:f"Shoujo  {flower_emoji}",3:f"Seinen  {coffee_emoji}",4:f"Josei  {moon_emoji}",0: "None"}

#* Predefined embed messages for various bot responses
embed_messages = {
    "adding": Embed(
        title="Adding Manga",
        description="Adding the manga to your list. Please wait.",
        color=Color.light_gray(),
    ),
    "added": Embed(
        title="Manga Added",
        description="The manga has been added successfully.",
        color=Color.green(),
    ),
    "400": Embed(
        title="Invalid Link",
        description="That link appears to be malformed. Please check it and try again.",
        color=Color.red(),
    ),
    "401": Embed(
        title="Unauthorized",
        description="Access was denied. Authentication may be missing or invalid.",
        color=Color.red(),
    ),
    "403": Embed(
        title="Access Forbidden",
        description="This page is restricted and cannot be accessed.",
        color=Color.red(),
    ),
    "404": Embed(
        title="Page Not Found",
        description="No page was found at that address.",
        color=Color.red(),
    ),
    "not_comick": Embed(
        title="Unsupported Source",
        description="Only manga links from Comick are supported.",
        color=Color.red(),
    ),
    "else": Embed(
        title="Unexpected Error",
        description="Something went wrong while processing your request.",
        color=Color.red(),
    ),
    "command_options": Embed(
        title="Available Commands",
        description="Choose one of the following options:",
        color=Color.light_gray(),
    ).add_field(
        name="Commands",
        value="`add`, `remove`, `list`, `search`",
    ),
    "no_link": Embed(
        title="Missing Link",
        description="No link was provided. Please include a manga link.",
        color=Color.orange(),
    ),
    "not_manga": Embed(
        title="Invalid Manga Page",
        description="The provided link does not point to a valid manga page.",
        color=Color.red(),
    ),
    "duplicate_manga": Embed(
        title="Already Added",
        description="This manga is already in your list.",
        color=Color.red(),
    ),
    "no_manga_to_show": Embed(
        title="No Manga Found",
        description="Your list is currently empty.",
        color=Color.red(),
    ),
    "all_removed": Embed(
        title="List Cleared",
        description="All manga have been removed from your list.",
        color=Color.light_gray(),
    ),
    "no_manga_to_remove": Embed(
        title="Nothing to Remove",
        description="Your list is empty. There is nothing to remove.",
        color=Color.red(),
    ),
    "max_manga_limit": Embed(
        title="Limit Reached",
        description="You have reached the maximum number of manga allowed.",
        color=Color.red(),
    ),
}


def cooldown_for_everyone_but_me(interaction: discord.Interaction):
    if interaction.user.id == 743831396874846229:
        return None

    if interaction.command.name == "search":
        return app_commands.Cooldown(rate=2,per=15)
    else:
        return app_commands.Cooldown(rate=2,per=5)




#* MangaCog class for manga management commands
@app_commands.user_install()
class MangaCog(commands.GroupCog, name="manga", description="Manga management"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self): 
        asyncio.create_task(self.check_feed_comick())
        asyncio.create_task(self.UpdateCoverLink())


#*                                       ///     SLASH COMMANDS (SEARCH,ADD,REMOVE,LIST)     ///
    """
                                            ///     SLASH COMMANDS    ///
    """


    @app_commands.command(name="search",description="Search Comick.io for manga with optional filters")
    @app_commands.describe(
    title="Manga title or keywords to search on Comick.io",
    status="Publication status filter (default: all statuses)",
    demographic="Target demographic filter (default: all demographics)",
    content_rating="Content rating filter (default: Safe and Suggestive)",
    limit="Number of results to return per request (default: 15)")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def search(
                self,
                interaction: discord.Interaction,
                title: str,
                status: Literal["Ongoing","Completed","Cancelled","Hiatus"] = None,
                demographic: Literal["Shounen","Shoujo","Seinen","Josei"] = None,
                content_rating: Literal["All","Safe","Suggestive","Erotica"] = None,
                limit: Literal[5,10,15,20] = 15,
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

        await interaction.response.defer()
        
        manga_list = await get_comick_search_result(params)        

        if manga_list:       
                manga_list.sort(key=lambda manga: manga["followers"],reverse=True)     
                view = SearchResultView(manga_dicts=manga_list,dc_id=interaction.user.id,source="comick",limit=3,searched_name=title,bot=self.bot)
                await view.render_page()            
                await interaction.followup.send(view=view)  
        else:
            await interaction.followup.send(content="No results found for your search.")



    @app_commands.command(name="trending",description="View the latest trending manga, manhwa or manhua")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.describe(
        day="Trending time range in days",
        comic_types="Filter by comic type (Default: All)",
        mature_content="Include mature titles or not (Default: False)"
    )    
    async def trending(
        self,
        interaction: discord.Interaction,
        day: Literal[7,30,90,180,270,360,720] = 0,
        comic_types: Literal["All","Manga","Manhwa","Manhua"]="All",
        mature_content: Literal["True","False"] = "false"):
        
        await interaction.response.defer()
        
        base_days = ["7","30","90"]
        if str(day) != "0" and (str(day) not in base_days):            
            base_days.append(str(day))        

        params= {
            "type": "trending",
            "accept_mature_content": str(mature_content).lower()
                }
        if day != 0:
            if day in [7,30,90]:
                params["day"] = 180
            else:
                params["day"] = day
        if comic_types != "All":            
            params["comic_types"] = comic_types.lower()
        
        success, manga_list = await get_trending_manga_from_comick(params,chosen_day=day)

        if success:
            view =  TrendingView(manga_list,interaction.user.id,limit=3,bot=self.bot,base_days=base_days,chosen_day=str(day if day != 0 else 7))
            await view.render_page()
            await interaction.followup.send(view=view)
        if not success:
            await interaction.followup.send("Couldnt search")
                              



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
    @app_commands.command(name="remove", description="Remove manga from your list")
    @app_commands.describe(title="Select a manga to remove from autocomplete",mode="Select whether to remove selected manga or all")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def remove_manga(
        self,
        interaction: discord.Interaction,
        title: str = None,
        mode: Literal["Selection menu", "Remove All"] = None,
        ):
        if mode and title:
            await interaction.response.send_message("Select either `title` or `mode` not both",ephemeral=True)            
        elif mode:
            mode_conv = {"selection menu": "select","remove all": "all"}
            await self.remove_comick(interaction,mode=mode_conv[mode.lower()])
        elif title:
            await self.remove_comick(interaction,slug=title)            
        elif (not mode) and (not title):
            await interaction.response.send_message("Select a manga or choose a removal method",ephemeral=True)
 
 
    @remove_manga.autocomplete("title")
    async def title_autocomplete(self,interaction: discord.Interaction,current: str):
        manga_dicts = await get_manga_list_of_a_user_from_comick(interaction.user.id)
        if not manga_dicts:
            return []
        choice_list = []
        
        for manga in manga_dicts:
            if len(choice_list) >= 25:
                break
            elif current.lower() in str(manga["title"]).lower():
                choice_list.append(app_commands.Choice(name=manga["title"],value=manga["slug"]))
        return choice_list



#*                                       ///     COMICK.IO CODES     ///
    """
                                            ///     COMICK      ///
    """     

    #* comick manga add function
    async def add_comick(self,interaction: discord.Interaction,link):
        all_manga = await get_manga_list_of_a_user_from_comick(interaction.user.id)
        limit = await get_manga_limit_of_a_user(interaction.user.id)
        
        #* checks if the given link is valid or not.
        await interaction.response.send_message(embed=embed_messages["adding"],delete_after=120)
        status, slug = await check_link_and_get_comick_slug(link)
        msg = await interaction.original_response()

        if status == 200:            
            #* checks if it is already in the list or not and then add it if not in list
            if not await is_duplicate("comick",interaction.user.id, slug):    
                if all_manga and limit and len(all_manga) >= limit:
                    await msg.edit(content=f"Current limit: **{limit}**",embed=embed_messages["max_manga_limit"])
                    return
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
                        title="Data Fetch Failed",
                        description="I couldn't retrieve the data. Please check and try again",
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



    async def list_comick(self,interaction: discord.Interaction,mode):

        #* checks if user has manga in list if not then return with a no manga msg
        dc_id = interaction.user.id
        manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)
        if manga_dicts == []:
            await interaction.response.send_message(
                embed=embed_messages["no_manga_to_show"],delete_after=120
            )
            return

        #* shows manga in compact mode
        if mode == "Compact":
            name = interaction.user.display_name

            layout_view = CompactMangaView(limit=5,manga_dicts=manga_dicts,dc_id=dc_id,name=name,source="comick")

            await layout_view.render_page()
          
            await interaction.response.send_message(view=layout_view)

        #* shows manga in detailed mode
        elif mode == "Detailed":
            layout_view = SingleMangaView(manga_dicts, dc_id, "comick")        

            await layout_view.render_page()
            
            await interaction.response.send_message(view=layout_view)



    async def remove_comick(self,interaction: discord.Interaction,slug:str=None, mode: str=None):        
        dc_id = interaction.user.id
        if slug:
            manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)
            if not manga_dicts:
                await interaction.response.send_message(embed=embed_messages["no_manga_to_remove"],delete_after=100)
                return
            for manga in manga_dicts:
                if manga["slug"] == slug:
                    await remove_manga_from_comick(dc_id,slug)                                           
                    await interaction.response.send_message(content=f"**{manga['title']}** has been removed from your list." ,delete_after=100)
        elif mode.lower() == "select":
            manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)

            if manga_dicts == []:
                await interaction.response.send_message(
                    embed=embed_messages["no_manga_to_remove"],
                    delete_after=100
                )
                return

            display_name = interaction.user.display_name

            layout_view = RemoveMangaView(limit=3,manga_dicts=manga_dicts,dc_id=dc_id,name=display_name,source="comick")
            await layout_view.render_page()

            await interaction.response.send_message(view=layout_view)

        elif mode.lower() == "all":            
            manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)
            if manga_dicts == []:
                await interaction.response.send_message(
                    embed=embed_messages["no_manga_to_remove"],
                    delete_after=100
                )
                return            
            embed_confirmation = Embed(
                title="⚠️ Confirm Deletion",
                description="You are about to delete **all** manga from your list. This action cannot be undone.\n\nDo you want to proceed?",
                color=Color.red(),
            )

            view_confirmation = View()

            #* Callback for proceeding with removal of all manga
            async def remove_all_manga(interaction: discord.Interaction):
                if interaction.user.id != dc_id:
                    await interaction.response.send_message(
                        "This button belongs to someone else. Please use your own.",
                        ephemeral=True, delete_after=20
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
            async def cancel_remove_manga(interaction: discord.Interaction):
                if interaction.user.id != dc_id:
                    await interaction.response.send_message(
                        "This button belongs to someone else. Please use your own.",
                        ephemeral=True, delete_after=20
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



#*                                          ///     FEED CHECKER     ///
    """
                                            ///     FEED CHECKER      ///
    """     

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

                        layout_view = ChapterNotificationView(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

                        await layout_view.render_view()


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
                            await asyncio.sleep(0.5)                                                                                                     
                        await asyncio.sleep(1)                         
            await asyncio.sleep(3600)

                         

#*                                          ///     AUTO COVER LINK UPDATER     ///
    """
                                            ///     AUTO COVER LINK UPDATER      ///
    """     
    async def UpdateCoverLink(self):
        await self.bot.wait_until_ready()
        while True:
            await update_cover_url()
            await asyncio.sleep(86400)



#*                                          ///     HELPER FUNCTIONS     ///
    """
                                            ///     HELPER FUNCTIONS      ///
    """     

    async def notify_users(self,dc_ids_n_slug_list,manga):            
        title = manga["title"]
        latest_chapter = dc_ids_n_slug_list["latest_chapter"]
        cover_url = manga["cover_url"]
        slug = manga["slug"]
        
        layout_view = ChapterNotificationView(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

        await layout_view.render_view()
        
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



#*                                          ///     APP COMMAND ERROR HANDLER     ///
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



#*                                          ///     LAYOUTVIEW CLASSES     ///
    """
                                            ///     LAYOUTVIEW CLASSES      ///
    """


class PageJumpModal(ui.Modal, title="Jump to page"):
    def __init__(self, parent_view, total_page):
        super().__init__()
        self.parent_view = parent_view
        self.total_page = total_page

        self.page = ui.TextInput(
            label="Enter page number",
            placeholder=f"1–{self.total_page}",
            required=True)
        self.add_item(self.page)

    async def on_submit(self,interaction:discord.Interaction):
        try:
            page_num = int(self.page.value) - 1
            if 1 <= page_num <= self.total_page:
                self.parent_view.cur_page = page_num 
                await self.parent_view.render_page()              
                await interaction.response.edit_message(view=self.parent_view)
            elif page_num > self.total_page:
                self.parent_view.cur_page = self.total_page - 1
                await self.parent_view.render_page()              
                await interaction.response.edit_message(view=self.parent_view)
            elif page_num < 1:
                self.parent_view.cur_page = 0
                await self.parent_view.render_page()              
                await interaction.response.edit_message(view=self.parent_view)                            
        except ValueError:
            await interaction.response.send_message("Please enter a valid number." ,ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)




class TrendingView(ui.LayoutView):
    def __init__(self, manga_list, dc_id, limit: int, bot, chosen_day: str,base_days: list):
        super().__init__()
        self.manga_list = manga_list
        self.dc_id = dc_id
        self.bot = bot       
        self.base_days = base_days
        self.chosen_day = chosen_day
        self.manga_dicts = self.manga_list[self.chosen_day]
        self.limit_per_page = limit
        self.cur_page = 0
        self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

    #* Generate embed for current manga page
    async def render_page(self):
        self.clear_items()

        self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

        start_index = self.limit_per_page * self.cur_page
        last_index = start_index + self.limit_per_page            

        container = ui.Container()
        

        for idx, manga in enumerate(self.manga_dicts[start_index:last_index],start=0):            
            demographic = demographic_conv_with_emoji[int(manga["demographic"])]
            content_rating = content_rating_conv[manga["content_rating"]]

            section = ui.Section(
                ui.TextDisplay(f"### {manga['title']}\n{demographic}  **•**  {content_rating}"),
                accessory=ui.Thumbnail(manga["cover_url"])
            )

            container.add_item(section)
            
            custom_id_1 = f"{self.cur_page * self.limit_per_page + idx}_{len(self.manga_dicts[start_index:last_index])}"
            custom_id_2 = f"{self.cur_page * self.limit_per_page + idx}.{len(self.manga_dicts[start_index:last_index])}"

            add_button = Button(label="Add",emoji=bookmark_emoji,style=ButtonStyle.secondary,custom_id=custom_id_1)
            add_button.callback = self.add_manga

            detail_button = Button(label="Details",emoji=info_emoji,style=ButtonStyle.secondary,custom_id=custom_id_2) 
            detail_button.callback = self.detail_manga
            
            slug_for_link = quote(manga["slug"],safe="")            
            web_view_button = Button(label="Open on web",style=ButtonStyle.url,url=f"https://comick.dev/comic/{slug_for_link}")
            section_buttons_row = ui.ActionRow()

            section_buttons_row.add_item(add_button)
            section_buttons_row.add_item(detail_button)
            section_buttons_row.add_item(web_view_button)
            container.add_item(section_buttons_row)

            if idx != (len(self.manga_dicts[start_index:last_index])- 1):
                container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small)) 


            
        buttons_row = ui.ActionRow()

        previous_button = Button(emoji=previous_emoji, style=ButtonStyle.secondary)
        previous_button.callback = self.previous_page

        next_button = Button(emoji=next_emoji, style=ButtonStyle.secondary)
        next_button.callback = self.next_page

        footer_button = Button(label=f"Page {self.cur_page+1} of {self.total_page}",style=ButtonStyle.secondary,disabled=True)
        
        page_navigate_row = ui.ActionRow()
        page_navigate_select = ui.Select(placeholder="Jump to page")
        
        for i in range(self.total_page):
            if i == self.cur_page:      
                page_navigate_select.append_option(discord.SelectOption(label=f"Page {i + 1}",value=str(i),emoji=pages_emoji,default=True))
            elif i != self.cur_page:
                page_navigate_select.append_option(discord.SelectOption(label=f"Page {i + 1}",value=str(i)))
                                
        page_navigate_select.callback = self.go_to_page

        days_navigate_row = ui.ActionRow()
        days_navigate_select = ui.Select(placeholder=f"Last {self.chosen_day} days")
                
        for day in self.base_days:
            if int(day) == int(self.chosen_day):
                days_navigate_select.append_option(discord.SelectOption(label=f"Last {day} days",value=str(day),emoji=calender_emoji,default=True))
            elif int(day) != int(self.chosen_day):
                days_navigate_select.append_option(discord.SelectOption(label=f"Last {day} days",value=str(day)))
            
                                
        days_navigate_select.callback = self.days_navigate

        buttons_row.add_item(previous_button)
        buttons_row.add_item(footer_button)
        buttons_row.add_item(next_button)
        page_navigate_row.add_item(page_navigate_select)
        days_navigate_row.add_item(days_navigate_select)

        self.add_item(container)
        self.add_item(buttons_row)
        self.add_item(page_navigate_row)
        self.add_item(days_navigate_row)


    async def detail_manga(self,interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True
            )
            return
        custom_id, total_manga = str(interaction.data['custom_id']).split(".")
        custom_id = int(custom_id)

        slug = self.manga_dicts[custom_id]["slug"] 
        title = self.manga_dicts[custom_id]["title"]

        followup_1 = await interaction.followup.send(content=f"Fetching **{title}**'s information...",wait=True,ephemeral=True)
        
        manga = await get_manga_from_db(slug)
        if not manga:
            success, manga = await get_manga_info_from_comick(slug)
        detail_view = SingleMangaView(manga_dicts=[manga],dc_id=interaction.user.id,source="comick",is_user_list=False)
        await detail_view.render_page()
        await followup_1.edit(content=None,view=detail_view)
        # await interaction.followup.send(view=detail_view,ephemeral=True)    

    async def days_navigate(self,interaction: discord.Interaction):        
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        day = interaction.data["values"][0]
        self.chosen_day = day
        self.manga_dicts = self.manga_list[self.chosen_day]
        self.cur_page = 0

        await self.render_page()
        await interaction.response.edit_message(view=self)



    async def go_to_page(self,interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        page_num = int(interaction.data["values"][0])
        self.cur_page = page_num

        await self.render_page()
        await interaction.response.edit_message(view=self)


    async def add_manga(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        custom_id, total_manga = str(interaction.data['custom_id']).split("_")
        custom_id = int(custom_id)
        
        
        title = self.manga_dicts[custom_id]["title"]
        slug = self.manga_dicts[custom_id]["slug"]        
        

        #* checks if it is already in the list or not and then add it if not in list
        followup = await interaction.followup.send(content=f"**{title}**",embed=embed_messages["adding"],wait=True,ephemeral=True)
        await followup.delete(delay=30)
        

        if not await is_duplicate("comick",interaction.user.id, slug):    
            all_manga = await get_manga_list_of_a_user_from_comick(interaction.user.id)
            limit = await get_manga_limit_of_a_user(interaction.user.id)
            if all_manga and limit and len(all_manga) >= limit:
                await followup.edit(content=f"Current limit: **{limit}**",embed=embed_messages["max_manga_limit"])
                return
            success, manga = await get_manga_info_from_comick(slug)                
            if success and isinstance(manga,dict):                 
                await write_info_comick(dc_id=interaction.user.id, manga=manga)
                
                await followup.edit(content=f"**{title}**",embed=embed_messages["added"])
                
                dc_ids_n_slug = await has_new_chapter(manga=manga)
                if dc_ids_n_slug:
                    await self.notify_users(dc_ids_n_slug,manga)
            else:
                #* sends error msg in chat
                embed = Embed(
                    title="Data Fetch Failed",
                    description="I tried, but the data will not come. Try again later",
                    color=Color.red(),
                )
                await followup.edit(embed=embed)                              
        else:            
            await followup.edit(embed=embed_messages["duplicate_manga"])


    async def notify_users(self,dc_ids_n_slug_list,manga):            
        title = manga["title"]
        latest_chapter = dc_ids_n_slug_list["latest_chapter"]
        cover_url = manga["cover_url"]
        slug = manga["slug"]
        
        layout_view = ChapterNotificationView(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

        await layout_view.render_view()
        
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

    
    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        

        if (self.cur_page + 1) == self.total_page:
            self.cur_page = 0

            await self.render_page()
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page += 1

            await self.render_page()
            await interaction.response.edit_message(view=self)

    #* Go to previous manga page
    async def previous_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return


        if (self.cur_page) == 0:
            self.cur_page = self.total_page - 1

            await self.render_page()                
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page -= 1

            await self.render_page()
            await interaction.response.edit_message(view=self)



class SingleMangaView(ui.LayoutView):
    def __init__(self, manga_dicts: list, dc_id: int, source: str, is_user_list = True):
        super().__init__()
        self.manga_dicts = manga_dicts
        self.dc_id = dc_id
        self.cur_page = 0
        self.source = source
        self.is_user_list = is_user_list

    #* Generate embed for current manga page
    async def render_page(self):
        num = self.cur_page
        manga_dict = self.manga_dicts[num]
        demographic = demographic_conv_with_emoji[int(manga_dict["demographic"])]
        short_desc = f"{manga_dict["description"][:2000]}..." if len(manga_dict["description"]) > 2000 else manga_dict["description"]

        self.clear_items()

        container = ui.Container()
        title = ui.TextDisplay(f"# {manga_dict['title']}")
        title_separator = ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small)
        text_section = ui.Section(accessory=ui.Thumbnail(manga_dict["cover_url"]))
               
        infos_1 = ui.TextDisplay(
        f"**Author**: {manga_dict["authors"]}   **•**   **Artist**: {manga_dict["artists"]}\n**Status**: {status_conv_with_emoji[int(manga_dict["status"])]}   **•**   **Latest Ch**: {manga_dict["latest_chapter"]}  {chapter_emoji}")

        infos_2 = ui.TextDisplay(
        f"**Rating**: {float(manga_dict["bayesian_rating"]):.2f}      **•**   **Demographic**: {demographic}\n**Started**: {manga_dict["start_year"]}   **•**   **Content**: {content_rating_conv[manga_dict["content_rating"]]}")

        desc_textdisplay = ui.TextDisplay(short_desc)

        buttons_row = ui.ActionRow()

        previous_button = Button(emoji=previous_emoji, style=ButtonStyle.secondary)
        previous_button.callback = self.previous_manga
        
        footer_button = Button(label=f"Manga {self.cur_page + 1} of {len(self.manga_dicts)}",style=ButtonStyle.blurple)
        footer_button.callback = self.send_page_modal


        next_button = Button(emoji=next_emoji, style=ButtonStyle.secondary)
        next_button.callback = self.next_manga

        remove_button = Button(emoji=bin_emoji, style=ButtonStyle.danger)
        remove_button.callback = self.remove_manga
        slug_for_link = quote(manga_dict["slug"],safe="")            
        web_view_button = Button(label="Open on web",style=ButtonStyle.url,url=f"https://comick.dev/comic/{slug_for_link}")

        if len(self.manga_dicts) <= 25: 
            navigate_row = ui.ActionRow()        
            navigate_select = ui.Select(placeholder=f"{manga_dict['title']}")
            for idx, manga in enumerate(self.manga_dicts[:25],start=0):            
                if idx == self.cur_page:
                    navigate_select.append_option(discord.SelectOption(label=f"{manga["title"][:99]}",value=str(idx),emoji=pages_emoji,default=True))
                else:
                    navigate_select.append_option(discord.SelectOption(label=f"{manga["title"][:99]}",value=str(idx)))
            navigate_select.callback = self.go_to_page
            navigate_row.add_item(navigate_select)
        
        
        text_section.add_item(infos_1)
        text_section.add_item(infos_2)
        if len(self.manga_dicts) > 1:
            buttons_row.add_item(previous_button)
            buttons_row.add_item(next_button)
            buttons_row.add_item(footer_button)
        buttons_row.add_item(web_view_button)
        if self.is_user_list:
            buttons_row.add_item(remove_button)

        container.add_item(title)
        container.add_item(title_separator)
        container.add_item(text_section)        
        container.add_item(desc_textdisplay)

        self.add_item(container)
        self.add_item(buttons_row)
        if 25 >= len(self.manga_dicts) > 2:
            self.add_item(navigate_row)


    async def send_page_modal(self,interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        total_page = len(self.manga_dicts)
        await interaction.response.send_modal(PageJumpModal(self,total_page))


    async def go_to_page(self,interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        page_num = int(interaction.data["values"][0])
        self.cur_page = page_num

        await self.render_page()
        await interaction.response.edit_message(view=self)

    #* Remove manga from user's list
    async def remove_manga(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return

        await remove_manga_from_comick(self.dc_id, self.manga_dicts[(self.cur_page)]["slug"])

        
        title = self.manga_dicts[self.cur_page]["title"]
        del self.manga_dicts[self.cur_page]
        if len(self.manga_dicts) == 0:
            self.clear_items()
            self.add_item(ui.TextDisplay("All manga have been removed from your list."))
            await interaction.response.edit_message(view=self)
            followup = await interaction.followup.send(f"The manga **{title}** has been removed.", ephemeral=True,wait=True)
            await followup.delete(delay=20)
        else:
            self.cur_page -= 1
            await self.next_manga(interaction)
            followup = await interaction.followup.send(
                f"The manga **{title}** has been removed.",
                ephemeral=True, wait= True
            )
            await followup.delete(delay=20)

    #* Go to previous manga in the list
    async def previous_manga(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        total_page = len(self.manga_dicts)


        if (self.cur_page) == 0:
            self.cur_page = total_page - 1            
            await self.render_page()
            
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page -= 1
            await self.render_page()
            
            await interaction.response.edit_message(view=self)

    #* Go to next manga in the list
    async def next_manga(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        total_page = len(self.manga_dicts)

        if (self.cur_page + 1) == total_page:
            self.cur_page = 0            
            await self.render_page()
            
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page += 1
            await self.render_page()
            
            await interaction.response.edit_message(view=self)


class CompactMangaView(ui.LayoutView):
    def __init__(self, manga_dicts: list, dc_id: int, name: str, source: str ,limit: int):
        super().__init__()
        self.manga_dicts = manga_dicts
        self.name = name
        self.source = source
        self.dc_id = dc_id

        self.limit_per_page = limit
        self.cur_page = 0
        self.total_page = ((len(manga_dicts) - 1) // self.limit_per_page) + 1

    #* Generate embed for current manga page
    async def render_page(self):
        self.clear_items()

        start_index = self.limit_per_page * self.cur_page
        last_index = start_index + self.limit_per_page            

        container = ui.Container()

        container.add_item(ui.TextDisplay(f"## {self.name}  **•**  {len(self.manga_dicts)} Manga"))
        container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))
        
        for idx, manga in enumerate(self.manga_dicts[start_index:last_index],start=0):
            section = ui.Section(
                ui.TextDisplay(f"### {manga['title']}\n**Author**: {manga["authors"]}\n**Last Ch**:  {manga["latest_chapter"]}   {chapter_emoji}\n**Status**: {status_conv_with_emoji[int(manga["status"])]}"),
                accessory=ui.Thumbnail(manga["cover_url"])
            )
            container.add_item(section)

            if idx != (len(self.manga_dicts[start_index:last_index]) - 1):
                container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))                        

        
        buttons_row = ui.ActionRow()

        previous_button = Button(emoji=previous_emoji, style=ButtonStyle.secondary)
        previous_button.callback = self.previous_page

        next_button = Button(emoji=next_emoji, style=ButtonStyle.secondary)
        next_button.callback = self.next_page
                
        footer_button = Button(label=f"Manga {self.cur_page + 1} of {self.total_page}",style=ButtonStyle.blurple)
        footer_button.callback = self.send_page_modal
    
        if 25 >= self.total_page > 2:    
            navigate_row = ui.ActionRow()
            navigate_select = ui.Select(placeholder="Jump to page")        
            for page_num in range(self.total_page):
                if page_num == self.cur_page:
                    navigate_select.append_option(discord.SelectOption(label=f"Page {page_num + 1}",value=str(page_num),emoji=pages_emoji,default=True))
                else:
                    navigate_select.append_option(discord.SelectOption(label=f"Page {page_num + 1}",value=str(page_num)))
                                    
            navigate_select.callback = self.go_to_page

        buttons_row.add_item(previous_button)
        buttons_row.add_item(next_button)
        buttons_row.add_item(footer_button)
        navigate_row.add_item(navigate_select)

        self.add_item(container)
        if self.total_page > 1:
            self.add_item(buttons_row)
        if 25 >= self.total_page > 2:    
            self.add_item(navigate_row)
    

    async def send_page_modal(self,interaction: discord.Interaction):        
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        await interaction.response.send_modal(PageJumpModal(self,self.total_page))

    async def go_to_page(self,interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        page_num = int(interaction.data["values"][0])
        self.cur_page = page_num

        await self.render_page()
        await interaction.response.edit_message(view=self)


    #* Go to next manga in the list
    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        

        if (self.cur_page + 1) == self.total_page:
            self.cur_page = 0

            await self.render_page()
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page += 1

            await self.render_page()
            await interaction.response.edit_message(view=self)

    #* Go to previous manga page
    async def previous_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return


        if (self.cur_page) == 0:
            self.cur_page = self.total_page - 1

            await self.render_page()                
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page -= 1

            await self.render_page()
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
    async def render_page(self):
        self.clear_items()

        self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

        start_index = self.limit_per_page * self.cur_page
        last_index = start_index + self.limit_per_page            

        container = ui.Container()

        container.add_item(ui.TextDisplay(f"## {self.name}   •   {len(self.manga_dicts)} Manga"))
        container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))

        for idx, manga in enumerate(self.manga_dicts[start_index:last_index],start=0):
            section = ui.Section(
                ui.TextDisplay(f"### {manga['title']}\n**Author**: {manga['authors']}\n**Last Ch**:  {manga['latest_chapter']}   {chapter_emoji}\n**Status**: {status_conv_with_emoji[int(manga['status'])]}"),
                accessory=ui.Thumbnail(manga["cover_url"])
            )
            container.add_item(section)
            
            custom_id = f"{self.cur_page * self.limit_per_page + idx}_{len(self.manga_dicts[start_index:last_index])}"
            remove_button = Button(label="Remove",style=ButtonStyle.gray,custom_id=custom_id)
            remove_button.callback = self.remove_manga

            remove_button_row = ui.ActionRow().add_item(remove_button)

            container.add_item(remove_button_row)

            if idx != (len(self.manga_dicts[start_index:last_index]) - 1):
                container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small))  


        footer_button = Button(label=f"Page {self.cur_page+1} of {self.total_page}",style=ButtonStyle.secondary,disabled=True)

    
        navigate_row = ui.ActionRow()
        navigate_select = ui.Select(placeholder="Jump to page",)
        
        for page_num in range(self.total_page):
            if page_num == self.cur_page:
                navigate_select.append_option(discord.SelectOption(label=f"Page {page_num + 1}",value=str(page_num),emoji=pages_emoji,default=True))
            else:
                navigate_select.append_option(discord.SelectOption(label=f"Page {page_num + 1}",value=str(page_num)))
                                
        navigate_select.callback = self.go_to_page

        
        buttons_row = ui.ActionRow()

        previous_button = Button(emoji=previous_emoji, style=ButtonStyle.secondary)
        previous_button.callback = self.previous_page

        next_button = Button(emoji=next_emoji, style=ButtonStyle.secondary)
        next_button.callback = self.next_page

        buttons_row.add_item(previous_button)
        buttons_row.add_item(next_button)
        buttons_row.add_item(footer_button)
        navigate_row.add_item(navigate_select)

        self.add_item(container)
        self.add_item(buttons_row)
        self.add_item(navigate_row)


    async def go_to_page(self,interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        page_num = int(interaction.data["values"][0])
        self.cur_page = page_num

        await self.render_page()
        await interaction.response.edit_message(view=self)



    async def remove_manga(self, interaction: discord.Interaction):        
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return

        custom_id, total_manga = str(interaction.data['custom_id']).split("_")
        custom_id = int(custom_id)
        total_manga = int(total_manga)
        title = self.manga_dicts[custom_id]["title"]
        

        await remove_manga_from_comick(self.dc_id, self.manga_dicts[custom_id]["slug"])
        

        del self.manga_dicts[custom_id]
        if len(self.manga_dicts) == 0:
            self.clear_items()

            self.add_item(ui.TextDisplay("All manga have been removed from your list."))
            # await interaction.response.edit_message(view=self)
            await interaction.response.edit_message(view=self)           
        else:
            
            if total_manga == 1:
                await self.previous_page(interaction)
            else:
                await self.render_page()
                # await interaction.response.edit_message(view=self)
                await interaction.response.edit_message(view=self)

        followup = await interaction.followup.send(content=f"The manga **{title}** has been removed.",ephemeral=True, wait= True)
        await followup.delete(delay=20)
    
    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        

        if (self.cur_page + 1) == self.total_page:
            self.cur_page = 0

            await self.render_page()
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page += 1

            await self.render_page()
            await interaction.response.edit_message(view=self)

    #* Go to previous manga page
    async def previous_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return


        if (self.cur_page) == 0:
            self.cur_page = self.total_page - 1

            await self.render_page()                
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page -= 1

            await self.render_page()
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
    async def render_page(self):
        self.clear_items()

        self.total_page = ((len(self.manga_dicts) - 1) // self.limit_per_page) + 1

        start_index = self.limit_per_page * self.cur_page
        last_index = start_index + self.limit_per_page            

        container = ui.Container()
        

        for idx, manga in enumerate(self.manga_dicts[start_index:last_index],start=0):
            short_desc = f"{manga["description"][:180]}..." if len(manga["description"]) > 180 else manga["description"]

            section = ui.Section(
                ui.TextDisplay(f"### {manga['title']}\n{chapter_emoji} Ch. {manga["latest_chapter"]}   **•**   {status_conv_with_emoji[int(manga["status"])]}   **•**   {star_emoji} {manga["rating"]}\n{short_desc}"),
                accessory=ui.Thumbnail(manga["cover_url"])
            )
            container.add_item(section)
            
            custom_id = f"{self.cur_page * self.limit_per_page + idx}_{len(self.manga_dicts[start_index:last_index])}"

            add_button = Button(label="Add",emoji=bookmark_emoji,style=ButtonStyle.gray,custom_id=custom_id)
            add_button.callback = self.add_manga
            slug_for_link = quote(manga["slug"],safe="")
            web_view_button = Button(label="Open on web",style=ButtonStyle.url,url=f"https://comick.dev/comic/{slug_for_link}")
            
            section_buttons_row = ui.ActionRow()

            section_buttons_row.add_item(add_button)
            section_buttons_row.add_item(web_view_button)
            container.add_item(section_buttons_row)

            if idx != (len(self.manga_dicts[start_index:last_index])- 1):
                container.add_item(ui.Separator(visible=True,spacing=discord.SeparatorSpacing.small)) 


            
        buttons_row = ui.ActionRow()

        previous_button = Button(emoji=previous_emoji, style=ButtonStyle.secondary)
        previous_button.callback = self.previous_page

        next_button = Button(emoji=next_emoji, style=ButtonStyle.secondary)
        next_button.callback = self.next_page

        footer_button = Button(label=f"Page {self.cur_page+1} of {self.total_page}",style=ButtonStyle.secondary,disabled=True)
        
        navigate_row = ui.ActionRow()
        navigate_select = ui.Select(placeholder="Jump to page",)
        
        for i in range(self.total_page):
            if i == self.cur_page:      
                navigate_select.append_option(discord.SelectOption(label=f"Page {i + 1}",value=str(i),emoji=pages_emoji,default=True))
            elif i != self.cur_page:
                navigate_select.append_option(discord.SelectOption(label=f"Page {i + 1}",value=str(i)))
                                
        navigate_select.callback = self.go_to_page

        buttons_row.add_item(previous_button)
        buttons_row.add_item(footer_button)
        buttons_row.add_item(next_button)
        navigate_row.add_item(navigate_select)

        self.add_item(container)
        self.add_item(buttons_row)
        self.add_item(navigate_row)


    async def go_to_page(self,interaction: discord.Interaction):        
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return

        page_num = int(interaction.data["values"][0])
        self.cur_page = page_num

        await self.render_page()
        await interaction.response.edit_message(view=self)


    async def add_manga(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        custom_id, total_manga = str(interaction.data['custom_id']).split("_")
        custom_id = int(custom_id)
        
        
        title = self.manga_dicts[custom_id]["title"]
        slug = self.manga_dicts[custom_id]["slug"]        
        

        #* checks if it is already in the list or not and then add it if not in list
        followup = await interaction.followup.send(content=f"**{title}**",embed=embed_messages["adding"],wait=True,ephemeral=True)
        await followup.delete(delay=30)
        

        if not await is_duplicate("comick",interaction.user.id, slug):    
            all_manga = await get_manga_list_of_a_user_from_comick(interaction.user.id)
            limit = await get_manga_limit_of_a_user(interaction.user.id)
            if all_manga and limit and len(all_manga) >= limit:
                await followup.edit(content=f"Current limit: **{limit}**",embed=embed_messages["max_manga_limit"])
                return
            success, manga = await get_manga_info_from_comick(slug)                
            if success and isinstance(manga,dict):                 
                await write_info_comick(dc_id=interaction.user.id, manga=manga)
                
                await followup.edit(content=f"**{title}**",embed=embed_messages["added"])
                
                dc_ids_n_slug = await has_new_chapter(manga=manga)
                if dc_ids_n_slug:
                    await self.notify_users(dc_ids_n_slug,manga)
            else:
                #* sends error msg in chat
                embed = Embed(
                    title="Data Fetch Failed",
                    description="I tried, but the data will not come. Try again later",
                    color=Color.red(),
                )
                await followup.edit(embed=embed)                              
        else:            
            await followup.edit(embed=embed_messages["duplicate_manga"])


    async def notify_users(self,dc_ids_n_slug_list,manga):            
        title = manga["title"]
        latest_chapter = dc_ids_n_slug_list["latest_chapter"]
        cover_url = manga["cover_url"]
        slug = manga["slug"]
        
        layout_view = ChapterNotificationView(title=title,latest_chapter=latest_chapter,cover_url=cover_url,slug=slug)

        await layout_view.render_view()
        
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

    
    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return
        

        if (self.cur_page + 1) == self.total_page:
            self.cur_page = 0

            await self.render_page()
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page += 1

            await self.render_page()
            await interaction.response.edit_message(view=self)

    #* Go to previous manga page
    async def previous_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.response.send_message(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return


        if (self.cur_page) == 0:
            self.cur_page = self.total_page - 1

            await self.render_page()                
            await interaction.response.edit_message(view=self)
        else:
            self.cur_page -= 1

            await self.render_page()
            await interaction.response.edit_message(view=self)


class ChapterNotificationView(ui.LayoutView):
    def __init__(self,title,latest_chapter,cover_url,slug):
        super().__init__()

        self.title = title
        self.latest_chapter = latest_chapter
        self.cover_url = cover_url
        self.slug = slug

    async def render_view(self):
        container = ui.Container()

        msg = random.choice(notification_templates).format(title=self.title,ch_num=self.latest_chapter)

        title = ui.TextDisplay(content=msg)
        container.add_item(title)

        cover = ui.MediaGallery(discord.MediaGalleryItem(self.cover_url))
        container.add_item(cover)

        self.add_item(container)

        button_row = ui.ActionRow()
        slug_for_link = quote(self.slug,safe="")
        link_button = Button(label="Read now!", style=ButtonStyle.url, url=f"https://comick.dev/comic/{slug_for_link}")

        button_row.add_item(link_button)

        self.add_item(button_row)
        


notification_templates = [
    "### 📢 Boom! **{title}** just released chapter **{ch_num}**!",
    "### 🎉 Good news! Chapter **{ch_num}** of **{title}** is out!",
    "### 🚀 Adventure continues! **{title}** chapter **{ch_num}** is live!",
    "### Purr! **{title}** just dropped a new chapter!\nCan you believe it's chapter **{ch_num}** already?",
    "### 😎 Don't blink! Chapter **{ch_num}** of **{title}** just hit the shelves!",
    "### 🍿 Popcorn ready? **{title}** chapter **{ch_num}** is waiting for you.",
    "### 🔥 Something is new! **{title}**, chapter **{ch_num}**, is out!",
    "### ✨ The saga continues… **{title}** chapter **{ch_num}** just dropped!",
    "### ⚡ Your favorite manga **{title}** has a new chapter\n Chapter**{ch_num}** is live now!",
    "### Heads up! **{title}** just got a new chapter (**{ch_num}**).",
    "### Another one! Chapter **{ch_num}** of **{title}** is out now!",
    "### Guess what? **{title}** has released chapter **{ch_num}**!",
    "### 📖 Chapter **{ch_num}** of **{title}** is here. Happy reading!",
    "### Keep up! **{title}** chapter **{ch_num}** is live now.",
    "### Don't miss out - **{title}** chapter **{ch_num}** just dropped.",
    "### New adventure alert! **{title}** chapter **{ch_num}** is out.",
    "### **{title}** fans, rejoice! Chapter **{ch_num}** is now online.",
    "### The wait is over! Chapter **{ch_num}** of **{title}** is here.",
    "### Time to read! **{title}** chapter **{ch_num}** has arrived.",
    "### Chapter **{ch_num}** of **{title}** just landed - enjoy the story!",
    "### **{title}** Ch. **{ch_num}** is out. Enjoy!",
    "### New chapter for **{title}** is up. Chapter **{ch_num}** here we go.",
    "### Just saw that **{title}** chapter **{ch_num}** is live.",
    "### Finally! **{title}** just updated to chapter **{ch_num}**.",
    "### **{title}** update: Chapter **{ch_num}** is ready to read.",
    "### Chapter **{ch_num}** of **{title}** just dropped.",
    "### Check it out-**{title}** Ch. **{ch_num}** is out now.",
    "### **{title}** is back with chapter **{ch_num}**.",
    "### In case you missed it, **{title}** chapter **{ch_num}** is out.",    
    "### **{title}** just released chapter **{ch_num}**!",
    "### Chapter **{ch_num}** of **{title}** is out now.",
    "### New chapter of **{title}** - **{ch_num}** - is available.",
    "### **{title}**, chapter **{ch_num}**, is live! Check it out.",
    "### Time to catch up: **{title}**, chapter **{ch_num}**.",
    "### **{title}** chapter **{ch_num}** just dropped. Enjoy!",
    "### Chapter **{ch_num}** of **{title}** has arrived.",
    "### Don't miss chapter **{ch_num}** of **{title}**.",
    "### 📖 **{title}** - chapter **{ch_num}** is ready to read!",
    "### Exciting news! Chapter **{ch_num}** of **{title}** is out.",
    "### **{title}**, chapter **{ch_num}**, is now available to read.",
    "### New chapter alert: **{title}**, chapter **{ch_num}**.",
    "### Chapter **{ch_num}** of **{title}** has just been released!",
    "### Dive in! **{title}**, chapter **{ch_num}**, is live.",
    "### **{title}** chapter **{ch_num}** is up - happy reading!"    
]


#* Setup function to add MangaCog to the bot
async def setup(bot):
    await bot.add_cog(MangaCog(bot))
