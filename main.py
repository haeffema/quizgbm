import discord
from discord import app_commands
from discord.ext import commands, tasks

from creds import bot_token, folder, quiz_master_id, quiz_channel_id, table_channel_id, log_channel_id
from src.quiz import Quiz

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
bot.remove_command("help")

global quiz_channel
global table_channel
global log_channel
global quiz_master
global quiz


@bot.event
async def on_ready():
    init()
    try:
        synced = await bot.tree.sync()
        print(f"{bot.user} synced {len(synced)} commands")
    except Exception as e:
        print(e)


@bot.event
async def on_message(ctx: discord.Message):
    if ctx.author != bot.user and ctx.author != quiz_master:
        if type(ctx.channel) is discord.DMChannel:
            await quiz.user_answer(ctx, quiz_master)
        if ctx.channel in [quiz_channel, table_channel, log_channel] and quiz.is_active:
            await quiz.points_minus_one(ctx.author)
            await ctx.delete()


@bot.tree.command(name="help", description="sends you all available commands")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("check your dms", ephemeral=True)
    if interaction.user == quiz_master:
        await interaction.user.send(
            "/start: start the current quiz\n/start_at: start the current quiz at the given number\n/remove: remove a user from the quiz\n/set_points: update the points for a user. if the user doesnt exist it creates the user with the given points\n/send_message: sends the message in the quiz channel")
    await interaction.user.send(
        "/join: you join the quiz\n/update_username: you can change your username so its not the generated username\n/hint: you go directly to the next hint\n/ff: you'll get the answer but only get half a point for the day")


@bot.tree.command(name="start", description="starts the quiz normally")
async def start(interaction: discord.Interaction):
    if interaction.user == quiz_master and not quiz.is_active:
        await interaction.response.send_message(f"started quiz", ephemeral=True)
        question.start()
        await quiz.start()
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="start_at", description="starts the quiz at the given number")
@app_commands.describe(number="the number of the question the quiz will be started from")
async def start_at(interaction: discord.Interaction, number: int):
    if interaction.user == quiz_master and not quiz.is_active:
        await interaction.response.send_message(f"started quiz at {number}", ephemeral=True)
        await quiz.start_at(number)
        question.start()
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="join", description="the user joins the quiz")
async def join(interaction: discord.Interaction):
    await interaction.response.send_message(f"welcome to the quiz :)", ephemeral=True)
    await quiz.join(interaction.user)
    await quiz_master.send(f"{interaction.user} joined")


@bot.tree.command(name="update_username", description="updates your username to the new given")
@app_commands.describe(username="the new username")
async def update_username(interaction: discord.Interaction, username: str):
    await interaction.response.send_message(f"updated username to {username}", ephemeral=True)
    await quiz.update_username(interaction.user, username)
    await quiz_master.send(f"{interaction.user} changed name to {username}")


@bot.tree.command(name="remove", description="removes the given player from the quiz")
@app_commands.describe(player="the player that will be removed")
async def remove(interaction: discord.Interaction, player: discord.User):
    if interaction.user == quiz_master:
        await interaction.response.send_message(f"removed {player.name}", ephemeral=True)
        await quiz.remove(player)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="hint",
                  description="directly skips to the next hint or sends you all hints if your finished already")
async def hint(interaction: discord.Interaction):
    await interaction.response.send_message("check your dms :(", ephemeral=True)
    await quiz.hint(interaction.user)
    await quiz_master.send(f"{interaction.user} used /hint")


@bot.tree.command(name="ff", description="you get the answer but only half a point")
async def ff(interaction: discord.Interaction):
    await interaction.response.send_message("check your dms :(", ephemeral=True)
    await quiz.ff(interaction.user)
    await quiz_master.send(f"{interaction.user} used /ff")


@bot.tree.command(name="set_points", description="changes the points of a given player to the given number")
@app_commands.describe(user="the player which points will be changed")
@app_commands.describe(new_points="the new points for the player")
async def set_points(interaction: discord.Interaction, user: discord.User, new_points: int):
    if interaction.user == quiz_master:
        await interaction.response.send_message(f"set points of {user.name} to {new_points}", ephemeral=True)
        await quiz.set_points(user, new_points)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@bot.tree.command(name="send_message", description="sends a message from the bot to the quiz channel")
@app_commands.describe(message="message that will be sent")
async def send_message(interaction: discord.Interaction, message: str):
    if interaction.user == quiz_master:
        await interaction.response.send_message("message sent", ephemeral=True)
        await quiz_channel.send(message)
    else:
        await interaction.response.send_message("you are not the quiz-master", ephemeral=True)


@tasks.loop(hours=24)
async def question():
    if quiz.is_active:
        await quiz.send_question(quiz_master)


def init():
    global quiz_channel
    global table_channel
    global log_channel
    global quiz_master
    global quiz
    quiz_channel = bot.get_channel(quiz_channel_id)
    table_channel = bot.get_channel(table_channel_id)
    log_channel = bot.get_channel(log_channel_id)
    quiz_master = bot.get_user(quiz_master_id)
    quiz = Quiz(quiz_channel, table_channel, log_channel, folder)


bot.run(bot_token)
