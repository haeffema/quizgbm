import os
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
from zoneinfo import ZoneInfo
from database import (
    add_user,
    get_data,
    get_question,
    get_user,
    get_users,
    update_data,
    update_user,
)

load_dotenv()

bot = commands.Bot(command_prefix="", intents=discord.Intents.all(), help_command=None)

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
QUIZ_CHANNEL_ID = int(os.getenv("QUIZ_CHANNEL_ID"))
TABLE_CHANNEL_ID = int(os.getenv("TABLE_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))


async def analyze_answer(message: discord.Message):
    if get_data().started:
        pass


async def send_question_to_receiver(receiver):
    question = get_question(get_data().question_id)
    file_name = f"question{question.id}.png"
    file_location = f'resources/{file_name}'
    description = f"{question.question}\nFrage {question.id}: {question.guesses} Versuche pro Hinweis"
    file = Path(file_location)
    embed = discord.Embed(title=question.category, description=description)
    if file.exists():
        dc_file = discord.File(file_location)
        embed.set_image(url=f"attachment://{file_name}")
        await receiver.send(embed=embed, file=dc_file)
    else:
        await receiver.send(embed=embed)


@bot.event
async def on_ready():
    sync_clock.start()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    user_ids = [user.id for user in get_users()]
    if message.author != bot.user and get_data().started:
        if type(message.channel) is discord.DMChannel and message.author.id in user_ids:
            await analyze_answer(message)
        if message.channel.id in [QUIZ_CHANNEL_ID, TABLE_CHANNEL_ID, LOG_CHANNEL_ID]:
            await message.delete()


@bot.tree.command(name="beitreten", description="Tritt dem Quiz bei")
async def beitreten(interaction: discord.Interaction):
    if interaction.user.id not in [user.id for user in get_users()]:
        add_user(interaction.user.id, interaction.user.name)
        await interaction.response.send_message(
            "Schön dass du hier bist :D", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Man kann nur einmal beitreten ;)", ephemeral=True
        )


@bot.tree.command(
    name="benutzername_updaten", description="Ändere deinen Benutzernamen"
)
async def benutzername_updaten(interaction: discord.Interaction, username: str):
    user = get_user(interaction.user.id)
    if user is not None:
        user.username = username
        update_user(user)
        await interaction.response.send_message(
            f"Benutzername ist nun {username}", ephemeral=True
        )
        return
    await interaction.response.send_message("Tritt zuerst dem Quiz bei", ephemeral=True)


@bot.tree.command(name="start", description="Start the quiz")
async def start(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID or get_data().started:
        data = get_data()
        data.started = True
        update_data(data)
        await bot.get_channel(QUIZ_CHANNEL_ID).send(data.start_message)
        await interaction.response.send_message("Quiz gestartet", ephemeral=True)
    else:
        await interaction.response.send_message("Leck Eier", ephemeral=True)


@tasks.loop(hours=5)
async def sync_clock():
    berlin_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    time_delta = berlin_time.utcoffset()

    quiz_time = time(0, 0, 0)
    dummy_quiz_date = datetime.combine(datetime.now(), quiz_time)
    adjusted_quiz_date = dummy_quiz_date - time_delta
    adjusted_quiz_time = adjusted_quiz_date.time()

    reminder_time = time(18, 0, 0)
    dummy_reminder_date = datetime.combine(datetime.now(), reminder_time)
    adjusted_reminder_date = dummy_reminder_date - time_delta
    adjusted_reminder_time = adjusted_reminder_date.time()

    send_question.change_interval(time=adjusted_quiz_time)
    send_reminder.change_interval(time=adjusted_reminder_time)

    if not send_question.is_running():
        send_question.change_interval(seconds=3)
        send_question.start()
    if not send_reminder.is_running():
        send_reminder.start()


@tasks.loop(hours=2000)
async def send_question():
    if get_data().started:
        # await send_question_to_receiver(bot.get_channel(QUIZ_CHANNEL_ID))
        for user in get_users():
            await send_question_to_receiver(bot.get_user(user.id))


@tasks.loop(hours=2000)
async def send_reminder():
    if get_data().started:
        pass


bot.run(TOKEN)
