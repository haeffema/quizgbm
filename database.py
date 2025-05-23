from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from consts import QUIZ_FOLDER

Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    question = Column(String, default="")
    answer = Column(String, default="")
    category = Column(String, default="")
    guesses = Column(Integer, default=3)
    hint1 = Column(String, default="")
    hint2 = Column(String, default="")
    hint3 = Column(String, default="")
    info = Column(String, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, default="player")
    points = Column(Integer, default=0)
    answered = Column(Boolean, default=False)
    guesses = Column(Integer, default=0)


class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    start_message = Column(String, default="")
    end_message = Column(String, default="")
    started = Column(Boolean, default=False)
    table_message = Column(Integer, default=None)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String, default="")
    question_id = Column(Integer, ForeignKey("questions.id"))


engine = create_engine(f"sqlite:///{QUIZ_FOLDER}/data.db")

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


### QUESTION ###


def get_question(id: int) -> Question:
    return session.query(Question).filter(Question.id == id).first()


### USER ###


def add_user(id: int, username: str) -> None:
    new_user = User(id=id, username=username)
    session.add(new_user)
    session.commit()


def get_user(id: int) -> User:
    return session.query(User).filter(User.id == id).first()


def get_users() -> list[User]:
    return session.query(User).all()


def update_user(user: User) -> None:
    session.add(user)
    session.commit()


### DATA ###


def get_data() -> Data:
    return session.query(Data).first()


def update_data(data: Data) -> None:
    session.add(data)
    session.commit()


### MESSAGE ###


def get_messages(question_id) -> list[Message]:
    return session.query(Message).filter(Message.question_id == question_id)


def add_message(content) -> None:
    new_message = Message(content=content, question_id=get_data().question_id)
    session.add(new_message)
    session.commit()
