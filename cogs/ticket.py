import discord
from discord import app_commands
from discord.ext import commands


class Ticket(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    class TicketView(discord.ui.View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
        async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="Tickets")
            if category is None:
                category = await guild.create_category(
                    "Tickets",
                    position=0,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        guild.me: discord.PermissionOverwrite(read_messages=True),
                    },
                )

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
            await interaction.response.edit_message(content="Ticket created", view=None)

        @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
        async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="Ticket cancelled", view=None)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 300, key=lambda i: (i.guild.id, i.user.id))
    async def create(self, interaction: discord.Interaction):
        """Create a ticket"""

        for channel in interaction.guild.text_channels:
            if channel.name == interaction.user.name:
                return await interaction.response.send_message(
                    "You already have an open ticket. Please close it first with `/ticket close` to open a new one.",
                    ephemeral=True,
                )

        await interaction.response.send_message(
            "Do you want to create a ticket? Misuse of this command will result in a ban.",
            ephemeral=True,
            view=self.TicketView(),
        )

    @app_commands.command()
    async def close(self, interaction: discord.Interaction):
        """Close a ticket"""
        if interaction.channel.category.name == "Tickets":
            await interaction.channel.delete()
            await interaction.response.send_message("Ticket closed", ephemeral=True)
        else:
            await interaction.response.send_message("This is not a ticket channel", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ticket(bot))
