class Question:
    def __init__(self, question_information: list):
        self.category = question_information[0]
        self.question = question_information[1]
        self.answer = question_information[2]
        self.hints = [question_information[3], question_information[4], question_information[5]]
        self.max_guesses = int(question_information[6])
