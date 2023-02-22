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
    print(f"logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(ctx: discord.Message):
    if ctx.author == bot.user:
        pass
    if type(ctx.channel) is discord.DMChannel:
        if ctx.author != bot.user and ctx.author != quiz_master:
            await quiz_master.send(ctx.author.name + ": " + ctx.content)
        await quiz.user_answer(ctx)
    if ctx.channel == quiz_channel:
        quiz.points_minus_one(ctx.author)
        await ctx.delete()


@bot.tree.command(name="start")
async def start(interaction: discord.Interaction):
    if interaction.user == quiz_master and not quiz.is_active:
        question.start()
        await quiz.start()
        await interaction.response.send_message(f"started quiz", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="start_at")
@app_commands.describe(number="Number of the Question to start the Quiz from.")
async def start_at(interaction: discord.Interaction, number: int):
    if interaction.user == quiz_master and not quiz.is_active:
        await quiz.start_at(number)
        question.start()
        await interaction.response.send_message(f"started quiz at {number}", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="join")
async def join(interaction: discord.Interaction):
    quiz.join(interaction.user)
    await interaction.response.send_message(f"welcome to the quiz :)", ephemeral=True)


@bot.tree.command(name="update_username")
@app_commands.describe(username="the new username")
async def update_username(interaction: discord.Interaction, username: str):
    quiz.update_username(interaction.user, username)
    await interaction.response.send_message(f"updated username to {username}", ephemeral=True)


@bot.tree.command(name="remove")
async def remove(interaction: discord.Interaction, player: discord.User):
    if interaction.user == quiz_master:
        quiz.remove(player)
        await interaction.response.send_message(f"removed {player.name}", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="table")
async def table(interaction: discord.Interaction):
    for player in quiz.players:
        await interaction.user.send(f"{player.rank}. {player.username}: {player.points}")


@bot.tree.command(name="set_points")
@app_commands.describe(player="id")
@app_commands.describe(new_points="points")
async def set_points(interaction: discord.Interaction, user: discord.User, new_points: int):
    if interaction.user == quiz_master:
        quiz.set_points(user, new_points)
        await interaction.response.send_message(f"set points of {user.name} to {new_points}", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


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
