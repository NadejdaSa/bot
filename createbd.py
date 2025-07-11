import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = sq.Column(sq.Integer, primary_key=True)

    def __str__(self):
        return f'Users{self.id}'


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = sq.Column(sq.Integer, primary_key=True)
    russian_word = sq.Column(sq.String(length=50), unique=True)
    english_word = sq.Column(sq.String(length=50), unique=True)

    def __str__(self):
        return f'Vocabulary{self.id}: {self.russian_word}, {self.english_word}'


class Words_for_users(Base):
    __tablename__ = "words_for_users"

    id = sq.Column(sq.Integer, primary_key=True)
    id_users = sq.Column(sq.Integer, sq.ForeignKey("users.id"), nullable=False)
    id_vocabulary = sq.Column(sq.Integer, sq.ForeignKey("vocabulary.id"), nullable=False)

    users = relationship(Users, backref="Words_for_users")
    vocabulary = relationship(Vocabulary, backref="Words_for_users")

    def __str__(self):
        return f'Words_for_users{self.id}: {self.id_users}, {self.id_vocabulary}'


def create_tables(engine, drop=False):
    if drop:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
