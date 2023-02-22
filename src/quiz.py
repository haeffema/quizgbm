from pathlib import Path

import discord

from src.player import Player
from src.question import Question


class Quiz:
    def __init__(self, channel: discord.TextChannel, folder: str):
        self.channel = channel
        self.folder = folder
        self.players = []
        self.questions = []
        self.start_message = None
        self.end_message = None
        self.active_question = None
        self.is_active = False
        self.count = 0
        self.generate_quiz()

    def generate_quiz(self):
        with open(self.folder + '/quiz.txt', encoding="utf-8") as setup:
            self.start_message = setup.readline()
            self.end_message = setup.readline()
            for question in setup.readlines():
                self.generate_question(question)

    def generate_question(self, question_str: str):
        question_information = question_str.split(";")
        self.questions.append(Question(question_information))

    async def start(self):
        if not self.is_active:
            await self.send_text(self.start_message)
            self.is_active = True

    async def start_at(self, number):
        if not self.is_active:
            self.count = number
            self.is_active = True

    def join(self, user: discord.User):
        for player in self.players:
            if player.user == user:
                return
        self.players.append(Player(user, user.name))

    def update_username(self, user: discord.User, username: str):
        for player in self.players:
            if player.user == user:
                player.username = username
                return

    def remove(self, user: discord.User):
        for player in self.players:
            if player.user == user:
                self.players.remove(player)
                return

    def set_points(self, user: discord.User, points: int):
        for player in self.players:
            if player.user == user:
                player.points = points
                return
        player = Player(user, user.name)
        player.points = points
        self.players.append(player)

    async def send_text(self, message: str):
        for text in message.split("|"):
            await self.channel.send(text)

    async def send_image(self):
        file = Path(self.folder + '/send' + str(self.count) + '.png')
        if file.exists():
            await self.channel.send(file=discord.File(self.folder + "/send" + str(self.count) + ".png"))

    async def send_question(self, quiz_master: discord.User):
        if self.active_question is not None:
            await self.reveal_answer()
        if self.count < len(self.questions):
            self.active_question = self.questions[self.count]
            self.count += 1
            await quiz_master.send("Heutigen Hints:")
            for hint in self.active_question.hints:
                await quiz_master.send(hint)
            await self.send_image()
            await self.send_text(self.active_question.question)
            await self.send_text(str(self.count) + "/" + str(len(self.questions)) + ": " + str(
                self.active_question.max_guesses) + " guesses")

    async def reveal_answer(self):
        self.reset_guesses()
        await self.send_text("Die Lösung war: " + self.active_question.answer)
        await self.send_text("Hints:")
        for hint in self.active_question.hints:
            await self.send_text(hint)
        for player in self.players:
            await self.send_text(f"{player.rank}. {player.username}: {player.points}")
        self.active_question = None
        if self.count == len(self.questions):
            await self.end_quiz()

    def reset_guesses(self):
        for player in self.players:
            player.guesses = 0
            player.correct_today = False

    async def end_quiz(self):
        for player in self.players:
            if player.rank == 1:
                await self.send_text("Herzlichen Glückwunsch " + player.username)
        await self.send_text(self.end_message)
        self.is_active = False

    async def user_answer(self, user_answer: discord.Message):
        for player in self.players:
            if player.user == user_answer.author:
                if player.correct_today or self.active_question is None:
                    return
                if user_answer.content == self.active_question.answer:
                    self.calculate_points(player)
                    player.correct_today = True
                    await user_answer.add_reaction('\N{white heavy check mark}')
                    await user_answer.reply(f"Damit hast du nun {player.points} Punkte.")
                    await self.all_correct_today()
                else:
                    player.guesses += 1
                    await user_answer.add_reaction('\N{negative squared cross mark}')
                    for x in range(3):
                        if player.guesses == self.active_question.max_guesses * (x + 1):
                            await user_answer.reply(self.active_question.hints[x])
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
        self.players.sort(key=lambda x: x.points, reverse=True)
        rank = 1
        for index, player in enumerate(self.players):
            player.rank = rank
            for x in range(index):
                if self.players[x].points == player.points:
                    player.rank = self.players[x].rank
            rank += 1

    def points_minus_one(self, user):
        for player in self.players:
            if player.user == user:
                player.points -= 1
