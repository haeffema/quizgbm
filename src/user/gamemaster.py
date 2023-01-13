from src.user.user import User


class GameMaster(User):
    def __init__(self, name, id):
        super().__init__(name, id)
