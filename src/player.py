class Player:
    def __init__(self, id, name):
        self.name = name
        self.id = id
        self.points = 0
        self.guesses = 0
        self.rank = 1
        self.correct_today = False
