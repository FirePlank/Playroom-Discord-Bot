import os

import discord
from discord.ext import commands
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
        print("Sucessfully synced applications commands")
        print(f"Connected as {bot.user}")

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}")
                    print(f"[ERROR] {e}")

        self.loop.create_task(self.startup())


bot = Bot()
bot.run(os.getenv("DISCORD_TOKEN"))