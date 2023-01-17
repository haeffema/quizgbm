import discord
from discord.ext import commands

from creds import bot_token

from src.quiz.quiz import Quiz

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
bot.remove_command("help")

quiz = Quiz([], [], "start test", "end test")


@bot.event
async def on_ready():
    print("logged in as {0.user}".format(bot))


@bot.event
async def on_message(ctx: discord.Message):
    await bot.process_commands(ctx)
    """
    if ctx.author != bot.user:
        print(ctx.author, ":", ctx.content, "in", ctx.channel)
        if type(ctx.channel) is discord.DMChannel:
            print("dm")
        else:
            print("no dm")
    """


@bot.command()
async def start(ctx: discord.Message):
    await quiz.start_quiz(ctx)


@bot.command()
async def get(ctx: discord.Message):
    await ctx.channel.send("https://discord.com/api/oauth2/authorize?client_id=802219294330585148&permissions=8&scope=bot")

bot.run(bot_token)
