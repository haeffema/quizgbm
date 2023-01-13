import discord
from discord.ext import commands

from src.user.init import players
from creds import bot_token

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
bot.remove_command("help")


@bot.event
async def on_ready():
    print("logged in as {0.user}".format(bot))


@bot.event
async def on_message(ctx: discord.Message):
    await bot.process_commands(ctx)
    if ctx.author != bot.user:
        print(ctx.author, ":", ctx.content)


@bot.command()
async def get(ctx: discord.Message):
    await ctx.channel.send("https://discord.com/api/oauth2/authorize?client_id=802219294330585148&permissions=8&scope=bot")

bot.run(bot_token)
