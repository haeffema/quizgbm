from pathlib import Path
import discord
import json
from discord.ext import commands, tasks
from datetime import datetime
from zoneinfo import ZoneInfo
from consts import (
    LOG_CHANNEL_ID,
    OWNER_ID,
    QUIZ_CHANNEL_ID,
    QUIZ_FOLDER,
    QUIZ_TIME,
    REMINDER_TIME,
    TABLE_CHANNEL_ID,
    TOKEN,
)
from database import (
    add_message,
    add_user,
    get_data,
    get_messages,
    get_question,
    get_user,
    get_users,
    update_data,
    update_user,
)
import pandas as pd
import matplotlib.pyplot as plt


bot = commands.Bot(command_prefix="", intents=discord.Intents.all(), help_command=None)


async def delete_last_message():
    for p in get_users():
        user = await bot.fetch_user(p.id)
        if user:
            dm_channel = await user.create_dm()
            async for message in dm_channel.history(limit=10):
                if message.author == bot.user:
                    await message.delete()
                    break


async def test():
    # await send_question()
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
                if message.content.lower() in [question.answer.lower()]:
                    await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                    user.points += calc_points(user.guesses, question.guesses)
                    user.answered = True
                    await message.reply(
                        f"Richtig! Damit hast du nun {user.points} Punkte."
                    )
                    await bot.get_user(OWNER_ID).send(
                        f"{message.author.display_name} hat richtig geantwortet."
                    )
                    add_message(
                        f"{message.author.display_name} hat richtig geantwortet."
                    )
                else:
                    user.guesses += 1
                    await message.add_reaction("\N{NEGATIVE SQUARED CROSS MARK}")
                    await bot.get_user(OWNER_ID).send(
                        f"{message.author.display_name} hat geantwortet: {message.content}"
                    )
                    add_message(
                        f"{message.author.display_name} hat geantwortet: {message.content}"
                    )
                    if (
                        user.guesses
                        in [
                            question.guesses - 1,
                            question.guesses * 2 - 1,
                            question.guesses * 3 - 1,
                        ]
                        and question.guesses > 1
                    ):
                        await message.add_reaction("\N{HEAVY EXCLAMATION MARK SYMBOL}")
                    if user.guesses == question.guesses:
                        await send_hints(message.author.id, 1)
                        await bot.get_user(OWNER_ID).send(
                            f"{message.author.display_name} hat Hinweis 1 bekommen."
                        )
                        add_message(
                            f"{message.author.display_name} hat Hinweis 1 bekommen."
                        )
                    elif user.guesses == question.guesses * 2:
                        await send_hints(message.author.id, 2)
                        await bot.get_user(OWNER_ID).send(
                            f"{message.author.display_name} hat Hinweis 2 bekommen."
                        )
                        add_message(
                            f"{message.author.display_name} hat Hinweis 2 bekommen."
                        )
                    elif user.guesses == question.guesses * 3:
                        await send_hints(message.author.id, 3)
                        await bot.get_user(OWNER_ID).send(
                            f"{message.author.display_name} hat Hinweis 3 bekommen."
                        )
                        add_message(
                            f"{message.author.display_name} hat Hinweis 3 bekommen."
                        )
        update_user(user)
        await send_table()


async def send_question_to_receiver(receiver: int):
    question = get_question(get_data().question_id)
    file_name = f"{question.id}.png"
    file_location = f"{QUIZ_FOLDER}/{file_name}"
    file = Path(file_location)
    dsc = f"{question.guesses} Versuche pro Hinweis"
    if question.guesses == 1:
        dsc = f"{question.guesses} Versuch pro Hinweis"
    embed = discord.Embed(
        title=question.question,
        description=dsc,
        timestamp=datetime.now(),
    )
    embed.set_author(name=question.category)
    embed.set_footer(text=f"Frage {question.id}")
    if file.exists():
        dc_file = discord.File(file_location)
        embed.set_image(url=f"attachment://{file_name}")
        await receiver.send(embed=embed, file=dc_file)
    else:
        await receiver.send(embed=embed)


