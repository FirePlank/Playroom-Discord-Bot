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

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return

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
        if before.guild is None or before.content == after.content:
            return

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

    @commands.Cog.listener()
    async def on_member_ban(self, interaction, member, reason):
        logging_channel_id = (
            self.bot.db.get_cursor()
            .execute(
                """
            SELECT logging_channel_id
            FROM settings
            WHERE guild_id = ?
        """,
                (interaction.guild.id,),
            )
            .fetchone()[0]
        )
        if logging_channel_id:
            logging_channel = self.bot.get_channel(logging_channel_id)
            embed = discord.Embed(title="Member Banned", color=discord.Color.red())
            embed.add_field(name="Member", value=member.mention, inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, interaction, member):
        logging_channel_id = (
            self.bot.db.get_cursor()
            .execute(
                """
            SELECT logging_channel_id
            FROM settings
            WHERE guild_id = ?
        """,
                (interaction.guild.id,),
            )
            .fetchone()[0]
        )
        if logging_channel_id:
            logging_channel = self.bot.get_channel(logging_channel_id)
            embed = discord.Embed(title="Member Unbanned", color=discord.Color.green())
            embed.add_field(name="Member", value=member.mention, inline=False)
            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO settings (guild_id)
            VALUES (?)
        """,
            (guild.id,),
        )
        self.bot.db.connection.commit()


async def setup(bot):
    await bot.add_cog(Logging(bot))
