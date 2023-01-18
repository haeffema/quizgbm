import discord
from discord.ext import commands, tasks

from creds import bot_token
from src.quiz.quiz import Quiz

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
bot.remove_command("help")

global test_channel
test_channel_id = 1062067679533482017
global quiz_channel
quiz_channel_id = 1032314542186823730

global game_master
game_master_id = 326305842427330560

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
    if ctx.author == game_master and not quiz.started:
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
    global game_master
    game_master = bot.get_user(game_master_id)
    global test_channel
    test_channel = bot.get_channel(test_channel_id)
    global quiz_channel
    quiz_channel = bot.get_channel(quiz_channel_id)
    global quiz
    quiz = Quiz(test_channel, [], 'lotr_max')


bot.run(bot_token)
