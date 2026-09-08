from os import getenv

from discord.ext import commands

from utils.db import get_manga_limit_of_a_user, update_manga_limit_of_a_user

spooks_id = int(getenv("spooks_id"))





class AdminCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    
    @commands.command()
    async def uml(self,ctx, dc_id: int, limit: int):        
        if ctx.author.id == spooks_id:            
            cur_limit = await get_manga_limit_of_a_user(dc_id=dc_id)
            await update_manga_limit_of_a_user(dc_id=dc_id,limit=limit)
            await ctx.send(f"Updated <@{dc_id}>'s manga limit from **{cur_limit}** to **{limit}**")



    #* Command to reload a cog (extension) by name
    @commands.command()
    async def rc(self, ctx, cog: str):
        if ctx.author.id == spooks_id:
            try:                
                await self.bot.reload_extension(f"cogs.{cog}")
                await ctx.send(f"`{cog}` reloaded **successfully**! ✅")
            except Exception as e:
                await ctx.send(f"**Error** reloading `{cog}`:```\n{e}```")

    #* Command to load a cog (extension) by name
    @commands.command()
    async def lc(self, ctx, cog: str):
        if ctx.author.id == spooks_id:
            try:
                await self.bot.load_extension(f"cogs.{cog}")
                await ctx.send(f"`{cog}` loaded **successfully**! ✅")
            except Exception as e:
                await ctx.send(f"**Error** loading `{cog}`:\n```{e}```")

    #* Command to unload a cog (extension) by name
    @commands.command()
    async def uc(self, ctx, cog: str):
        if ctx.author.id == spooks_id:
            try:
                await self.bot.unload_extension(f"cogs.{cog}")
                await ctx.send(f"`{cog}` unloaded **successfully**! ✅")
            except Exception as e:
                await ctx.send(f"**Error** unloading `{cog}`:\n```{e}```")




async def setup(bot):
    await bot.add_cog(AdminCog(bot))