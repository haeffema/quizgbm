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


async def test():
    pass


def calc_points(guesses, max_guesses):
    points = 4 - (guesses // max_guesses)
    if points < 1:
        return 1
    return points


async def analyze_answer(message: discord.Message):
    if get_data().started:
        user = get_user(message.author.id)
        if user is not None:
            question = get_question(get_data().question_id)
            if question is not None and not user.answered:
                await bot.get_user(OWNER_ID).send(
                    f"{user.username} hat geantwortet: {message.content}"
                )
                if message.content.lower() == question.answer.lower():
                    await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                    user.points += calc_points(user.guesses, question.guesses)
                    user.answered = True
                    await message.reply(
                        f"Richtig! Damit hast du nun {user.points} Punkte."
                    )
                    await send_table()
                else:
                    user.guesses += 1
                    await message.add_reaction("\N{NEGATIVE SQUARED CROSS MARK}")
                    if user.guesses == question.guesses:
                        await message.reply(question.hint1)
                    elif user.guesses == question.guesses * 2:
                        await message.reply(question.hint2)
                    elif user.guesses == question.guesses * 3:
                        await message.reply(question.hint3)
        update_user(user)


async def send_question_to_receiver(receiver):
    question = get_question(get_data().question_id)
    file_name = f"{question.id}.png"
    file_location = f"resources/{file_name}"
    title = f"{question.category}: {question.question}"
    description = f"Frage {question.id}: {question.guesses} Versuche pro Hinweis"
    file = Path(file_location)
    embed = discord.Embed(title=title, description=description)
    if file.exists():
        dc_file = discord.File(file_location)
        embed.set_image(url=f"attachment://{file_name}")
        await receiver.send(embed=embed, file=dc_file)
    else:
        await receiver.send(embed=embed)


async def send_question_to_owner():
    question = get_question(get_data().question_id)
    embed = discord.Embed(title=question.question, description=question.answer)
    embed.add_field(name="Hinweis 1", value=question.hint1, inline=True)
    embed.add_field(name="Hinweis 2", value=question.hint2, inline=True)
    embed.add_field(name="Hinweis 3", value=question.hint3, inline=True)
    await bot.get_user(OWNER_ID).send(embed=embed)


async def send_table():
    embed = discord.Embed(title="Tabelle")
    places = ""
    players = ""
    points = ""

    users = get_users()
    users.sort(key=lambda x: x.points, reverse=True)
    rank = 1
    old_points = users[0].points
    for i, user in enumerate(users):
        if old_points != user.points:
            rank = i + 1
            old_points = user.points
        places += f"{rank}\n"
        players += f"{user.username}\n"
        points += f"{user.points}\n"

    embed.add_field(name="Platz", value=places, inline=True)
    embed.add_field(name="Spieler", value=players, inline=True)
    embed.add_field(name="Punkte", value=points, inline=True)

    data = get_data()
    table_channel = bot.get_channel(TABLE_CHANNEL_ID)
    if data.table_message:
        message = await table_channel.fetch_message(data.table_message)
        await message.edit(embed=embed)
    else:
        message = await table_channel.send(embed=embed)
        data.table_message = message.id
        update_data(data)


async def question_finished():
    question = get_question(get_data().question_id)
    if question.info is None:
        embed = discord.Embed(
            title=f"{question.category}: {question.question}",
            description=f"Antwort: {question.answer}",
        )
    else:
        embed = discord.Embed(
            title=f"{question.category}: {question.question}",
            description=f"Antwort: {question.answer}\n{question.info}",
        )
    embed.add_field(name="Hinweis 1", value=question.hint1, inline=True)
    embed.add_field(name="Hinweis 2", value=question.hint2, inline=True)
    embed.add_field(name="Hinweis 3", value=question.hint3, inline=True)
    await bot.get_channel(QUIZ_CHANNEL_ID).send(embed=embed)
    await send_table()


@bot.event
async def on_ready():
    await send_table()
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
        if message.channel.id in [QUIZ_CHANNEL_ID, TABLE_CHANNEL_ID]:
            await message.delete()


@bot.tree.command(name="beitreten", description="Tritt dem Quiz bei")
async def beitreten(interaction: discord.Interaction):
    if interaction.user.id not in [user.id for user in get_users()]:
        add_user(interaction.user.id, interaction.user.name)
        await interaction.response.send_message(
            "Schön dass du hier bist :D", ephemeral=True
        )
        await bot.get_user(OWNER_ID).send(
            f"{interaction.user.name} ist dem Quiz beigetreten"
        )
    else:
        await interaction.response.send_message(
            "Man kann nur einmal beitreten ;)", ephemeral=True
        )
    await send_table()


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
    else:
        await interaction.response.send_message(
            "Tritt zuerst dem Quiz bei", ephemeral=True
        )
    await send_table()


@bot.tree.command(name="start", description="Start the quiz")
async def start(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID and not get_data().started:
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
        send_question.start()
    if not send_reminder.is_running():
        send_reminder.start()


@tasks.loop(hours=2000)
async def send_question():
    data = get_data()
    if data.started:
        if data.question_id is None:
            data.question_id = 1
            update_data(data)
        else:
            await question_finished()
            data.question_id += 1
            update_data(data)
            if get_question(data.question_id) is None:
                data.started = False
                update_data(data)
                await bot.get_channel(QUIZ_CHANNEL_ID).send(data.end_message)
                await send_table()
                return
        await send_question_to_owner()
        await send_question_to_receiver(bot.get_channel(QUIZ_CHANNEL_ID))
        for user in get_users():
            user.answered = False
            user.guesses = 0
            update_user(user)
            await send_question_to_receiver(bot.get_user(user.id))


@tasks.loop(hours=2000)
async def send_reminder():
    if get_data().started:
        for user in get_users():
            if user.answered is False:
                await bot.get_user(user.id).send("Du hast noch nicht geantwortet!")


bot.run(TOKEN)
