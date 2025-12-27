from discord.ext import commands
from discord import ButtonStyle, ui
import discord
from discord.ui import Button
import asyncio
from discord import app_commands
from typing import Literal
from utils.db import update_subscribscription, get_subscribers_list
from os import getenv

from utils.crollparser import get_latest_croll_news_list, get_latest_croll_news_list_from_source
from utils.malnewsparser import get_latest_mal_news_list_from_source, get_latest_mal_news_list


error_log_channel_id = int(getenv("error_log_channel_id"))


class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self): 
        asyncio.create_task(self.check_news_croll())
        asyncio.create_task(self.check_news_mal())


    class NewsView(ui.LayoutView):
        def __init__(self, news, source):
            super().__init__()
            self.news = news
            self.source = source

        async def news_cv2(self): 
                container = ui.Container()

                if self.source == "mal":
                    source_name = ui.TextDisplay(content=f"<:mal:1452372315277885462>  **MyAnimeList News**  <t:{self.news["timestamp"]}:s>")
                elif self.source == "croll":
                    source_name = ui.TextDisplay(content=f"<:croll:1452370897817047318>  **Crunchyroll News**  <t:{self.news["timestamp"]}:s>")
                
                container.add_item(source_name)

                title = ui.TextDisplay(content=f"## {self.news['title']}")
                container.add_item(title)
                container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
                
                if self.source == "mal":
                    content = ui.TextDisplay(content=self.news["description"])
                elif self.source == "croll":
                    content = ui.TextDisplay(content=self.news["content"])
                container.add_item(content)

                thumbnail = ui.MediaGallery(discord.MediaGalleryItem(self.news["image_url"]))
                container.add_item(thumbnail)

                self.add_item(container)

                action_row = ui.ActionRow()
                link_button = Button(label="View on Web", style=ButtonStyle.link, url=self.news["news_url"])
                action_row.add_item(link_button)
                
                self.add_item(action_row)




    class SingleNewsView(ui.LayoutView):
        def __init__(self, news_list, source,dc_id):
            super().__init__()
            self.news_list = news_list
            self.cur_page = 1
            self.source = source
            self.dc_id = dc_id

        #* Generate embed for current news page
        async def single_news_view(self):
            num = self.cur_page - 1

            self.clear_items()


            container = ui.Container()

            if self.source == "mal":
                source_name = ui.TextDisplay(content=f"<:mal:1452372315277885462>  **MyAnimeList News**  <t:{self.news_list[num]["timestamp"]}:s>")
            elif self.source == "croll":
                source_name = ui.TextDisplay(content=f"<:croll:1452370897817047318>  **Crunchyroll News**  <t:{self.news_list[num]["timestamp"]}:s>")
            

            title = ui.TextDisplay(content=f"## {self.news_list[num]['title']}")
            
            if self.source == "mal":
                content = ui.TextDisplay(content=self.news_list[num]["description"])
            elif self.source == "croll":
                content = ui.TextDisplay(content=self.news_list[num]["content"])

            thumbnail = ui.MediaGallery(discord.MediaGalleryItem(self.news_list[num]["image_url"]))

            buttons_row = ui.ActionRow()
            link_button = Button(label="View on Web", style=ButtonStyle.link, url=self.news_list[num]["news_url"])
            
            previous_button = Button(emoji="<:leftarrow:1453438612774326304>", style=ButtonStyle.secondary)
            previous_button.callback = self.previous_news
            

            next_button = Button(emoji="<:rightarrow:1453438615362338847>", style=ButtonStyle.secondary)
            next_button.callback = self.next_news

            footer_button = Button(label=f"{self.cur_page}/{len(self.news_list)}",style=ButtonStyle.secondary,disabled=True)
            
            navigate_row = ui.ActionRow()
            navigate_select = ui.Select(placeholder="Navigate to...",)
            
            for idx, news in enumerate(self.news_list,start=1):
                navigate_select.append_option(discord.SelectOption(label=f"Page {idx}",value=str(idx),description=news["title"][:99]))
                                    
            navigate_select.callback = self.navigate_to


            container.add_item(source_name)
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(title)
            container.add_item(content)
            container.add_item(thumbnail)        
            buttons_row.add_item(previous_button)
            buttons_row.add_item(next_button)
            buttons_row.add_item(link_button)
            buttons_row.add_item(footer_button)
            navigate_row.add_item(navigate_select)

            self.add_item(container)
            self.add_item(buttons_row)
            self.add_item(navigate_row)

        async def navigate_to(self,interaction: discord.Interaction):
            page_num = int(interaction.data["values"][0])
            self.cur_page = page_num

            await self.single_news_view()
            await interaction.response.edit_message(view=self)

        #* Go to previous news in the list
        async def previous_news(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            total_page = len(self.news_list)

            if (self.cur_page - 1) == 0:
                self.cur_page = total_page
                await self.single_news_view()
                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page -= 1
                await self.single_news_view()
                
                await interaction.response.edit_message(view=self)

        #* Go to next news in the list
        async def next_news(self, interaction):
            if interaction.user.id != self.dc_id:
                await interaction.response.send_message(
                    "Scratch! This button is not yours to play with!", ephemeral=True
                )
                return
            total_page = len(self.news_list)
            if (self.cur_page + 1) > total_page:
                self.cur_page = 1
                await self.single_news_view()
                
                await interaction.response.edit_message(view=self)
            else:
                self.cur_page += 1
                await self.single_news_view()
                
                await interaction.response.edit_message(view=self)




    @app_commands.command(name="news",description="View the latest anime news from various sources")
    @app_commands.describe(source="Select a news source")
    @app_commands.user_install()
    async def news(self, interaction: discord.Interaction,source: Literal["Crunchyroll News","MyAnimeList News"]):
        src = str(source).lower()

        await interaction.response.defer()

        if src == "crunchyroll news":
            result = await get_latest_croll_news_list_from_source()
            
            new = result["new_news"]
            news_list = result["news"]


            if news_list:
                if new:                
                    layout_view = self.SingleNewsView(news_list=news_list,source="croll",dc_id=interaction.user.id)
                    await layout_view.single_news_view()
                    
                    await interaction.followup.send(view=layout_view)
                    await self.check_news_croll(once=True)
                else:       
                    layout_view = self.SingleNewsView(news_list=news_list,source="croll",dc_id=interaction.user.id)
                    await layout_view.single_news_view()
                    
                    await interaction.followup.send(view=layout_view)
            else:
                await interaction.followup.send(content="Nyaa... something went wrong fetching the news. Try again later!")            


        elif src == "myanimelist news":
            result = await get_latest_mal_news_list_from_source()
            
            new = result["new_news"]
            news_list = result["news"]


            if news_list:
                if new:                
                    layout_view = self.SingleNewsView(news_list=news_list,source="mal",dc_id=interaction.user.id)
                    await layout_view.single_news_view()
                    
                    await interaction.followup.send(view=layout_view)
                    await self.check_news_mal(once=True)
                else:       
                    layout_view = self.SingleNewsView(news_list=news_list,source="mal",dc_id=interaction.user.id)
                    await layout_view.single_news_view()
                    
                    await interaction.followup.send(view=layout_view)
            else:
                await interaction.followup.send(content="Nyaa... something went wrong fetching the news. Try again later!")            




    @app_commands.command(name="subscribe",description="Subscribe to Anime News updates")
    @app_commands.describe(source="Select a news source")
    @app_commands.user_install()
    async def subscribe(self, interaction: discord.Interaction,source: Literal["Crunchyroll News","MyAnimeList News"]):
        src = str(source).lower()
        if src == "crunchyroll news":
            await update_subscribscription(
                dc_id=interaction.user.id,
                source="croll",
                num=1
                )
        elif src == "myanimelist news":
            await update_subscribscription(
                dc_id=interaction.user.id,
                source="mal",
                num=1
                )
        await interaction.response.send_message(
            content=f"Successfully subscribed to **{source}**\nFrom now on you will recieve news on DM.\n-# To unsubscribe do `/unsubscribe [source]`",
            ephemeral=True
            )


    @app_commands.command(name="unsubscribe",description="Unsubscribe from Anime News updates")
    @app_commands.describe(source="Select a news source")
    @app_commands.user_install()
    async def unsubscribe(self, interaction: discord.Interaction,source: Literal["Crunchyroll News","MyAnimeList News"]):
        src = str(source).lower()
        if src == "crunchyroll news":
            await update_subscribscription(
                dc_id=interaction.user.id,
                source="croll",
                num=0
                )
        elif src == "myanimelist news":
            await update_subscribscription(
                dc_id=interaction.user.id,
                source="mal",
                num=0
                )
        await interaction.response.send_message(
            content=f"Successfully unsubscribed to **{source}**\n-# To subscribe again do `/subscribe [source]`",
            ephemeral=True
            )



    async def check_news_croll(self,once=False):
        await self.bot.wait_until_ready()

        excep_error_channel = self.bot.get_channel(error_log_channel_id)
        if once:
            while True:
                #* gets news dict
                news_list = await get_latest_croll_news_list()
                if news_list:
                    for news in reversed(news_list):
                        news_view = self.NewsView(news,"croll")

                        await news_view.news_cv2()

                        dc_ids = await get_subscribers_list("croll")

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
                                            f"Could not fetch {dc_id}'s user info to send News"
                                        )                         

                                await user.send(view=news_view)
                            except discord.Forbidden:
                                await excep_error_channel.send(
                                    f"Could not DM. {user.name}'s DM is locked. DISCORD ID: `{user.id}`"
                                    )
                            except discord.NotFound:
                                await excep_error_channel.send(
                                    f"Could not send News: User with ID `{dc_id}` not found (may have deleted their account or been banned)."
                                )
                            except discord.HTTPException:
                                await excep_error_channel.send(
                                    f"Could not fetch {dc_id}'s user info to send News"
                                )
                            except Exception as e:
                                await excep_error_channel.send(
                                    f"Could not send News to `{dc_id}`\nError:```{e}```"
                                )                    
    
                await asyncio.sleep(360)
        else:
            news_list = await get_latest_croll_news_list()
            if news_list:
                for news in reversed(news_list):
                    news_view = self.NewsView(news,"croll")

                    await news_view.news_cv2()

                    dc_ids = await get_subscribers_list("croll")

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
                                        f"Could not fetch {dc_id}'s user info to send News"
                                    )                         

                            await user.send(view=news_view)
                        except discord.Forbidden:
                            await excep_error_channel.send(
                                f"Could not DM. {user.name}'s DM is locked. DISCORD ID: `{user.id}`"
                                )
                        except discord.NotFound:
                            await excep_error_channel.send(
                                f"Could not send News: User with ID `{dc_id}` not found (may have deleted their account or been banned)."
                            )
                        except discord.HTTPException:
                            await excep_error_channel.send(
                                f"Could not fetch {dc_id}'s user info to send News"
                            )
                        except Exception as e:
                            await excep_error_channel.send(
                                f"Could not send News to `{dc_id}`\nError:```{e}```"
                            )  


    async def check_news_mal(self,once=False):
        await self.bot.wait_until_ready()

        excep_error_channel = self.bot.get_channel(error_log_channel_id)
        if once:
            while True:
                news_list = await get_latest_mal_news_list()
                if news_list:
                    for news in reversed(news_list):
                        news_view = self.NewsView(news,"mal")
                        await news_view.news_cv2()

                        dc_ids = await get_subscribers_list("mal")
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
                                            f"Could not fetch {dc_id}'s user info to send News"
                                        )                         

                                await user.send(view=news_view)
                            except discord.Forbidden:
                                await excep_error_channel.send(
                                    f"Could not DM. {user.name}'s DM is locked. DISCORD ID: `{user.id}`"
                                    )
                            except discord.NotFound:
                                await excep_error_channel.send(
                                    f"Could not send News: User with ID `{dc_id}` not found (may have deleted their account or been banned)."
                                )
                            except discord.HTTPException:
                                await excep_error_channel.send(
                                    f"Could not fetch {dc_id}'s user info to send News"
                                )
                            except Exception as e:
                                await excep_error_channel.send(
                                    f"Could not send News to `{dc_id}`\nError:```{e}```"
                                )             


                
                await asyncio.sleep(360)
        else:
            news_list = await get_latest_mal_news_list()
            if news_list:
                for news in reversed(news_list):
                    news_view = self.NewsView(news,"mal")
                    await news_view.news_cv2()

                    dc_ids = await get_subscribers_list("mal")
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
                                        f"Could not fetch {dc_id}'s user info to send News"
                                    )                         

                            await user.send(view=news_view)
                        except discord.Forbidden:
                            await excep_error_channel.send(
                                f"Could not DM. {user.name}'s DM is locked. DISCORD ID: `{user.id}`"
                                )
                        except discord.NotFound:
                            await excep_error_channel.send(
                                f"Could not send News: User with ID `{dc_id}` not found (may have deleted their account or been banned)."
                            )
                        except discord.HTTPException:
                            await excep_error_channel.send(
                                f"Could not fetch {dc_id}'s user info to send News"
                            )
                        except Exception as e:
                            await excep_error_channel.send(
                                f"Could not send News to `{dc_id}`\nError:```{e}```"
                            )             


                
        

async def setup(bot):
    await bot.add_cog(NewsCog(bot))
