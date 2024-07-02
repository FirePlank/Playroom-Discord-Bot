import discord
from discord import app_commands
from discord.ext import commands


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def test(self, interaction: discord.Interaction):
        """command description"""
        await interaction.response.send_message(r"cogs \o/")


async def setup(bot):
    await bot.add_cog(Test(bot))
