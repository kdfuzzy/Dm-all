import os
import asyncio
import logging
import discord
from discord.ext import commands
from discord import app_commands

# ================== CONFIG ==================
COMMAND_PREFIX = "."
DM_DELAY = 1.7
MAX_CONCURRENT_DMS = 1

# User IDs that will NEVER be DM'd
EXCLUDED_USER_IDS = {1351694428527394876}

# Set to a guild ID for instant slash updates (recommended while testing)
# Example: SYNC_GUILD_ID = 123456789012345678
SYNC_GUILD_ID = None
# ============================================

# ---------- LOGGING ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True  # REQUIRED for prefix commands

# ---------- BOT CLASS ----------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents
        )

    async def setup_hook(self):
        # Auto-sync slash commands
        if SYNC_GUILD_ID:
            guild = discord.Object(id=SYNC_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logging.info(f"Slash commands synced to guild {SYNC_GUILD_ID}")
        else:
            await self.tree.sync()
            logging.info("Slash commands globally synced")

bot = MyBot()

# ---------- READY ----------
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        await guild.chunk()
        logging.info(f"Member cache loaded for {guild.name}")

# ---------- MASS DM CORE ----------
async def run_mass_dm(
    guild: discord.Guild,
    send_func,
    message: str,
    target_statuses: set[discord.Status]
):
    sent = 0
    failed = 0
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DMS)

    async def dm_member(member: discord.Member):
        nonlocal sent, failed

        if member.bot:
            return
        if member.id in EXCLUDED_USER_IDS:
            return
        if member.status not in target_statuses:
            return

        async with semaphore:
            try:
                await member.send(message)
                sent += 1
                await asyncio.sleep(DM_DELAY)
            except (discord.Forbidden, discord.HTTPException):
                failed += 1
            except Exception:
                failed += 1

    await send_func("📨 **Starting mass DM...**")
    await asyncio.gather(*(dm_member(m) for m in guild.members))
    await send_func(f"✅ **Done** | Sent: `{sent}` | Failed: `{failed}`")

# ================= PREFIX COMMANDS =================
# ANYONE can run these now

@bot.command(name="massdm")
async def massdm(ctx, *, message: str):
    await run_mass_dm(
        guild=ctx.guild,
        send_func=ctx.send,
        message=message,
        target_statuses={discord.Status.online, discord.Status.dnd}
    )

@bot.command(name="massdm_offline")
async def massdm_offline(ctx, *, message: str):
    await run_mass_dm(
        guild=ctx.guild,
        send_func=ctx.send,
        message=message,
        target_statuses={discord.Status.offline, discord.Status.invisible}
    )

# ================= SLASH COMMANDS =================
# ANYONE can run these now

@bot.tree.command(name="massdm", description="DM online/DND members")
@app_commands.describe(message="Message to send")
async def slash_massdm(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    async def responder(content):
        await interaction.followup.send(content, ephemeral=True)

    await run_mass_dm(
        guild=interaction.guild,
        send_func=responder,
        message=message,
        target_statuses={discord.Status.online, discord.Status.dnd}
    )

@bot.tree.command(name="massdm_offline", description="DM offline/invisible members")
@app_commands.describe(message="Message to send")
async def slash_massdm_offline(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    async def responder(content):
        await interaction.followup.send(content, ephemeral=True)

    await run_mass_dm(
        guild=interaction.guild,
        send_func=responder,
        message=message,
        target_statuses={discord.Status.offline, discord.Status.invisible}
    )

# ================= RUN BOT =================

bot.run(os.getenv("DISCORD_TOKEN"))
