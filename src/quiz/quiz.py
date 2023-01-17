import discord
from discord.ext import commands


class Quiz:
    def __init__(self, players: list, questions: list, start_message: str, end_message: str):
        self.players = players
        self.channel = None
        self.questions = questions
        self.start_message = start_message
        self.end_message = end_message
        self.started = False

    async def start_quiz(self, ctx: discord.Message):
        self.channel = ctx.channel
        await self.send_text(self.start_message)
        self.started = True

    async def send_text(self, message: str):
        await self.channel.send(message)
