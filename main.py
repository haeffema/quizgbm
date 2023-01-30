import discord
from discord import app_commands
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
    init()
    print("logged in as {0.user}".format(bot))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(ctx: discord.Message):
    await bot.process_commands(ctx)
    if type(ctx.channel) is discord.DMChannel:
        if ctx.author != bot.user:
            await quiz_master.send(ctx.author.name + ": " + ctx.content)
        await quiz.user_answer(ctx)


@bot.command()
async def start(ctx: discord.Message):
    if ctx.author == quiz_master and not quiz.is_active:
        question.start()
        await quiz.start_quiz()


@bot.tree.command(name="register")
@app_commands.describe(username="Enter your username")
async def register(interaction: discord.Interaction, username: str):
    quiz.register_player(interaction.user.id, username)
    await interaction.response.send_message(f"set your username to {username}", ephemeral=True)


@bot.tree.command(name="quit")
@app_commands.describe()
async def quit(interaction: discord.Interaction):
    await interaction.response.send_message(f"removed {quiz.quit_player()}", ephemeral=True)


@tasks.loop(hours=24)
async def question():
    if quiz.is_active:
        await quiz.send_question()


def init():
    global quiz_master
    global quiz_channel
    global quiz
    quiz_master = bot.get_user(quiz_master_id)
    quiz_channel = bot.get_channel(quiz_channel_id)
    quiz = Quiz(quiz_channel, folder)


bot.run(bot_token)
