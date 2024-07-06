import os
import sqlite3
from sqlite3 import Connection

import discord
from discord import InteractionType
from discord.app_commands import AppCommandError
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self, db_name: str = "bot.db"):
        self.connection: Connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def add_guilds(self, bot):
        for guild in bot.guilds:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO settings (guild_id)
                VALUES (?)
            """,
                (guild.id,),
            )
        self.connection.commit()

    def create_tables(self):
        self.cursor.execute(
            """
                    CREATE TABLE IF NOT EXISTS warnings (
                        user_id INTEGER,
                        warning_id INTEGER,
                        warning_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reason TEXT
                    )
        """
        )

        self.cursor.execute(
            """
                    CREATE TABLE IF NOT EXISTS settings (
                        guild_id INTEGER UNIQUE,
                        staff_role_id INTEGER,
                        logging_channel_id INTEGER,
                        ticket_category_id INTEGER
                    )
        """
        )

        self.cursor.execute(
            """
                    CREATE TABLE IF NOT EXISTS tickets (
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL
                    )
        """
        )

        self.connection.commit()

    def get_cursor(self):
        return self.cursor

    def get_connection(self):
        return self.connection


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False),
        )

    async def startup(self):
        await bot.wait_until_ready()
        await bot.tree.sync()
        self.db.add_guilds(self)
        print("Successfully synced applications commands")
        print(f"Connected as {bot.user}")

    async def setup_hook(self):
        self.tree.on_error = self.on_app_command_error
        self.db = Database()

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
