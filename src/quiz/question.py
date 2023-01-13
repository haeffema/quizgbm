class Question:
    def __init__(self, question, answer, hints, max_guesses, player_guesses):
        self.question = question
        self.answer = answer
        self.hints = hints
        self.max_guesses = max_guesses
        self.player_guesses = player_guesses
