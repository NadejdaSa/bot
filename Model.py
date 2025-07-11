import sqlalchemy
import json
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from createbd import create_tables, Users, Vocabulary, Words_for_users
from translate import Translator
from sqlalchemy import func, and_
import random
import os
from sqlalchemy.sql import exists as sqlalchemy_exists
from dotenv import load_dotenv

load_dotenv()

translator = Translator(from_lang='russian', to_lang='english')


def create_connection(db_name, db_user, db_password, db_host, db_port, name_db):
    DSN = f'{db_name}://{db_user}:{db_password}@{db_host}:{db_port}/{name_db}'
    engine = sqlalchemy.create_engine(DSN)
    return engine

engine = create_connection(
    db_name=os.getenv('DB_NAME'),
    db_user=os.getenv('DB_USER'),
    db_password=os.getenv('DB_PASSWORD'),
    db_host=os.getenv('DB_HOST'),
    db_port=os.getenv('DB_PORT'),
    name_db=os.getenv('NAME_DB')
)


create_tables(engine)
Session = sessionmaker(bind=engine)
session = Session()


with open('js.json', 'r') as file:
    data = json.load(file)

for record in data:
    model = {
        'vocabulary': Vocabulary,
    }[record.get('model')]
    pk = record.get('pk')
    exists = session.query(model).filter_by(id=pk).first()
    if not exists:
        session.add(model(id=pk, **record.get('fields')))
session.commit()


def add_new_user_id(user_id):
    user = session.query(Users).filter(Users.id == user_id).first()
    if not user:
        session.add(Users(id=user_id))
        session.commit()


def add_new_word(user_id, fill_word):
    counter = 0
    existing = session.query(Vocabulary).filter(Vocabulary.russian_word == fill_word).first()
    if not existing:
        max_id = session.query(func.max(Vocabulary.id)).scalar()
        counter = (max_id or 0) + 1
        translation = translator.translate(fill_word)
        session.add(Vocabulary(id=counter, russian_word=fill_word, english_word=translation))
        session.commit()
    else:
        counter = existing.id

    exists_link = session.query(Words_for_users).filter(
        and_(Words_for_users.id_users == user_id, Words_for_users.id_vocabulary == counter)
            ).first()
    if not exists_link:
        session.add(Words_for_users(id_users=user_id, id_vocabulary=counter))
        session.commit()


def delete_word(user_id, delete_word):
    result = session.execute(sqlalchemy.select(Vocabulary.id).where(
        Vocabulary.russian_word == delete_word)
    ).scalars()
    flag = False
    for i in result:
        flag = True
        idd = i
        stmt = sqlalchemy.delete(Words_for_users).where(
            and_(
                Words_for_users.id_vocabulary == idd,
                Words_for_users.id_users == user_id))
        session.execute(stmt)
        count = session.query(Words_for_users).filter(
            Words_for_users.id_vocabulary == idd).count()
        if count == 0:
            tmt = sqlalchemy.delete(Vocabulary).where(Vocabulary.id == idd)
            session.execute(tmt)
    session.commit()
    return flag


def get_random_number_from_db(user_id=None):
    user_exists = session.query(sqlalchemy_exists().where(Users.id == user_id)).scalar()
    if not user_exists:
        random_vocab = session.query(Vocabulary).order_by(func.random()).first()
        if not random_vocab:
            return None
        random_number = random_vocab.id
    else:
        result = session.query(Words_for_users).filter(Words_for_users.id_users == user_id).all()
        user_ids = [r.id_vocabulary for r in result]
        all_ids = session.query(Vocabulary.id).all()
        all_ids = [row[0] for row in all_ids]
        if not all_ids:
            return None
        numbers = list(set(user_ids + all_ids))
        random_number = random.choice(numbers)
    r_w = session.query(Vocabulary.russian_word).filter(
        Vocabulary.id == random_number).first()[0]
    c_w = session.query(Vocabulary.english_word).filter(
        Vocabulary.id == random_number).first()[0]
    wrong_words_raw = session.query(Vocabulary.english_word)\
        .filter(Vocabulary.id != random_number)\
        .order_by(func.random()).limit(3).all()
    wrong_words = [w[0] for w in wrong_words_raw]
    while len(wrong_words) < 3:
        wrong_words += wrong_words
    w1, w2, w3 = wrong_words[:3]

    return r_w, c_w, w1, w2, w3
