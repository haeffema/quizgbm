class Player:
    def __init__(self, player_information):
        self.name = player_information[0]
        self.id = int(player_information[1])
        self.points = 0
        self.guesses = 0
        self.rank = 1
        self.correct_today = False
