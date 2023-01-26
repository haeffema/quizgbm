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
        with open(self.folder + '/player.txt', encoding="utf-8") as setup:
            for player in setup.readlines():
                self.generate_player(player)

    def generate_question(self, question_str: str):
        question_information = question_str.split(";")
        self.questions.append(Question(question_information))

    def generate_player(self, player_str: str):
        player_information = player_str.split(";")
        self.players.append(Player(player_information))

    async def send_question(self):
        if self.active_question is not None:
            await self.reveal_answer()
        self.reset_guesses()
        if self.count < len(self.questions):
            self.active_question = self.questions[self.count]
            await self.send_image_of_question()
            await self.send_text(self.active_question.question)
            self.count += 1
        else:
            await self.end_quiz()

    async def start_quiz(self):
        if self.is_active:
            return
        texts = self.start_message.split("|")
        for text in texts:
            await self.send_text(text)
        self.is_active = True

    async def end_quiz(self):
        await self.send_text("Damit gewinnt " + self.players[0].name + "! Herzlichen Glückwunsch!")
        await self.send_text(self.end_message)
        self.is_active = False

    async def send_image_of_question(self):
        file = Path(self.folder + '/send' + str(self.count) + '.png')
        if file.exists():
            await self.channel.send(file=discord.File(self.folder + "/send" + str(self.count) + ".png"))

    async def send_text(self, message: str):
        await self.channel.send(message)

    async def send_player_text(self, message: str, player):
        await player.send(message)

    def reset_guesses(self):
        for player in self.players:
            player.guesses = 0
            player.correct_today = False

    async def user_answer(self, ctx: discord.Message):
        for player in self.players:
            if ctx.author.id == player.id:
                player.guesses += 1
                if self.active_question is None:
                    return
                if ctx.content == self.active_question.answer:
                    await ctx.add_reaction('\N{white heavy check mark}')
                    if self.active_question.max_guesses == 1:
                        player.points += 5 - player.guesses
                    elif player.guesses // self.active_question.max_guesses > 3:
                        player.points += 1
                    else:
                        player.points += 4 - player.guesses // self.active_question.max_guesses
                    player.correct_today = True
                    await self.all_correct_today()
                else:
                    await ctx.add_reaction('\N{negative squared cross mark}')
                    for x in range(3):
                        if player.guesses == self.active_question.max_guesses * (x + 1):
                            await self.send_player_text(self.active_question.hints[x], ctx.author)

    async def all_correct_today(self):
        for player in self.players:
            if not player.correct_today:
                return
        await self.reveal_answer()

    async def reveal_answer(self):
        await self.send_text("Die Lösung war: " + self.active_question.answer)
        await self.send_points()
        self.active_question = None

    async def send_points(self):
        self.players.sort(key=lambda x: x.points, reverse=True)
        rank = 1
        for index, player in enumerate(self.players):
            player.rank = rank
            for x in range(index):
                if self.players[x].points == player.points:
                    player.rank = self.players[x].rank
            await self.send_text(str(player.rank) + ". " + player.name + ": " + str(player.points))
            rank += 1
