import os
import asyncio
import logging
import discord
from discord.ext import commands
from discord import app_commands

# ================== CONFIG ==================
COMMAND_PREFIX = "."
DM_DELAY = 1.7
KICK_DELAY = 1.5
MAX_CONCURRENT_DMS = 1

# User IDs that will NEVER be affected
EXCLUDED_USER_IDS = {1351694428527394876}

# Set this to a guild ID for instant slash command sync
# Example: SYNC_GUILD_ID = 123456789012345678
SYNC_GUILD_ID = None
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

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
            logging.info(f"Slash commands synced to guild {SYNC_GUILD_ID}")
        else:
            await self.tree.sync()
            logging.info("Slash commands globally synced")

bot = MyBot()

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        await guild.chunk()

# ================= MASS DM CORE =================
async def run_mass_dm(guild, send_func, message, target_statuses):
    sent = 0
    failed = 0
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DMS)

    async def dm_member(member):
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
            except:
                failed += 1

    await send_func("📨 Starting mass DM...")
    await asyncio.gather(*(dm_member(m) for m in guild.members))
    await send_func(f"✅ Done | Sent: `{sent}` | Failed: `{failed}`")

# ================= SLASH COMMANDS =================

@bot.tree.command(name="massdm", description="DM online/DND members")
@app_commands.describe(message="Message to send")
async def slash_massdm(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    async def responder(msg):
        await interaction.followup.send(msg, ephemeral=True)

    await run_mass_dm(
        interaction.guild,
        responder,
        message,
        {discord.Status.online, discord.Status.dnd}
    )

@bot.tree.command(name="massdm_offline", description="DM offline/invisible members")
@app_commands.describe(message="Message to send")
async def slash_massdm_offline(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)

    async def responder(msg):
        await interaction.followup.send(msg, ephemeral=True)

    await run_mass_dm(
        interaction.guild,
        responder,
        message,
        {discord.Status.offline, discord.Status.invisible}
    )

# ================= KICK ALL =================

@bot.tree.command(name="kickall", description="Kick all members")
@app_commands.describe(reason="Kick reason")
async def kickall(interaction: discord.Interaction, reason: str = "Kicked"):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    kicked = 0
    failed = 0

    try:
        for member in guild.members:
            if member.bot:
                continue
            if member.id in EXCLUDED_USER_IDS:
                continue
            if member == guild.owner:
                continue

            # Bot cannot kick users with higher/equal role
            if member.top_role >= guild.me.top_role:
                failed += 1
                continue

            try:
                await member.kick(reason=reason)
                kicked += 1
                await asyncio.sleep(KICK_DELAY)
            except:
                failed += 1

    finally:
        await interaction.followup.send(
            f"👢 Kickall complete\n"
            f"✅ Kicked: `{kicked}`\n"
            f"❌ Failed: `{failed}`",
            ephemeral=True
        )

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))
