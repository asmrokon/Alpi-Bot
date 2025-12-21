from discord.ext import commands
from os import getenv

spooks_id = int(getenv("spooks_id"))





class AdminCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    



    #* Command to reload a cog (extension) by name
    @commands.command()
    @commands.guild_only()
    async def rc(self, ctx, cog: str):
        if ctx.author.id == spooks_id:
            try:
                await self.bot.reload_extension(f"cogs.{cog}")
                await ctx.send(f"`{cog}` reloaded **successfully**! ✅")
            except Exception as e:
                await ctx.send(f"**Error** reloading `{cog}`:```\n{e}```")

    #* Command to load a cog (extension) by name
    @commands.command()
    @commands.guild_only()
    async def lc(self, ctx, cog: str):
        if ctx.author.id == spooks_id:
            try:
                await self.bot.load_extension(f"cogs.{cog}")
                await ctx.send(f"`{cog}` loaded **successfully**! ✅")
            except Exception as e:
                await ctx.send(f"**Error** loading `{cog}`:\n```{e}```")

    #* Command to unload a cog (extension) by name
    @commands.command()
    @commands.guild_only()
    async def uc(self, ctx, cog: str):
        if ctx.author.id == spooks_id:
            try:
                await self.bot.unload_extension(f"cogs.{cog}")
                await ctx.send(f"`{cog}` unloaded **successfully**! ✅")
            except Exception as e:
                await ctx.send(f"**Error** unloading `{cog}`:\n```{e}```")




async def setup(bot):
    await bot.add_cog(AdminCog(bot))