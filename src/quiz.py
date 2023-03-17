from pathlib import Path

import discord

from src.log import Log
from src.player import Player
from src.question import Question


class Quiz:
    def __init__(self, quiz_channel: discord.TextChannel, table_channel: discord.TextChannel,
                 log_channel: discord.TextChannel, folder: str):
        self.quiz_channel = quiz_channel
        self.table_channel = table_channel
        self.log_channel = log_channel
        self.folder = folder
        self.players = []
        self.questions = []
        self.log_list = []
        self.start_message = ""
        self.end_message = ""
        self.table_message = None
        self.active_question = None
        self.is_active = False
        self.count = 0
        self.generate_quiz()

    def generate_quiz(self):
        with open(self.folder + '/quiz.txt', encoding="utf-8") as setup:
            for line in setup.readline().split(';'):
                self.start_message += line + "\n"
            for line in setup.readline().split(';'):
                self.end_message += line + "\n"
            for question in setup.readlines():
                self.generate_question(question)

    def generate_question(self, question_str: str):
        question_information = question_str.split(";")
        self.questions.append(Question(question_information))

    async def start(self):
        if not self.is_active:
            await self.quiz_channel.send(self.start_message)
            self.is_active = True

    async def start_at(self, number):
        if not self.is_active:
            self.count = number - 1
            self.is_active = True

    async def strike(self, user: discord.Member, reason: str):
        for player in self.players:
            if player.user == user:
                if player.strikes == 2:
                    await user.send(f"{reason}: damit bist du aus dem Quiz.")
                    self.players.remove(player)
                if player.strikes == 1:
                    await user.send(f"{reason}: damit verlierst du alle Punkte.")
                    player.strikes = 2
                    player.points = 0
                if player.strikes == 0:
                    await user.send(f"{reason}: hier passiert noch nichts.")
                    player.strikes = 1
                await self.update_table()
                return

    async def join(self, user: discord.User):
        for player in self.players:
            if player.user == user:
                return
        self.players.append(Player(user, user.name))
        await self.update_table()

    async def update_username(self, user: discord.User, username: str):
        for player in self.players:
            if player.user == user:
                player.username = username
                await self.update_table()
                return

    async def remove(self, user: discord.User):
        for player in self.players:
            if player.user == user:
                self.players.remove(player)
                await self.update_table()
                return

    async def set_points(self, user: discord.User, points: int):
        for player in self.players:
            if player.user == user:
                player.points = points
                await self.update_table()
                return
        player = Player(user, user.name)
        player.points = points
        self.players.append(player)
        await self.update_table()

    async def hint(self, user: discord.User):
        for player in self.players:
            if player.user == user:
                if player.correct_today:
                    await self.send_hints(user)
                    return
                player.guesses += self.active_question.max_guesses - player.guesses % self.active_question.max_guesses
                for count in range(3):
                    if player.guesses == self.active_question.max_guesses * (count + 1):
                        self.log_list.append(Log(player, "used /hint", count))
                        await user.send(self.active_question.hints[count])
                        await self.update_table()
                        return

    async def send_question(self, quiz_master: discord.User):
        if self.active_question is not None:
            await self.reveal_answer()
        self.active_question = self.questions[self.count]
        self.count += 1
        await self.send_question_embed(self.quiz_channel)
        for player in self.players:
            await self.send_question_embed(player.user)
        await self.send_hints(quiz_master)
        await self.update_table()

    async def send_question_embed(self, receiver):
        filename = 'send' + str(self.count) + '.png'
        file_location = self.folder + "/" + filename
        description = self.active_question.question + f"\n{self.count}/{len(self.questions)}: {self.active_question.max_guesses} guesses"
        file = Path(file_location)
        embed = discord.Embed(title=self.active_question.category, description=description)
        if file.exists():
            dc_file = discord.File(file_location)
            embed.set_image(url='attachment://' + filename)
            await receiver.send(embed=embed, file=dc_file)
        else:
            await receiver.send(embed=embed)

    async def send_hints(self, user):
        message = "Hints:\n"
        for hint in self.active_question.hints:
            message += f"{hint}\n"
        message += f"Lösung: {self.active_question.answer}"
        await user.send(message)

    async def send_reminder(self):
        if self.active_question is None:
            return
        for player in self.players:
            if not player.correct_today:
                await player.user.send("Hey, du solltest heute noch antworten.\nNutze /hint um schneller an Hints zu "
                                       "kommen.")

    async def reveal_answer(self):
        self.reset_guesses()
        await self.log_answers()
        self.active_question = None
        self.log_list = []
        if self.count == len(self.questions):
            await self.end_quiz()

    async def log_answers(self):
        filename = 'send' + str(self.count) + '.png'
        file_location = self.folder + "/" + filename
        file = Path(file_location)
        self.log_list.sort(key=lambda x: x.hint_number)
        hint_numbers = [1, 2, 3, "fill"]
        embed = discord.Embed(title=self.active_question.category, description=self.active_question.question)
        users_str = ""
        answers_str = ""
        for log in self.log_list:
            if log.hint_number == hint_numbers[0]:
                if users_str != "" and answers_str != "":
                    embed.add_field(name="", value=users_str, inline=True)
                    embed.add_field(name="", value=answers_str, inline=True)
                    users_str = ""
                    answers_str = ""
                embed.add_field(name="",
                                value=f"Hint {log.hint_number}: {self.active_question.hints[log.hint_number - 1]}",
                                inline=False)
                hint_numbers.remove(hint_numbers[0])
            users_str += f"{log.player.username}\n"
            answers_str += f"{log.content}\n"
        if users_str != "" and answers_str != "":
            embed.add_field(name="", value=users_str, inline=True)
            embed.add_field(name="", value=answers_str, inline=True)
        if "fill" in hint_numbers:
            hint_numbers.remove("fill")
        for hint_num in hint_numbers:
            embed.add_field(name="", value=f"Hint {hint_num}: {self.active_question.hints[hint_num - 1]}",
                            inline=False)
        embed.add_field(name=self.active_question.answer, value="", inline=False)
        if file.exists():
            dc_file = discord.File(file_location)
            embed.set_image(url='attachment://' + filename)
            await self.log_channel.send(embed=embed, file=dc_file)
        else:
            await self.log_channel.send(embed=embed)

    def reset_guesses(self):
        for player in self.players:
            player.guesses = 0
            player.correct_today = False

    async def end_quiz(self):
        for player in self.players:
            if player.rank == 1:
                self.end_message = f"Herzlichen Glückwunsch {player.username}\n" + self.end_message
        await self.quiz_channel.send(self.end_message)
        self.is_active = False

    async def user_answer(self, user_answer: discord.Message, quiz_master: discord.User):
        for player in self.players:
            if player.user == user_answer.author:
                if player.correct_today or self.active_question is None:
                    return
                if user_answer.content == self.active_question.answer:
                    player.points += self.calculate_points(player)
                    player.correct_today = True
                    await user_answer.add_reaction('\N{white heavy check mark}')
                    await user_answer.reply(f"Damit hast du nun {player.points} Punkte.")
                    await self.all_correct_today()
                else:
                    if player.guesses // self.active_question.max_guesses < 3:
                        self.log_list.append(
                            Log(player, user_answer.content, player.guesses // self.active_question.max_guesses))
                    else:
                        self.log_list.append(Log(player, user_answer.content, 3))
                    player.guesses += 1
                    await user_answer.add_reaction('\N{negative squared cross mark}')
                    for count in range(3):
                        if player.guesses == self.active_question.max_guesses * (count + 1):
                            await user_answer.reply(self.active_question.hints[count])
                await quiz_master.send(f"{player.username}: {user_answer.content}")
                await self.update_table()
                return

    def calculate_points(self, player):
        points = 4 - (player.guesses // self.active_question.max_guesses)
        if points < 1:
            return 1
        return points

    async def all_correct_today(self):
        for player in self.players:
            if not player.correct_today:
                return
        await self.reveal_answer()

    async def update_table(self):
        if self.table_message is not None:
            await self.table_message.delete()
        self.players.sort(key=lambda player_to_sort: player_to_sort.points, reverse=True)
        rank = 1
        for index, player in enumerate(self.players):
            player.rank = rank
            for count in range(index):
                if self.players[count].points == player.points:
                    player.rank = self.players[count].rank
            rank += 1
        embed = discord.Embed(title=f"{self.count}/{len(self.questions)}")
        places_str = ""
        player_str = ""
        points_str = ""
        for player in self.players:
            places_str += f"{player.rank}.\n"
            player_str += f"{player.username}\n"
            if player.correct_today or self.active_question is None:
                points_str += f"{player.points}\n"
            else:
                points_str += f"{player.points} | max. + {self.calculate_points(player)}\n"
        embed.add_field(name="Platz", value=places_str, inline=True)
        embed.add_field(name="Spieler", value=player_str, inline=True)
        embed.add_field(name="Punkte", value=points_str, inline=True)
        self.table_message = await self.table_channel.send(embed=embed)

    async def points_minus_one(self, user):
        for player in self.players:
            if player.user == user:
                player.points -= 1
                await self.update_table()
                return
