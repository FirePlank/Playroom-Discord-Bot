import contextlib

import discord
from discord import app_commands
from discord.ext import commands


class Ticket(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    class TicketView(discord.ui.View):
        def __init__(self, bot):
            super().__init__()
            self.bot = bot

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
        async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Check if the user has an open ticket, if so then this is for deletion
            cursor = self.bot.db.get_cursor()
            cursor.execute(
                """
                SELECT channel_id FROM tickets
                WHERE user_id = ? AND guild_id = ?
                """,
                (interaction.user.id, interaction.guild.id),
            )
            ticket = cursor.fetchone()
            if ticket:
                channel = interaction.guild.get_channel(ticket[0])
                with contextlib.suppress(discord.HTTPException, AttributeError):
                    await channel.delete()
                cursor.execute(
                    """
                    DELETE FROM tickets
                    WHERE user_id = ? AND guild_id = ?
                    """,
                    (interaction.user.id, interaction.guild.id),
                )
                self.bot.db.get_connection().commit()
                with contextlib.suppress(discord.HTTPException):
                    return await interaction.response.edit_message(content="Ticket closed", view=None)

            guild = interaction.guild
            category_id = cursor.execute(
                """
                SELECT ticket_category_id FROM settings
                WHERE guild_id = ?
                """,
                (guild.id,),
            ).fetchone()[0]
            category = guild.get_channel(category_id)
            channel = await category.create_text_channel(interaction.user.name)
            await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
            embed = discord.Embed(
                title="Ticket",
                description="Please explain what you need help with. To close this ticket, type `/ticket close`",
                color=discord.Color.blurple(),
            )
            await channel.send(
                content=interaction.user.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True)
            )
            cursor.execute(
                """
                INSERT INTO tickets (user_id, guild_id, channel_id)
                VALUES (?, ?, ?)
                """,
                (interaction.user.id, guild.id, channel.id),
            )
            self.bot.db.get_connection().commit()
            await interaction.response.edit_message(content="Ticket created", view=None)

        @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
        async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="Action cancelled", view=None)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def category(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        """Set the ticket category"""

        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
                UPDATE settings
                SET ticket_category_id = ?
                WHERE guild_id = ?
            """,
            (category.id, interaction.guild.id),
        )
        self.bot.db.get_connection().commit()
        await interaction.response.send_message(f"Ticket category set to {category.name}", ephemeral=True)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 300, key=lambda i: (i.guild.id, i.user.id))
    async def create(self, interaction: discord.Interaction):
        """Create a ticket"""

        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            SELECT channel_id FROM tickets
            WHERE user_id = ? AND guild_id = ?
            """,
            (interaction.user.id, interaction.guild.id),
        )
        if cursor.fetchone():
            return await interaction.response.send_message(
                "You already have an open ticket. Please close it first with `/ticket close` to open a new one.",
                ephemeral=True,
            )

        # Proceed with ticket creation if no open ticket exists
        category_id = cursor.execute(
            """
            SELECT ticket_category_id FROM settings
            WHERE guild_id = ?
            """,
            (interaction.guild.id,),
        ).fetchone()[0]
        category = interaction.guild.get_channel(category_id)
        if category is None:
            return await interaction.response.send_message(
                "Ticket category not set or does not exist. Please ask an administrator to set it up.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "Do you want to create a ticket? Misuse of this command will result in a ban.",
            ephemeral=True,
            view=self.TicketView(self.bot),
        )

    @app_commands.command()
    async def close(self, interaction: discord.Interaction):
        """Close a ticket"""

        cursor = self.bot.db.get_cursor()
        cursor.execute(
            """
            SELECT channel_id FROM tickets
            WHERE user_id = ? AND guild_id = ?
            """,
            (interaction.user.id, interaction.guild.id),
        )
        ticket = cursor.fetchone()
        if ticket is None:
            return await interaction.response.send_message("You do not have an open ticket.", ephemeral=True)

        await interaction.response.send_message(
            "Are you sure you want to close the ticket?",
            ephemeral=True,
            view=self.TicketView(self.bot),
        )


async def setup(bot):
    await bot.add_cog(Ticket(bot))
