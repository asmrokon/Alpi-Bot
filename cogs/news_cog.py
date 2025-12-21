from discord.ext import commands
from discord import Embed, Color, ButtonStyle
import discord
from datetime import datetime, timezone
from discord.ui import Button, View
import asyncio
import json
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


    async def check_news_croll(self):
        await self.bot.wait_until_ready()

        excep_error_channel = self.bot.get_channel(error_log_channel_id)

        while True:
            #* gets news dict
            news = await get_latest_croll_news()
            if news:
                news_embed = Embed(
                    title=news["title"],
                    description=f"{news['content']}",
                    color=Color.orange(),)
                news_embed.set_image(url=news["image_url"])
                news_embed.set_author(name="Crunchyroll News",icon_url="https://www.crunchyroll.com/news/img/favicons/favicon-v2-96x96.png")
                news_embed.timestamp = datetime.now(timezone.utc)

                view = View()
                link_button = Button(label="Link", style=ButtonStyle.link, url=news["news_url"])
                view.add_item(link_button)

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

                        await user.send(content=news["title"],embed=news_embed, view=view)
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

            
    async def check_news_mal(self):
        await self.bot.wait_until_ready()

        excep_error_channel = self.bot.get_channel(error_log_channel_id)

        while True:
            news = await get_latest_mal_news()
            if news:
                news_embed = Embed(
                    title=news["title"],
                    description=f"{news['description']}",
                    color=Color.blue(),)
                news_embed.set_image(url=news["image_url"])
                news_embed.set_author(name="MyAnimeList News",icon_url="https://cdn.myanimelist.net/img/sp/icon/apple-touch-icon-256.png")
                news_embed.timestamp = datetime.now(timezone.utc)

                view = View()
                link_button = Button(label="Link", style=ButtonStyle.link, url=news["news_url"])
                view.add_item(link_button)

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

                        await user.send(content=news["title"],embed=news_embed, view=view)
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
