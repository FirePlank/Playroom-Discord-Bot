import discord
from discord import app_commands
from discord.ext import commands


@app_commands.default_permissions(administrator=True)
class Logging(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the logging channel"""
        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
                UPDATE settings
                SET logging_channel_id = ?
                WHERE guild_id = ?
            """,
            (channel.id, interaction.guild.id),
        )
        self.bot.db.get_connection().commit()
        await interaction.response.send_message(f"Logging channel set to {channel.mention}")

    @app_commands.command()
    async def toggle(self, interaction: discord.Interaction, on: bool):
        """Turn logging on or off"""
        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
                UPDATE settings
                SET logging_on = ?
                WHERE guild_id = ?
            """,
            (on, interaction.guild.id),
        )
        self.bot.db.get_connection().commit()

        status = "on" if on else "off"
        await interaction.response.send_message(f"Logging turned {status}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Send an embed message to the logging channel when a message is deleted
        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            SELECT logging_channel_id
            FROM settings
            WHERE guild_id = ?
            AND logging_on = TRUE
        """,
            (message.guild.id,),
        )

        logging_channel_id = cursor.fetchone()
        if logging_channel_id:
            logging_channel = self.bot.get_channel(logging_channel_id[0])
            embed = discord.Embed(
                title="Message Deleted",
                description=f"Message by {message.author.mention} deleted in {message.channel.mention}",
                color=discord.Color.red(),
            )
            embed.add_field(name="Content", value=message.content, inline=False)
            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Send an embed message to the logging channel when a message is edited
        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            SELECT logging_channel_id
            FROM settings
            WHERE guild_id = ?
        """,
            (before.guild.id,),
        )

        logging_channel_id = cursor.fetchone()
        if logging_channel_id:
            logging_channel = self.bot.get_channel(logging_channel_id[0])
            embed = discord.Embed(
                title="Message Edited",
                description=f"Message by {before.author.mention} edited in {before.channel.mention}",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            await logging_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logging(bot))