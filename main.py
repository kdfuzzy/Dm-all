import os
import asyncio
import discord
from discord.ext import commands

# ================= CONFIG =================
COMMAND_PREFIX = "."
KICK_DELAY = 1.5

# User that will NEVER be kicked
EXCLUDED_USER_IDS = {1351694428527394876}
# =========================================

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ---------- BOT ----------
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        await guild.chunk()

# ================= KICKALL COMMAND =================

@bot.command(name="kickall")
async def kickall(ctx, *, reason: str = "Kicked"):
    guild = ctx.guild
    kicked = 0
    failed = 0

    await ctx.send("👢 Starting kickall...")

    for member in guild.members:
        if member.bot:
            continue
        if member.id in EXCLUDED_USER_IDS:
            continue
        if member == guild.owner:
            continue

        # Bot cannot kick users with higher or equal role
        if member.top_role >= guild.me.top_role:
            failed += 1
            continue

        try:
            await member.kick(reason=reason)
            kicked += 1
            await asyncio.sleep(KICK_DELAY)
        except Exception as e:
            print(f"Failed to kick {member}: {e}")
            failed += 1

    await ctx.send(
        f"👢 **Kickall complete**\n"
        f"✅ Kicked: `{kicked}`\n"
        f"❌ Failed: `{failed}`"
    )

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))
