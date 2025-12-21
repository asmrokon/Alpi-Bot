from discord.ext import commands
from discord import ButtonStyle, ui
import discord
from discord.ui import Button
import asyncio
from discord import app_commands
from typing import Literal
from utils.db import update_subscribscription, get_subscribers_list
from os import getenv

from utils.crollparser import get_latest_croll_news
from utils.malnewsparser import get_latest_mal_news


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
        
            container = ui.Container()

            if self.source == "mal":
                source_name = ui.TextDisplay(content=f"<:mal:1452372315277885462>  **MyAnimeList News**  <t:{news["timestamp"]}:s>")
            elif self.source == "croll":
                source_name = ui.TextDisplay(content=f"<:croll:1452370897817047318>  **Crunchyroll News**  <t:{news["timestamp"]}:s>")
            
            container.add_item(source_name)

            title = ui.TextDisplay(content=f"## {news['title']}")
            container.add_item(title)
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

            if self.source == "mal":
                content = ui.TextDisplay(content=news["description"])
            elif self.source == "croll":
                content = ui.TextDisplay(content=news["content"])
            container.add_item(content)

            thumbnail = ui.MediaGallery(discord.MediaGalleryItem(news["image_url"]))
            container.add_item(thumbnail)

            self.add_item(container)

            action_row = ui.ActionRow()
            link_button = Button(label="Link", style=ButtonStyle.link, url=news["news_url"])
            action_row.add_item(link_button)
            self.add_item(action_row)


    async def check_news_croll(self):
        await self.bot.wait_until_ready()

        excep_error_channel = self.bot.get_channel(error_log_channel_id)

        while True:
            #* gets news dict
            news = await get_latest_croll_news()
            if news:
                news_view = self.NewsView(news,"croll")

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
 
            await asyncio.sleep(10)

    @app_commands.command(name="subscribe",description="Subscribe to Anime News")
    @app_commands.describe(source="Choose a news source")
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


    @app_commands.command(name="unsubscribe",description="unSubscribe to Anime News")
    @app_commands.describe(source="Choose a news source")
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
            
    async def check_news_mal(self):
        await self.bot.wait_until_ready()

        excep_error_channel = self.bot.get_channel(error_log_channel_id)

        while True:
            news = await get_latest_mal_news()
            if news:
                view = self.NewsView(news,"mal")

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

                        await user.send(view=view)
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


            
            await asyncio.sleep(10)
        

async def setup(bot):
    await bot.add_cog(NewsCog(bot))
