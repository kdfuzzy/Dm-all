import os
import asyncio
import discord
from discord.ext import commands

# ================= CONFIG =================
COMMAND_PREFIX = "."
DM_DELAY = 1.7

# User that will NEVER be DMed
EXCLUDED_USER_IDS = {1351694428527394876}
# =========================================

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

# ---------- BOT ----------
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        await guild.chunk()

# ================= DM HELPERS =================

async def mass_dm(ctx, message, statuses):
    sent = 0
    failed = 0

    await ctx.send("📨 Starting mass DM...")

    for member in ctx.guild.members:
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
        except Exception as e:
            print(f"❌ Failed to DM {member}: {e}")
            failed += 1

    await ctx.send(
        f"✅ **Mass DM complete**\n"
        f"📤 Sent: `{sent}`\n"
        f"❌ Failed: `{failed}`"
    )

# ================= COMMANDS =================

@bot.command(name="dmall")
async def dmall(ctx, *, message: str):
    """DM online & DND members"""
    await mass_dm(
        ctx,
        message,
        {discord.Status.online, discord.Status.dnd}
    )

@bot.command(name="dmall_offline")
async def dmall_offline(ctx, *, message: str):
    """DM offline & invisible members"""
    await mass_dm(
        ctx,
        message,
        {discord.Status.offline, discord.Status.invisible}
    )

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))
