"""
Utility Discord bot (slash commands) built with discord.py 2.x.

Features:
  /ping                     latency check
  /poll question options    quick reaction poll (up to 10 options, "|" separated)
  /remind minutes message   DM reminder after N minutes
  /serverinfo               member count, channels, creation date
  /userinfo [member]        join date, roles, account age
  /clear amount             bulk-delete messages (needs Manage Messages)
  welcome message           greets new members in the configured channel

Setup: see README.md (create a bot on the Discord Developer Portal, put the
token in a .env file, invite the bot with the "applications.commands" scope).
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True  # required for on_member_join (enable in the dev portal too)

bot = commands.Bot(command_prefix="!", intents=intents)

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
@bot.event
async def on_ready() -> None:
    synced = await bot.tree.sync()
    log.info("Logged in as %s — %d slash commands synced", bot.user, len(synced))


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if not WELCOME_CHANNEL_ID:
        return
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        return
    embed = discord.Embed(
        title=f"Welcome, {member.display_name}!",
        description=f"Glad to have you in **{member.guild.name}**. You are member #{member.guild.member_count}.",
        color=discord.Color.green(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)


# --------------------------------------------------------------------------- #
# Slash commands
# --------------------------------------------------------------------------- #
@bot.tree.command(name="ping", description="Check the bot latency")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(f"Pong! `{bot.latency * 1000:.0f} ms`", ephemeral=True)


@bot.tree.command(name="poll", description="Create a quick poll")
@app_commands.describe(question="The question to ask", options="Options separated by | (2 to 10)")
async def poll(interaction: discord.Interaction, question: str, options: str) -> None:
    choices = [o.strip() for o in options.split("|") if o.strip()]
    if not 2 <= len(choices) <= 10:
        await interaction.response.send_message("Give between 2 and 10 options, separated by `|`.", ephemeral=True)
        return
    lines = [f"{NUMBER_EMOJIS[i]}  {choice}" for i, choice in enumerate(choices)]
    embed = discord.Embed(title=f"📊 {question}", description="\n".join(lines), color=discord.Color.blurple())
    embed.set_footer(text=f"Poll by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    for i in range(len(choices)):
        await message.add_reaction(NUMBER_EMOJIS[i])


@bot.tree.command(name="remind", description="Get a DM reminder after N minutes")
@app_commands.describe(minutes="Delay in minutes (1-1440)", message="What to remind you about")
async def remind(interaction: discord.Interaction, minutes: app_commands.Range[int, 1, 1440], message: str) -> None:
    await interaction.response.send_message(f"⏰ OK, I'll remind you in **{minutes} min**: _{message}_", ephemeral=True)

    async def _fire() -> None:
        await asyncio.sleep(minutes * 60)
        try:
            await interaction.user.send(f"⏰ Reminder: {message}")
        except discord.Forbidden:
            log.warning("Cannot DM %s (DMs closed)", interaction.user)

    asyncio.create_task(_fire())


@bot.tree.command(name="serverinfo", description="Show information about this server")
async def serverinfo(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Use this in a server.", ephemeral=True)
        return
    embed = discord.Embed(title=guild.name, color=discord.Color.gold())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Members", value=str(guild.member_count))
    embed.add_field(name="Text channels", value=str(len(guild.text_channels)))
    embed.add_field(name="Voice channels", value=str(len(guild.voice_channels)))
    embed.add_field(name="Roles", value=str(len(guild.roles)))
    embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "?")
    embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "D"))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Show information about a member")
@app_commands.describe(member="The member to inspect (default: you)")
async def userinfo(interaction: discord.Interaction, member: discord.Member | None = None) -> None:
    member = member or interaction.user  # type: ignore[assignment]
    now = datetime.now(timezone.utc)
    embed = discord.Embed(title=member.display_name, color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Account created", value=discord.utils.format_dt(member.created_at, "D"))
    embed.add_field(name="Account age", value=f"{(now - member.created_at).days} days")
    if isinstance(member, discord.Member) and member.joined_at:
        embed.add_field(name="Joined server", value=discord.utils.format_dt(member.joined_at, "D"))
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) or "None", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Delete the last N messages in this channel")
@app_commands.describe(amount="Number of messages to delete (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]) -> None:
    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("Use this in a text channel.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        msg = "You don't have permission to do that."
    else:
        log.exception("Command error", exc_info=error)
        msg = "Something went wrong. Please try again."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is missing. Copy .env.example to .env and fill it in.")
    bot.run(TOKEN, log_handler=None)
