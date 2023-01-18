import discord

from src.quiz.question import Question


class Quiz:
    def __init__(self, channel, players: list, folder: str):
        self.players = players
        self.channel = channel
        self.folder = folder
        self.questions = []
        self.start_message = None
        self.end_message = None
        self.started = False
        self.count = 0
        self.generate_quiz()

    def generate_quiz(self):
        with open(self.folder + '/quiz.txt', encoding="utf-8") as setup:
            self.start_message = setup.readline()
            self.end_message = setup.readline()
            for question in setup.readlines():
                self.generate_question(question, self.folder)

    def generate_question(self, question_str: str, folder: str):
        question_information = question_str.split(";")
        self.questions.append(Question(question_information, folder))

    async def send_question(self):
        if self.count < len(self.questions):
            question: Question = self.questions[self.count]
            await self.send_image(discord.File(question.image))
            await self.send_text(question.question)
            self.count += 1
            return
        await self.end_quiz()

    async def start_quiz(self):
        if self.started:
            return
        await self.send_text(self.start_message)
        self.started = True

    async def end_quiz(self):
        await self.send_text(self.end_message)
        self.started = False

    async def send_image(self, image: discord.File):
        await self.channel.send(file=image)

    async def send_text(self, message: str):
        await self.channel.send(message)
