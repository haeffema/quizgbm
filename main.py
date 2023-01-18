import discord
from discord.ext import commands, tasks

from creds import bot_token, folder, quiz_master_id, quiz_channel_id
from src.quiz import Quiz

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
bot.remove_command("help")

global quiz_channel
global quiz_master
global quiz


@bot.event
async def on_ready():
    print("logged in as {0.user}".format(bot))
    init()


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
    if ctx.author == quiz_master and not quiz.started:
        question.start()
        await quiz.start_quiz()


@tasks.loop(seconds=1)
async def question():
    if quiz.started:
        await quiz.send_question()


@bot.command()
async def get(ctx: discord.Message):
    await ctx.channel.send(
        "https://discord.com/api/oauth2/authorize?client_id=802219294330585148&permissions=8&scope=bot")


def init():
    global quiz_master
    global quiz_channel
    global quiz
    quiz_master = bot.get_user(quiz_master_id)
    quiz_channel = bot.get_channel(quiz_channel_id)
    quiz = Quiz(quiz_channel, [], folder)


bot.run(bot_token)
