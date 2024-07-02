import os
from typing import Any

import discord
from discord import InteractionType
from discord.app_commands import AppCommandError
from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv

load_dotenv()


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False)
        )

    async def startup(self):
        await bot.wait_until_ready()
        await bot.tree.sync()
        print("Successfully synced applications commands")
        print(f"Connected as {bot.user}")

    async def setup_hook(self):
        self.tree.on_error = self.on_app_command_error
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}")
                    print(f"[ERROR] {e}")

        # noinspection PyAsyncCall
        self.loop.create_task(self.startup())

    async def on_app_command_error(self, interaction: "InteractionType", error: AppCommandError):
        await interaction.response.send_message(str(error), ephemeral=True)


bot = Bot()
bot.run(os.getenv("DISCORD_TOKEN"))
