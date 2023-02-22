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


@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    if interaction.user == quiz_master:
        await interaction.user.send("/start: start the current quiz")
        await interaction.user.send("/start_at: start the current quiz at the given number")
        await interaction.user.send("/remove: remove a user from the quiz")
        await interaction.user.send(
            "/set_points: update the points for a user. if the user doesnt exist it creates the user with the given points")
        await interaction.user.send("/send_message: sends the message in the quiz channel")
    await interaction.user.send("/join: you join the quiz")
    await interaction.user.send("/update_username: you can change your username so its not the generated username")
    await interaction.user.send(
        "/table: you get the current table. (The guesses a player has today and if the player has correctly answered today)")


@bot.tree.command(name="start")
async def start(interaction: discord.Interaction):
    if interaction.user == quiz_master and not quiz.is_active:
        question.start()
        await quiz.start()
        await interaction.response.send_message(f"started quiz", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="start_at")
@app_commands.describe(number="the number of the question the quiz will be started from")
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
@app_commands.describe(player="the player that will be removed")
async def remove(interaction: discord.Interaction, player: discord.User):
    if interaction.user == quiz_master:
        quiz.remove(player)
        await interaction.response.send_message(f"removed {player.name}", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="table")
async def table(interaction: discord.Interaction):
    for player in quiz.players:
        await interaction.user.send(
            f"{player.rank}. {player.username}: {player.points}. ({player.guesses} - {player.correct_today})")


@bot.tree.command(name="set_points")
@app_commands.describe(user="the player which points will be changed")
@app_commands.describe(new_points="the new points for the player")
async def set_points(interaction: discord.Interaction, user: discord.User, new_points: int):
    if interaction.user == quiz_master:
        quiz.set_points(user, new_points)
        await interaction.response.send_message(f"set points of {user.name} to {new_points}", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="send_message")
@app_commands.describe(message="message that will be sent")
async def send_message(interaction: discord.Interaction, message: str):
    if interaction.user == quiz_master:
        await quiz_channel.send(message)
        await interaction.response.send_message("message sent", ephemeral=True)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@tasks.loop(hours=24)
async def question():
    if quiz.is_active:
        await quiz.send_question(quiz_master)


def init():
    global quiz_master
    global quiz_channel
    global quiz
    quiz_master = bot.get_user(quiz_master_id)
    quiz_channel = bot.get_channel(quiz_channel_id)
    quiz = Quiz(quiz_channel, folder)


bot.run(bot_token)
