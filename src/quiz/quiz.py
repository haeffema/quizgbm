import discord

from src.quiz.question import Question


class Quiz:
    def __init__(self, channel, players: list, questions: list, start_message: str, end_message: str):
        self.players = players
        self.channel = channel
        self.questions = questions
        self.start_message = start_message
        self.end_message = end_message
        self.started = False
        self.count = 0

    async def send_question(self):
        question: Question = self.questions[self.count]
        await self.send_image(discord.File(question.image))
        await self.send_text(question.question)
        self.count += 1

    async def start_quiz(self):
        if self.started:
            return
        await self.send_text(self.start_message)
        self.started = True

    async def send_image(self, image: discord.File):
        await self.channel.send(file=image)

    async def send_text(self, message: str):
        await self.channel.send(message)
