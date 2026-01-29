import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

# ================= CONFIG =================
COMMAND_PREFIX = "."
DM_DELAY = 1.7

# User that will NEVER be DMed
EXCLUDED_USER_IDS = {1351694428527394876}

# OPTIONAL: put a guild ID here for INSTANT slash updates
# If None, commands sync globally (can take up to 1 hour)
SYNC_GUILD_ID = None
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
    await ctx.send("📨 Starting mass DM...")
    sent, failed = await mass_dm(
        ctx.guild.members,
        message,
        {discord.Status.online, discord.Status.dnd}
    )
    await ctx.send(f"✅ Done | Sent: `{sent}` | Failed: `{failed}`")

@bot.command(name="dmall_offline")
async def dmall_offline(ctx, *, message: str):
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
