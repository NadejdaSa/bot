import sqlalchemy
import json
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from createbd import create_tables, Users, Vocabulary, Words_for_users
from translate import Translator
from sqlalchemy.sql import text
from sqlalchemy import func
import random
known_users = []
translator = Translator(from_lang='russian', to_lang='english')


def create_connection(db_name, db_user, db_password, db_host, db_port, name_db):
    DSN = f'{db_name}://{db_user}:{db_password}@{db_host}:{db_port}/{name_db}'
    engine = sqlalchemy.create_engine (DSN)
    return engine
engine = create_connection() #заполнить


create_tables(engine)
Session = sessionmaker(bind=engine)
session = Session()

session.commit()

with open('js.json', 'r') as file:
    data = json.load(file)

for record in data:
    model = {
        'vocabulary': Vocabulary,
    }[record.get('model')]
    session.add(model(id=record.get('pk'), **record.get('fields')))
session.commit()


def add_new_user_id(user_id):
    if user_id not in known_users:
        session.add(Users(id=user_id))
        known_users.append(user_id)
        session.commit()
    

def add_new_word(user_id,fill_word):
    counter = 0
    if not session.query(Vocabulary).filter(Vocabulary.russian_word == fill_word).all():
        counter = session.execute(text("SELECT COUNT(*) FROM vocabulary")).scalar() + 1
        translation = translator.translate(fill_word)
        session.add(Vocabulary(id=counter,russian_word=fill_word,english_word=translation))
    else:
        result = session.execute(sqlalchemy.select(Vocabulary.id).where(Vocabulary.russian_word == fill_word)).scalars()
        for i in result:
            counter = i
    session.add(Words_for_users(id_users=user_id, id_vocabulary=counter))
    session.commit()

def delete_word(user_id,delete_word):
    result = session.execute(sqlalchemy.select(Vocabulary.id).where(Vocabulary.russian_word == delete_word)).scalars() 
    flag = False
    for i in result:
        flag = True
        idd = i
        stmt = sqlalchemy.delete(Words_for_users).where(Words_for_users.id_vocabulary == idd and Words_for_users.id_users == user_id)
        session.execute(stmt)
        tmt = sqlalchemy.delete(Vocabulary).where(Vocabulary.id == idd)
        session.execute(tmt)
    session.commit()
    return flag

def get_random_number_from_db(user_id=None):
    if user_id not in known_users:
        random_number = session.query(Vocabulary).order_by(func.random()).first().id
    else:
        result = session.query(Words_for_users).filter(Words_for_users.id_users == user_id)
        numbers = [i for i in range(1, 11)] + [i.id_vocabulary for i in result]
        random_number = random.choice(numbers)

    
    random_russian_word = session.execute(sqlalchemy.select(Vocabulary.russian_word).where(Vocabulary.id == random_number)).all()
    r_w = random_russian_word[0][0]
    correct_word = session.execute(sqlalchemy.select(Vocabulary.english_word).where(Vocabulary.russian_word == r_w)).all()
    c_w = correct_word[0][0]
    w = session.execute(sqlalchemy.select(Vocabulary.english_word).where(Vocabulary.russian_word != r_w).distinct().limit(3)).all()
    w1 = w[0][0]
    w2 = w[1][0]
    w3 = w[2][0]
    
    return r_w, c_w, w1, w2, w3




    
session.close()

