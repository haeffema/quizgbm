import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

from creds import bot_token, folder, quiz_master_id, quiz_channel_id, table_channel_id, log_channel_id
from src.quiz import Quiz

bot = commands.Bot(command_prefix="", intents=discord.Intents.all())
bot.remove_command("help")

global quiz_channel
global table_channel
global log_channel
global quiz_master
global quiz
global question_hour
global reminder_hour


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


@bot.tree.command(name="start", description="starts with the first question and sends the start message")
async def start(interaction: discord.Interaction):
    if interaction.user == quiz_master:
        if quiz.is_active:
            await interaction.response.send_message("quiz is already running", ephemeral=True)
        else:
            await interaction.response.send_message(f"started quiz", ephemeral=True)
            await quiz.start()
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="start_at", description="starts the quiz at the given number and without start message")
@app_commands.describe(number="the question the quiz will start at")
async def start_at(interaction: discord.Interaction, number: int):
    if interaction.user == quiz_master and not quiz.is_active:
        if quiz.is_active:
            await interaction.response.send_message("quiz is already running", ephemeral=True)
        else:
            await interaction.response.send_message(f"started quiz at {number}", ephemeral=True)
            await quiz.start_at(number)
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="send_message", description="sends a message from the bot to the quiz channel")
@app_commands.describe(message="message that will be sent")
async def send_message(interaction: discord.Interaction, message: str):
    if interaction.user == quiz_master:
        await interaction.response.send_message("message was sent", ephemeral=True)
        await quiz_channel.send(message)
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="set_points", description="changes the points of a user")
@app_commands.describe(user="the user")
@app_commands.describe(new_points="the new points")
async def set_points(interaction: discord.Interaction, user: discord.User, new_points: int):
    if interaction.user == quiz_master:
        await interaction.response.send_message(f"set points of {user.name} to {new_points}", ephemeral=True)
        await quiz.set_points(user, new_points)
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="remove", description="removes the user from the quiz")
@app_commands.describe(user="the user")
async def remove(interaction: discord.Interaction, user: discord.User):
    if interaction.user == quiz_master:
        await interaction.response.send_message(f"removed {user.name}", ephemeral=True)
        await quiz.remove(user)
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="change_time",
                  description="allows the quiz master to change the hour of question and reminder. standard times are "
                              "0 and 20")
@app_commands.describe(question="the hour the question will be sent")
@app_commands.describe(reminder="the hour the reminder will be sent")
async def change_time(interaction: discord.Interaction, question: int, reminder: int):
    if interaction.user == quiz_master:
        await interaction.response.send_message(f"questions now at {question}, reminder at {reminder}", ephemeral=True)
        global question_hour
        question_hour = question
        global reminder_hour
        reminder_hour = reminder
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="strike", description="the player will receive a strike")
@app_commands.describe(player="the player")
@app_commands.describe(reason="the reason")
async def strike(interaction: discord.Interaction, player: discord.User, reason: str):
    if interaction.user == quiz_master:
        await interaction.response.send_message(f"{player.name} has received a strike for: {reason}", ephemeral=True)
        await quiz.strike(player, reason)
    else:
        await interaction.response.send_message("you are not the quiz master", ephemeral=True)


@bot.tree.command(name="join", description="you join the quiz")
async def join(interaction: discord.Interaction):
    if interaction.user != quiz_master:
        await interaction.response.send_message("welcome to the quiz :)", ephemeral=True)
        await quiz.join(interaction.user)
        await quiz_master.send(f"{interaction.user} joined")
    else:
        await interaction.response.send_message("the quiz master can't join", ephemeral=True)


@bot.tree.command(name="update_username", description="updates your username")
@app_commands.describe(username="the new username")
async def update_username(interaction: discord.Interaction, username: str):
    if interaction.user != quiz_master:
        await interaction.response.send_message(f"updated username to {username}", ephemeral=True)
        await quiz.update_username(interaction.user, username)
        await quiz_master.send(f"{interaction.user} changed name to {username}")
    else:
        await interaction.response.send_message("the quiz master can't change his username", ephemeral=True)


@bot.tree.command(name="hint", description="skips to the next hint. if finished sends you all the hints")
async def hint(interaction: discord.Interaction):
    if interaction.user != quiz_master:
        await interaction.response.send_message("check your dms", ephemeral=True)
        await quiz.hint(interaction.user)
        await quiz_master.send(f"{interaction.user} used /hint")
    else:
        await interaction.response.send_message("the quiz master doesn't need hints", ephemeral=True)


@tasks.loop(minutes=15, reconnect=True)
async def fix_clock_format():
    if send_question.is_running():
        send_question.change_interval(time=datetime.time(hour=local_hour_to_utc(question_hour)))
    if send_reminder.is_running():
        send_reminder.change_interval(time=datetime.time(hour=local_hour_to_utc(reminder_hour)))


def local_hour_to_utc(local_hour):
    utc_hour_now = datetime.datetime.utcnow().hour
    local_hour_now = datetime.datetime.now().hour
    difference_utc_local = utc_hour_now - local_hour_now
    return (local_hour + difference_utc_local) % 24


@tasks.loop(hours=1000, reconnect=True)
async def send_question():
    if quiz.is_active:
        await quiz.send_question(quiz_master)


@tasks.loop(hours=1000, reconnect=True)
async def send_reminder():
    if quiz.is_active:
        await quiz.send_reminder()


def init():
    global quiz_channel
    global table_channel
    global log_channel
    global quiz_master
    global quiz
    global question_hour
    global reminder_hour
    quiz_channel = bot.get_channel(quiz_channel_id)
    table_channel = bot.get_channel(table_channel_id)
    log_channel = bot.get_channel(log_channel_id)
    quiz_master = bot.get_user(quiz_master_id)
    quiz = Quiz(quiz_channel, table_channel, log_channel, folder)
    question_hour = 0
    reminder_hour = 20
    fix_clock_format.start()
    send_question.start()
    send_reminder.start()


bot.run(bot_token)
