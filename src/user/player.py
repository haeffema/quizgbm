from src.user.user import User


class Player(User):
    def __init__(self, id, name):
        User.__init__(self, id, name)
        self.points = 0
