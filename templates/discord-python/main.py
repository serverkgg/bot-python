import os

import discord
from discord import app_commands


class Bot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()


bot = Bot()


@bot.tree.command(name="ping", description="Replies with pong and the latency")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user}, /ping is registered")


bot.run(os.environ["DISCORD_TOKEN"])
