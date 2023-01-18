class Question:
    def __init__(self, question_information: list):
        self.question = question_information[0]
        self.answer = question_information[1]
        self.hints = [question_information[2], question_information[3], question_information[4]]
        self.max_guesses = int(question_information[5])
