from discord.ext import commands
from discord import Embed, Color, ButtonStyle, app_commands
from discord.ui import Button, View
import discord
from typing import Literal
from random import choice
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
from utils.feedchecker import get_new_chapters_info



#* channel ID
error_log_channel_id = int(getenv("error_log_channel_id"))



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


#* MangaCog class for manga management commands
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
    class SingleMangaView(View):
        def __init__(self, manga_dicts, dc_id, source):
            super().__init__()
            self.manga_dicts = manga_dicts
            self.dc_id = dc_id
            self.cur_page = 1
            self.source = source

        #* Generate embed for current manga page
        async def single_manga_view(self):
            num = self.cur_page - 1
            embed_manga = Embed(title=self.manga_dicts[num]["title"])
            embed_manga.add_field(
                name="",
                value=f"**Latest Chapter**: {self.manga_dicts[num]["latest_chapter"]}\n**Authors**: {self.manga_dicts[num]["authors"]}\n**Artists**: {self.manga_dicts[num]["artists"]}\n\n{self.manga_dicts[num]["description"]}",
            )
            embed_manga.set_thumbnail(url=self.manga_dicts[num]["cover_url"])
            embed_manga.set_footer(text=f"{self.cur_page}/{len(self.manga_dicts)}")

            return embed_manga

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
                embed = await self.single_manga_view()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                self.cur_page -= 1
                await self.single_manga_view()
                embed = await self.single_manga_view()
                await interaction.response.edit_message(embed=embed, view=self)

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
                embed = await self.single_manga_view()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                self.cur_page += 1
                await self.single_manga_view()
                embed = await self.single_manga_view()
                await interaction.response.edit_message(embed=embed, view=self)

    #* View for selecting manga to remove from list
    class ToRemoveListView(View):
        def __init__(self, display_name, manga_dicts, dc_id, icon_url,source):
            super().__init__()
            self.manga_dicts = manga_dicts
            self.display_name = display_name
            self.dc_id = dc_id
            self.icon_url = icon_url
            self.source = source

        #* Generate embed for manga removal selection
        async def to_remove_list(self):
            embed = Embed(title="")
            for idx, manga in enumerate(self.manga_dicts, start=1):
                embed.add_field(
                    name=f"{idx}. {manga['title']}",
                    value="",
                    inline=False,
                )
            embed.set_footer(text="Select the number of the manga you want to remove")
            embed.set_author(
                name=f"{self.display_name}'s Manga List", icon_url=self.icon_url
            )
            return embed

        #* Add buttons for each manga in the list
        async def add_button(self):
            for num in range(len(self.manga_dicts)):
                button = Button(
                    label=f"{num+1}", custom_id=f"{num}", style=ButtonStyle.secondary
                )
                button.callback = self.on_button_click
                self.add_item(button)

        #* Callback for button click to remove selected manga
        async def on_button_click(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            
            clicked_id = int(interaction.data["custom_id"])
            title = self.manga_dicts[clicked_id]["title"]


            await remove_manga_from_comick(self.dc_id, self.manga_dicts[clicked_id]["slug"])
            
            del self.manga_dicts[clicked_id]
            await self.update_to_remove_list(interaction, title)

        #* Update embed and buttons after removal
        async def update_to_remove_list(self, interaction, title):
            if len(self.manga_dicts) == 0:
                for item in self.children:
                    self.remove_item(item)
                await interaction.response.edit_message(
                    embed=embed_messages["all_removed"], view=self
                )
                await interaction.followup.send(
                    f"Nyaa... the treat **{title}** has been removed.", ephemeral=True
                )
            else:
                new_embed = await self.to_remove_list()
                for _ in self.children:
                    self.remove_item(_)
                await self.add_button()
                await interaction.response.edit_message(embed=new_embed, view=self)
                await interaction.followup.send(f"Nyaa... the treat **{title}** has been removed.", ephemeral=True)



#*                                            ///     SLASH COMMANDS (ADD,REMOVE,LIST)     ///



    #* Slash command to add a manga to user's list
    @app_commands.command(name="add", description="Add a manga to your list")
    @app_commands.describe(link="Paste the manga comick.io URL you want to add")
    async def add(self, interaction: discord.Interaction, link: str):
        link = link.lower()
        await self.add_comick(interaction,link)

    #* Slash command to show user's manga list
    @app_commands.command(name="list", description="Show your Manga list")
    @app_commands.describe(mode="Choose how you want the list to be displayed")
    async def list_manga(self, interaction: discord.Interaction,mode: Literal["Compact", "Detailed"]):
        await self.list_comick(interaction,mode)

    #* Slash command to remove manga from user's list
    @app_commands.command(name="remove", description="Remove a manga from your list")
    @app_commands.describe(mode="Choose whether to remove selected manga or all")
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
            #* gets manga info in dict
            success, manga = await get_manga_info_from_comick(slug)
            if success and isinstance(manga,dict):
                #* checks if it is already in the list or not and then add it if not in list
                if not await is_duplicate("comick",interaction.user.id, manga["slug"]):    
                    await write_info_comick(dc_id=interaction.user.id, manga=manga)
                    await msg.edit(embed=embed_messages["added"])
                else:
                    await msg.edit(embed=embed_messages["duplicate_manga"])
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
            embed = Embed(title="")

            for idx, manga in enumerate(manga_dicts, start=1):
                embed.add_field(
                    name=f"{idx}. {manga['title']}",
                    value=f"Latest Chapter: {manga['latest_chapter']}",
                    inline=False,
                )
            embed.set_author(
                name=f"{interaction.user.display_name}'s Manga List",
                icon_url=interaction.user.display_avatar.url,)

            await interaction.response.send_message(embed=embed)

        #* shows manga in detailed mode
        elif mode == "Detailed":
            view_detailed = self.SingleMangaView(manga_dicts, dc_id, "comick")

            previous_button = Button(label="Previous", style=ButtonStyle.secondary)
            previous_button.callback = view_detailed.previous_manga

            remove_button = Button(label="Remove", style=ButtonStyle.danger)
            remove_button.callback = view_detailed.remove_manga

            next_button = Button(label="Next", style=ButtonStyle.secondary)
            next_button.callback = view_detailed.next_manga

            view_detailed.add_item(previous_button)
            view_detailed.add_item(next_button)
            view_detailed.add_item(remove_button)

            embed_single_manga = await view_detailed.single_manga_view()
            await interaction.response.send_message(
                embed=embed_single_manga, view=view_detailed
            )



    async def remove_comick(self,interaction,mode):

        if mode == "Select":
            dc_id = interaction.user.id
            display_name = interaction.user.display_name
            icon_url = interaction.user.display_avatar.url
            manga_dicts = await get_manga_list_of_a_user_from_comick(dc_id)
            if manga_dicts == []:
                await interaction.response.send_message(
                    embed=embed_messages["no_manga_to_remove"]
                )
                return

            view = self.ToRemoveListView(display_name, manga_dicts, dc_id, icon_url,source="comick")

            await view.add_button()
            embed = await view.to_remove_list()

            await interaction.response.send_message(embed=embed, view=view)

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




    #* Embed notification style 1 for new chapter
    def embed_notification_1(self, title, latest_chapter, cover_url):
        embed_notification = discord.Embed(
            title=f"Meow! **{title}** has a fresh chapter, you're now up to chapter **{latest_chapter}**!",
            color=discord.Color.orange(),
        )
        embed_notification.set_image(url=cover_url)
        return embed_notification

    #* Embed notification style 2 for new chapter
    def embed_notification_2(self, title, latest_chapter, cover_url):
        embed_notification = discord.Embed(
            title=f"Purr! {title} just dropped a new chapter!",
            description=f"Can you believe it's chapter {latest_chapter} already?",
            color=discord.Color.purple(),
        )
        embed_notification.set_image(url=cover_url)
        return embed_notification



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

                        view = View()
                        link_button = Button(label="Link", style=ButtonStyle.link, url=f"https://comick.dev/comic/{slug}")
                        view.add_item(link_button)

                        for dc_id in dc_ids:
                            embed_notification = choice(
                                [self.embed_notification_1, self.embed_notification_2]
                            )(title, latest_chapter, cover_url)
                            embed_notification.set_author(name="Comick",icon_url="https://comick.dev/_next/image?url=%2Fstatic%2Ficons%2Funicorn-64.png&w=144&q=75")
                            
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

                                await user.send(embed=embed_notification, view=view)
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
                        
                        
                        
                        
            await asyncio.sleep(1800)


    """
                                            ///     AUTO COVER LINK UPDATER      ///
    """     
    async def UpdateCoverLink(self):
        await self.bot.wait_until_ready()
        while True:
            await update_cover_url()
            await asyncio.sleep(3600)





#* Setup function to add MangaCog to the bot
async def setup(bot):
    await bot.add_cog(MangaCog(bot))
