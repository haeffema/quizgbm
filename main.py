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
    await bot.process_commands(ctx)
    if type(ctx.channel) is discord.DMChannel:
        if ctx.author != bot.user:
            await quiz_master.send(ctx.author.name + ": " + ctx.content)
        await quiz.user_answer(ctx)
    if ctx.channel == quiz_channel:
        quiz.points_minus_one(ctx.author.id)


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
    await interaction.response.send_message(f"removed {quiz.quit_player(interaction.user.id)}", ephemeral=True)


@bot.tree.command(name="points")
@app_commands.describe()
async def points(interaction: discord.Interaction):
    await interaction.response.send_message(f"Da hast gerade {quiz.get_points(interaction.user.id)} Punkte.",
                                            ephemeral=True)


@bot.tree.command(name="set_points")
@app_commands.describe(player="id")
@app_commands.describe(new_points="points")
async def set_points(interaction: discord.Interaction, player: str, new_points: int):
    if interaction.user.id == quiz_master_id:
        name = quiz.set_points(int(player), new_points)
        await interaction.response.send_message(f"Set {name} points to {new_points}", ephemeral=True)


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
