from discord import app_commands, Interaction
from discord import ui
from typing import Literal
import discord
import json
from discord.ext import commands
from utils.emojis import Emojis



class EventCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot


    @app_commands.command(name="commands",description="See all the available commands")
    @app_commands.user_install()
    async def commands(self,interaction: Interaction,category: Literal["Manga","News"]="Manga"):
        with open("command_list.json","r") as f:
            commands_list = json.load(f)        
        ctgs = ["manga","news"]        

        view = CommandView(chosen_ctg=category.lower(),commands_list=commands_list,ctgs=ctgs,dc_id=interaction.user.id)
        await view.render_page()

        await interaction.response.send_message(view=view)
    



class CommandView(ui.LayoutView):
    def __init__(self,dc_id,chosen_ctg="Manga",commands_list={},ctgs=[]):
        super().__init__()
        self.chosen_ctg = chosen_ctg.lower()
        self.command_list = commands_list
        self.ctgs = ctgs
        self.dc_id = dc_id
    
    async def render_page(self):
        self.clear_items()

        container = ui.Container()
        cmd_ls = self.command_list[self.chosen_ctg.lower()]
        
        # Manga
        if self.chosen_ctg == "manga":
            manga_text_1 = ui.TextDisplay(
                content=f"## {Emojis.research} Discovery\n{cmd_ls['search']['embed']}  {cmd_ls['search']['args']}\n-# {cmd_ls['search']['desc']}\n\n{cmd_ls['trending']['embed']}  {cmd_ls['trending']['args']}\n-# {cmd_ls['trending']['desc']}"
            )

            manga_text_2 = ui.TextDisplay(
                content=f"## {Emojis.library} Library\n{cmd_ls['add']['embed']}  {cmd_ls['add']['args']}\n-# {cmd_ls['add']['desc']}\n\n{cmd_ls['remove']['embed']}  {cmd_ls['remove']['args']}\n-# {cmd_ls['remove']['desc']}\n\n{cmd_ls['list']['embed']}  {cmd_ls['list']['args']}\n-# {cmd_ls['list']['desc']}"
            )


        # News
        elif self.chosen_ctg == "news":
            news_text_1 = ui.TextDisplay(
                content=f"## {Emojis.newspaper} Animanga News\n{cmd_ls['news']['embed']}  {cmd_ls['news']['args']}\n-# {cmd_ls['news']['desc']}\n\n{cmd_ls['subscribe']['embed']}  {cmd_ls['subscribe']['args']}\n-# {cmd_ls['subscribe']['desc']}\n\n{cmd_ls['unsubscribe']['embed']}  {cmd_ls['unsubscribe']['args']}\n-# {cmd_ls['unsubscribe']['desc']}"
            )
                              

        ctg_action_row = ui.ActionRow()
        ctg_select = ui.Select()
        for ctg in self.ctgs:
            if ctg == str(self.chosen_ctg):
                if ctg == "manga":
                    ctg_select.add_option(label=ctg.capitalize(),value=ctg,default=True,emoji=Emojis.manga)
                elif ctg == "news":
                    ctg_select.add_option(label=ctg.capitalize(),value=ctg,default=True,emoji=Emojis.megaphone)
            else:
                if ctg == "manga":
                    ctg_select.add_option(label=ctg.capitalize(),value=ctg,emoji=Emojis.manga)
                elif ctg == "news":
                    ctg_select.add_option(label=ctg.capitalize(),value=ctg,emoji=Emojis.megaphone)                
        ctg_select.callback = self.go_to_ctg

        ctg_action_row.add_item(ctg_select)

        if self.chosen_ctg == "manga":
            container.add_item(manga_text_1)
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(manga_text_2)
        elif self.chosen_ctg == "news":
            container.add_item(news_text_1)

        self.add_item(container)
        self.add_item(ctg_action_row)

                
    async def go_to_ctg(self,interaction: discord.Interaction):
        if interaction.user.id != self.dc_id:
            await interaction.followup.send(
                "This button belongs to someone else. Please use your own.", ephemeral=True, delete_after=20
            )
            return        
        ctg = interaction.data["values"][0]
        self.chosen_ctg = ctg

        await self.render_page()
        await interaction.response.edit_message(view=self)



async def setup(bot):
    await bot.add_cog(EventCog(bot))