async def send_question_to_owner():
    question = get_question(get_data().question_id)
    embed = discord.Embed(title=question.question, description=question.answer)
    embed.add_field(name="Hinweis 1", value=question.hint1)
    embed.add_field(name="Hinweis 2", value=question.hint2)
    embed.add_field(name="Hinweis 3", value=question.hint3)
    embed.set_footer(text=f"Frage {question.id} | {question.guesses} Versuche")
    file_name = f"{question.id}.png"
    file_location = f"{QUIZ_FOLDER}/{file_name}"
    file = Path(file_location)
    if file.exists():
        dc_file = discord.File(file_location)
        embed.set_image(url=f"attachment://{file_name}")
        await bot.get_user(OWNER_ID).send(embed=embed, file=dc_file)
    else:
        await bot.get_user(OWNER_ID).send(embed=embed)


async def send_table(finished=False):
    table_data = {"Platz": [], "Spieler": [], "Punkte": []}

    users = get_users()
    users.sort(key=lambda x: x.points, reverse=True)
    rank = 1
    old_points = users[0].points
    points_len = len(str(old_points))
    for i, user in enumerate(users):
        if old_points != user.points:
            rank = i + 1
            old_points = user.points
        table_data["Platz"].append(rank)
        table_data["Spieler"].append(user.username)
        if user.answered or finished:
            table_data["Punkte"].append(f"{user.points:0{points_len}d}")
        else:
            table_data["Punkte"].append(
                f"{user.points:0{points_len}d} | max. + {calc_points(user.guesses, get_question(get_data().question_id).guesses)}"
            )

    if finished:
        winner = []
        for i in range(len(table_data["Platz"])):
            if table_data["Platz"][i] == 1:
                winner.append(table_data["Spieler"][i])
        if len(winner) == 1:
            await bot.get_channel(QUIZ_CHANNEL_ID).send(
                f"Herzlichen Glückwunsch an {winner[0]} zum ersten Platz!"
            )
        else:
            await bot.get_channel(QUIZ_CHANNEL_ID).send(
                f"Herzlichen Glückwunsch an {', '.join(winner)} zum ersten Platz!"
            )

    with open("old_data.json", "r") as f:
        old_data = json.load(f)

    if old_data == table_data:
        return

    with open("old_data.json", "w") as f:
        json.dump(table_data, f, indent=4)

    df = pd.DataFrame(table_data)

    fig, ax = plt.subplots(figsize=(5, 2))
    fig.patch.set_facecolor("#070709")
    ax.set_facecolor("#131517")

    ax.axis("tight")
    ax.axis("off")

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="center",
        colColours=["#131517"] * df.shape[1],
    )

    for (i, j), cell in table.get_celld().items():
        cell.set_edgecolor("#e5e5e8")
        cell.set_text_props(color="#e5e5e8", fontsize=10)
        if i == 0:
            cell.set_text_props(fontweight="bold", color="#e5e5e8", fontsize=10)
        if i > 0:
            cell.set_facecolor("#131517")

    plt.title("Tabelle", fontsize=14, color="#e5e5e8", pad=3)

    plt.subplots_adjust(top=0.85)

    plt.savefig(
        "table.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    plt.close()

    data = get_data()
    table_channel = bot.get_channel(TABLE_CHANNEL_ID)
    if data.table_message:
        try:
            message = await table_channel.fetch_message(data.table_message)
            await message.delete()
        finally:
            pass
    message = await table_channel.send(file=discord.File("table.png"))
    data.table_message = message.id
    update_data(data)


async def question_finished():
    question = get_question(get_data().question_id)
    messages = get_messages(get_data().question_id)
    msg_txt = f"{question.question}\n"
    for message in messages:
        msg_txt += f"{message.content}\n"
    if question.info is None:
        embed = discord.Embed(
            title=f"{question.id}: {question.category} | {question.guesses} Versuche",
            description=msg_txt,
        )
    else:
        embed = discord.Embed(
            title=f"{question.category}: {question.question}",
            description=question.info,
        )
    embed.add_field(name="Hinweis 1", value=question.hint1, inline=True)
    embed.add_field(name="Hinweis 2", value=question.hint2, inline=True)
    embed.add_field(name="Hinweis 3", value=question.hint3, inline=True)
    embed.add_field(name=question.answer, value=" ")

    await bot.get_channel(LOG_CHANNEL_ID).send(embed=embed)


async def send_hints(userId: int, hintAmount: int):
    question = get_question(get_data().question_id)
    embed = discord.Embed(title=question.question)
    embed.add_field(name="Hinweis 1", value=question.hint1)
    if hintAmount > 1:
        embed.add_field(name="Hinweis 2", value=question.hint2)
    if hintAmount > 2:
        embed.add_field(name="Hinweis 3", value=question.hint3)
    file_name = f"{question.id}.png"
    file_location = f"{QUIZ_FOLDER}/{file_name}"
    file = Path(file_location)
    if file.exists():
        dc_file = discord.File(file_location)
        embed.set_image(url=f"attachment://{file_name}")
        await bot.get_user(userId).send(embed=embed, file=dc_file)
    else:
        await bot.get_user(userId).send(embed=embed)


@bot.event
async def on_ready():
    sync_clock.start()
    await test()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    user_ids = [user.id for user in get_users()]
    if message.author != bot.user and get_data().started:
        if type(message.channel) is discord.DMChannel and message.author.id in user_ids:
            await analyze_answer(message)
        if (
            message.channel.id in [QUIZ_CHANNEL_ID, TABLE_CHANNEL_ID, LOG_CHANNEL_ID]
            and message.author.id != OWNER_ID
        ):
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


@bot.tree.command(
    name="hinweis", description="Gibt den nächsten Hinweis, damit auch weniger Punkte."
)
async def hinweis(interaction: discord.Interaction):
    if get_data().started:
        user = get_user(interaction.user.id)
        if user is not None:
            question = get_question(get_data().question_id)
            if question is not None:
                if not user.answered:
                    if user.guesses < question.guesses:
                        user.guesses = question.guesses
                        await send_hints(interaction.user.id, 1)
                        await bot.get_user(OWNER_ID).send(
                            f"{interaction.user.display_name} hat Hinweis 1 per Command bekommen."
                        )
                        add_message(
                            f"{interaction.user.display_name} hat Hinweis 1 per Command bekommen."
                        )
                    elif user.guesses < question.guesses * 2:
                        user.guesses = question.guesses * 2
                        await send_hints(interaction.user.id, 2)
                        await bot.get_user(OWNER_ID).send(
                            f"{interaction.user.display_name} hat Hinweis 2 per Command bekommen."
                        )
                        add_message(
                            f"{interaction.user.display_name} hat Hinweis 2 per Command bekommen."
                        )
                    elif user.guesses < question.guesses * 3:
                        user.guesses = question.guesses * 3
                        await send_hints(interaction.user.id, 3)
                        await bot.get_user(OWNER_ID).send(
                            f"{interaction.user.display_name} hat Hinweis 3 per Command bekommen."
                        )
                        add_message(
                            f"{interaction.user.display_name} hat Hinweis 3 per Command bekommen."
                        )
                    else:
                        await interaction.user.send("Du hast alle Hinweise erhalten.")
                    update_user(user)
                else:
                    await send_hints(interaction.user.id, 3)
    await interaction.response.send_message("Schau in deine DM's.", ephemeral=True)
    await send_table()


@bot.tree.command(name="start", description="Startet das Quiz.")
async def start(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID and not get_data().started:
        data = get_data()
        data.started = True
        update_data(data)
        await bot.get_channel(QUIZ_CHANNEL_ID).send(data.start_message)
        await interaction.response.send_message("Quiz gestartet", ephemeral=True)
    else:
        await interaction.response.send_message("Leck Eier", ephemeral=True)


@bot.tree.command(
    name="nachricht", description="Schicke eine Nachricht in den Channel."
)
async def nachricht(interaction: discord.Interaction, message: str):
    if interaction.user.id == OWNER_ID:
        await bot.get_channel(QUIZ_CHANNEL_ID).send(message)
        await interaction.response.send_message("Nachricht verschickt", ephemeral=True)
    else:
        await interaction.response.send_message("Leck Eier", ephemeral=True)


@tasks.loop(hours=5)
async def sync_clock():
    berlin_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    time_delta = berlin_time.utcoffset()

    quiz_time = QUIZ_TIME
    dummy_quiz_date = datetime.combine(datetime.now(), quiz_time)
    adjusted_quiz_date = dummy_quiz_date - time_delta
    adjusted_quiz_time = adjusted_quiz_date.time()

    reminder_time = REMINDER_TIME
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
                await send_table(True)
                return
        await send_question_to_owner()
        await send_question_to_receiver(bot.get_channel(QUIZ_CHANNEL_ID))
        for user in get_users():
            user.answered = False
            user.guesses = 0
            update_user(user)
            await send_question_to_receiver(bot.get_user(user.id))
        await send_table()


@tasks.loop(hours=2000)
async def send_reminder():
    if get_data().started:
        for user in get_users():
            if user.answered is False:
                await bot.get_user(user.id).send(
                    f"Hallo {user.username}, denk daran zu antworten!"
                )


bot.run(TOKEN)
