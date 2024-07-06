import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View


class PaginationView(View):
    def __init__(self, embeds, owner_id):
        super().__init__()
        self.embeds = embeds
        self.current_page = 0
        self.owner_id = owner_id

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey, disabled=True)
    async def previous_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You do not have permission to use this button.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            for child in self.children:
                child.disabled = False
            if self.current_page == 0:
                button.disabled = True
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.send_message("You have reached the first page.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey, disabled=False)
    async def next_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You do not have permission to use this button.", ephemeral=True)
            return

        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            for child in self.children:
                child.disabled = False
            if self.current_page == len(self.embeds) - 1:
                button.disabled = True
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.send_message("You have reached the last page.", ephemeral=True)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff(interaction: discord.Interaction) -> bool:
        cursor = interaction.client.db.get_cursor()
        cursor.execute(
            """
            SELECT staff_role_id FROM settings
            WHERE guild_id = ?
            """,
            (interaction.guild.id,),
        )
        staff_role_id = cursor.fetchone()
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id[0])
            return staff_role in interaction.user.roles
        return False

    @app_commands.command()
    @commands.has_permissions(administrator=True)
    async def staff_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set the staff role"""

        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            UPDATE settings
            SET staff_role_id = ?
            WHERE guild_id = ?
            """,
            (role.id, interaction.guild.id),
        )
        self.bot.db.get_connection().commit()
        await interaction.response.send_message(f"Staff role set to {role.mention}")

    @app_commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
        """Kick a member"""

        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} has been kicked.")

    @app_commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
        """Ban a member"""

        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} has been banned.")

    @app_commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
        """Unban a member"""

        await member.unban(reason=reason)
        await interaction.response.send_message(f"{member.mention} has been unbanned.")

    @app_commands.command()
    @app_commands.check(is_staff)
    async def warn(
        self, interaction: discord.Interaction, member: discord.Member, *, reason: str, silent: bool = False
    ):
        """Warn a member"""

        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            INSERT INTO warnings (user_id, guild_id, reason)
            VALUES (?, ?, ?)
            """,
            (member.id, interaction.guild.id, reason),
        )
        self.bot.db.get_connection().commit()

        # Check if the command is not in silent mode before attempting to send a DM
        if not silent:
            try:
                await member.send(f"You have been warned in {interaction.guild.name} for '{reason}'.")
                dm_status = "A DM has been sent to the member."
            except discord.Forbidden:
                dm_status = "Could not send a DM to the member."
        else:
            dm_status = "Silent warning issued; no DM sent."

        # Send a confirmation message in the channel, including the DM status
        await interaction.response.send_message(f"{member.mention} has been warned for '{reason}'. {dm_status}")

    @app_commands.command()
    @app_commands.check(is_staff)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        """Get warnings for a member"""

        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            SELECT warning_time, reason
            FROM warnings
            WHERE user_id = ?
            AND guild_id = ?
            """,
            (member.id, interaction.guild.id),
        )
        warnings = cursor.fetchall()

        if not warnings:
            return await interaction.response.send_message(f"{member.mention} has no warnings.")

        max_warnings_per_page = 5
        embeds = []
        for i in range(0, len(warnings), max_warnings_per_page):
            embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.red())
            for warning in warnings[i : i + max_warnings_per_page]:
                embed.add_field(name=warning[0], value=warning[1], inline=False)
            embeds.append(embed)

        view = PaginationView(embeds, interaction.user.id)
        await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command()
    @app_commands.check(is_staff)
    async def clear(self, interaction: discord.Interaction, amount: int):
        """Clear messages"""

        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"{amount} messages have been cleared.")

    @app_commands.command()
    @app_commands.check(is_staff)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        """Set slowmode"""

        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Slowmode set to {seconds} seconds.")

    @app_commands.command()
    @app_commands.check(is_staff)
    async def lock(self, interaction: discord.Interaction):
        """Lock a channel"""

        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("Channel locked.")

    @app_commands.command()
    @app_commands.check(is_staff)
    async def unlock(self, interaction: discord.Interaction):
        """Unlock a channel"""

        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("Channel unlocked.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
