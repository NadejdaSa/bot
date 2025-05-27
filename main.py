from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import random
import Model
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
import os

class CommandWord:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

# Вместо BOT TOKEN HERE нужно вставить токен вашего бота, полученный у @BotFather
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") #заполнить
# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    fill_word = State()  
    fill_deleted_word = State() 
    fill_c_w = State() # Состояние ожидания ввода слова


# Создаем объекты кнопок
start_word = KeyboardButton(text="Давай")
exit = KeyboardButton(text="Выход")
r_w, c_w, w1, w2, w3 = Model.get_random_number_from_db()
add_word = KeyboardButton(text=CommandWord.ADD_WORD)
delete_word = KeyboardButton(text=CommandWord.DELETE_WORD)
next_word = KeyboardButton(text=CommandWord.NEXT)


# Создаем объект клавиатуры, добавляя в него кнопки
keyboard1 = ReplyKeyboardMarkup(keyboard=[[start_word, add_word, delete_word, exit]], resize_keyboard=True,one_time_keyboard=True)
next_btn = KeyboardButton(text=CommandWord.NEXT)
add_word_btn = KeyboardButton(text=CommandWord.ADD_WORD)
delete_word_btn = KeyboardButton(text=CommandWord.DELETE_WORD)

# Этот хэндлер будет срабатывать на команду "/start" и отправлять в чат клавиатуру
@dp.message(Command(commands=["start","card"]))
async def process_start_command(message: Message):
    await message.answer(
        text= 
        'Привет 👋 Давай попрактикуемся в английском языке. \n Тренировки можешь проходить в удобном для себя темпе. \n У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения. Для этого воспрользуйся инструментами: \n добавить слово ➕, \n удалить слово 🔙.\n Ну что, начнём ⬇️',
        reply_markup=keyboard1
    )
# Этот хэндлер будет срабатывать на команду Выход и открывать начальное меню
@dp.message(F.text == "Выход", StateFilter(default_state))
async def end_command(message: Message, state: FSMContext):
    await message.answer(
        text= 
        "Попрактикуемся в следующий раз, до встречи!!!", reply_markup=keyboard1
    )
    await state.clear()


# Этот хэндлер будет срабатывать на ответ "Добавить слово ➕" и скрывать клавиатуру
@dp.message(F.text=='Добавить слово ➕', StateFilter(default_state))
async def process_add_word_answer(message: Message, state: FSMContext):
    user_id = message.chat.id
    Model.add_new_user_id(user_id)
    await message.answer(text='Пожалуйста, введите слово на русском языке')
    # Устанавливаем состояние ожидания ввода слова
    await state.set_state(FSMFillForm.fill_word)
    

# Этот хэндлер будет срабатывать, если введено корректное слово
# и переводить в состояние ожидания ввода слова
@dp.message(StateFilter(FSMFillForm.fill_word))
async def fill_db_russian_word(message: Message, state: FSMContext):
    user_id = message.chat.id
    fill_word=message.text
    Model.add_new_word(user_id,fill_word)
    await message.answer(text='Готово! Будем тренироваться?',
        reply_markup=keyboard1)
# Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()
    
# Этот хэндлер будет срабатывать на ответ "Удалить слово" 
@dp.message(F.text=='Удалить слово🔙', StateFilter(default_state))
async def process_delete_word(message: Message, state: FSMContext):
    await message.answer(text='Пожалуйста, введите слово, которое хотите удалить,на русском языке')
    # Устанавливаем состояние ожидания ввода слова
    await state.set_state(FSMFillForm.fill_deleted_word)

# Этот хэндлер будет срабатывать, если введено корректное слово
# и переводить в состояние ожидания ввода слова
@dp.message(StateFilter(FSMFillForm.fill_deleted_word))
async def fill_db_deleted_word(message: Message, state: FSMContext):
    user_id = message.chat.id
    delete_word=message.text
    if Model.delete_word(user_id,delete_word):
        await message.reply(f"Слово '{delete_word}' успешно удалено из базы данных.", reply_markup=keyboard1)
    else:
        await message.reply(f"Слово '{delete_word}' не найдено в базе данных.", reply_markup=keyboard1)
# Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@dp.message(F.text == "Давай", StateFilter(default_state))
async def start_command(message: Message, state: FSMContext):
    user_id = message.chat.id
    r_w, c_w, w1, w2, w3 = Model.get_random_number_from_db(user_id)
    print(c_w)
    # Сохраняем правильный ответ в состояние
    await state.update_data(correct_word=c_w)
    answers_keyboard = [KeyboardButton(text=c_w)] + [KeyboardButton(text=w1)] + [KeyboardButton(text=w2)] + [KeyboardButton(text=w3)]
    random.shuffle(answers_keyboard)
    builder = ReplyKeyboardBuilder()
    builder.row(*answers_keyboard,exit, width = 3)
    ans_keyboard_obj = builder.as_markup()
    await message.answer(
        text= 
        f"Выбери перевод слова:\n🇷🇺 {r_w}",
        reply_markup=ans_keyboard_obj
    )
    # Устанавливаем состояние ожидания ввода слова
    await state.set_state(FSMFillForm.fill_c_w)
    return r_w, c_w, w1, w2, w3


# Этот хэндлер будет срабатывать на правильный ответ 

@dp.message(StateFilter(FSMFillForm.fill_c_w))
async def process_answer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    c_w = user_data.get('correct_word')
    print(c_w)
    if message.text == c_w:
        await message.answer(
            text='Да, несомненно, вы правы!Продолжим?', reply_markup=keyboard1
        )
        await state.clear()
    else:
        await message.answer(
        text='К сожалению, вы ошиблись. Попробуйте снова'
    )
    

if __name__ == '__main__':
    dp.run_polling(bot)
