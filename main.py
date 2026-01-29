import os
import asyncio
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands

# ================= CONFIG =================
COMMAND_PREFIX = "."
DM_DELAY = 1.7

EXCLUDED_USER_IDS = {1351694428527394876}

# Slash command sync (set guild ID for instant sync)
SYNC_GUILD_ID = None

# WEBHOOK (LOGS)
LOG_WEBHOOK_URL = "https://discord.com/api/webhooks/1466260690858676407/RTbOvYUU9mnHa3tfsrubVU8J0g95KzeMXEybiZbhncKUCCxWd9xfCbGqNyrrHeiiEFk9"
# =========================================

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

# ---------- BOT ----------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

    async def setup_hook(self):
        if SYNC_GUILD_ID:
            guild = discord.Object(id=SYNC_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Slash commands synced to guild {SYNC_GUILD_ID}")
        else:
            await self.tree.sync()
            print("✅ Slash commands globally synced")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        await guild.chunk()

# ================= WEBHOOK LOGGER =================

async def log_to_webhook(
    user,
    guild,
    channel,
    command_name,
    content
):
    embed = {
        "title": "📨 DM Command Used",
        "color": 0x5865F2,
        "fields": [
            {"name": "User", "value": f"{user} (`{user.id}`)", "inline": False},
            {"name": "Guild", "value": f"{guild.name} (`{guild.id}`)", "inline": False},
            {"name": "Channel", "value": f"{channel.name} (`{channel.id}`)", "inline": False},
            {"name": "Command", "value": command_name, "inline": False},
            {"name": "Message", "value": content[:1024], "inline": False},
        ],
        "footer": {"text": "DM Logger"},
    }

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(LOG_WEBHOOK_URL, session=session)
        await webhook.send(embed=discord.Embed.from_dict(embed))

# ================= DM CORE =================

async def mass_dm(members, message, statuses):
    sent = 0
    failed = 0

    for member in members:
        if member.bot:
            continue
        if member.id in EXCLUDED_USER_IDS:
            continue
        if member.status not in statuses:
            continue

        try:
            await member.send(message)
            sent += 1
            await asyncio.sleep(DM_DELAY)
        except:
            failed += 1

    return sent, failed

# ================= PREFIX COMMANDS =================

@bot.command(name="dmall")
async def dmall(ctx, *, message: str):
    await log_to_webhook(
        ctx.author,
        ctx.guild,
        ctx.channel,
        ".dmall",
        message
    )

    await ctx.send("📨 Starting mass DM...")
    sent, failed = await mass_dm(
        ctx.guild.members,
        message,
        {discord.Status.online, discord.Status.dnd}
    )
    await ctx.send(f"✅ Done | Sent: `{sent}` | Failed: `{failed}`")

@bot.command(name="dmall_offline")
async def dmall_offline(ctx, *, message: str):
    await log_to_webhook(
        ctx.author,
        ctx.guild,
        ctx.channel,
        ".dmall_offline",
        message
    )

    await ctx.send("📨 Starting offline mass DM...")
    sent, failed = await mass_dm(
        ctx.guild.members,
        message,
        {discord.Status.offline, discord.Status.invisible}
    )
    await ctx.send(f"✅ Done | Sent: `{sent}` | Failed: `{failed}`")

# ================= SLASH COMMANDS =================

@bot.tree.command(name="dmall", description="DM online & DND members")
@app_commands.describe(message="Message to send")
async def slash_dmall(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    await log_to_webhook(
        interaction.user,
        interaction.guild,
        interaction.channel,
        "/dmall",
        message
    )

    sent, failed = await mass_dm(
        interaction.guild.members,
        message,
        {discord.Status.online, discord.Status.dnd}
    )

    await interaction.followup.send(
        f"✅ Done | Sent: `{sent}` | Failed: `{failed}`",
        ephemeral=True
    )

@bot.tree.command(name="dmall_offline", description="DM offline & invisible members")
@app_commands.describe(message="Message to send")
async def slash_dmall_offline(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    await log_to_webhook(
        interaction.user,
        interaction.guild,
        interaction.channel,
        "/dmall_offline",
        message
    )

    sent, failed = await mass_dm(
        interaction.guild.members,
        message,
        {discord.Status.offline, discord.Status.invisible}
    )

    await interaction.followup.send(
        f"✅ Done | Sent: `{sent}` | Failed: `{failed}`",
        ephemeral=True
    )

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))
