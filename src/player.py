import discord


class Player:
    def __init__(self, user: discord.User, username):
        self.username = username
        self.user = user
        self.points = 0
        self.guesses = 0
        self.rank = 1
        self.correct_today = False
