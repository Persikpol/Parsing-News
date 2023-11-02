from bs4 import BeautifulSoup
import requests
import sqlite3
import re
import datetime
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import json
import csv
import hashlib
import os
import uuid
# from rutermextract import TermExtractor

url = 'https://www.coindesk.com/livewire/'
allNews = []

# Записываем HTML код

page = requests.get(url)
status = page.status_code
#print(status)
if(status != 200):
    print(url, " is not available. Status code : ", status )
soup = BeautifulSoup(page.text, "html.parser")
#print(soup)
allNews = soup.findAll('div', class_='card__Meta-sc-3i6u6z-1 fGEoXt')
for elem in allNews:
    pretty_html =  elem.prettify()
    print (pretty_html)
    print ('-'*20)


# Подключение к БД

conn = sqlite3.connect('db/my_news.db')
cur = conn.cursor()

# Создание таблицы с новостями

cur.execute('''
CREATE TABLE IF NOT EXISTS News (
date DATE,
link TEXT,
title TEXT PRIMARY KEY,
text TEXT
)
''')
conn.commit()

# Создание таблицы пользователей

cur.execute('''
CREATE TABLE IF NOT EXISTS Users (
uuid TEXT,
login TEXT PRIMARY KEY,
password TEXT
)
''')
conn.commit()

# Создание таблицы избранных новостей

cur.execute('''
CREATE TABLE IF NOT EXISTS Favorites (
id TEXT,
favorite_news TEXT,
FOREIGN KEY (favorite_news) REFERENCES News(link)
)
''')
conn.commit()

# Создание таблицы ключевых слов

cur.execute('''
CREATE TABLE IF NOT EXISTS Tags (
id TEXT,
key_tag TEXT,
FOREIGN KEY (id) REFERENCES Users(uuid)
)
''')
conn.commit()

# Запись новостей (дата, ссылка, заголовок и текст) в БД

for elem in allNews:
  d = elem.find('time')
  d1 = d.text
  d1 = d1.replace(',', '')
  d_t = datetime.strptime(d1, '%B %d %Y').date()
  patt = re.compile(r'href=[\'"]?([^\">]+)')
  l = re.findall(patt, str(elem))[0]
  full_l = 'https://www.coindesk.com' + l
  te = elem.find('p')
  te1 = te.text
  ti = elem.find('a', class_="headline__HeadlineLink-sc-1uoawmp-0 jbDMkW")
  ti1 = ti.text
  print(d1, '\n', full_l, '\n', te1, '\n', ti1 )
  try:
    cur.execute("INSERT INTO News VALUES(?, ?, ?, ?)", (d_t, full_l, ti1, te1))
  except:
    break
  
conn.commit()

# Показать все записи в БД

def show_news():
  cur.execute('SELECT * FROM News')
  news = cur.fetchall()

  for news in news:
    print(news)
    
# Дамп БД

fail_name = input('Введите имя файла в формате [ддммгггг_ччммсс].sql \n')
path = "db/" + fail_name
with open(path, "w") as f:
  for sql in conn.iterdump():
    f.write(sql)
    
# Восстановление БД из файла [name].sql (ввести имя файла на диске)
def data_recovery():
  fail_name = input('Введите имя файла в формате [File Name].sql \n')
  path = "db/" + fail_name
  with open(path, "r") as f:
    sql = f.read()
    cur.executescript(sql)
  
# Показать новости в заданном временном диапазоне

d1 = input('Введите начальную дату в формате дд мм гггг, без точек, через пробелы ')
d2 = input('Введите конечную дату в формате дд мм гггг, без точек, через пробелы ')
d_1 = datetime.strptime(d1, '%d %m %Y').date()
d_2 = datetime.strptime(d2, '%d %m %Y').date()
# d_2 = datetime.now().date()
# d_1 = d_2 - relativedelta(days=8)
# print(type(d_1), type(d_2))
# pattern = 'two'
cur.execute('SELECT * FROM News WHERE date BETWEEN (?) AND (?)', (d_1, d_2))
result1 = cur.fetchall()
for elem in result1:
    print(' \n'.join(elem))
    
# Удаление записи
def delete_news():
  pattern = input('Ведите ссылку на новость, которую хотите удалить: ')
  cur.execute('DELETE FROM News WHERE link LIKE ?', ('%'+pattern+'%',))
  result = cur.fetchall()
  cur.execute('SELECT * FROM News WHERE link LIKE ?', ('%'+pattern+'%',))
  result1 = cur.fetchall()
  if (len(result1) == 0):
    print("Запись удалена")
  else:
    print("Запись не была удалена")
    
# Поиск записи с определенными словами
def search():
  pattern = input('Введите слово, с которым хотите найти записи: ')
  cur.execute('SELECT * FROM News WHERE title LIKE ?', ('%'+pattern+'%',))
  res_tit = cur.fetchall()
  for elem in res_tit:
      print(' \n'.join(elem))
  cur.execute('SELECT * FROM News WHERE text LIKE ?', ('%'+pattern+'%',))
  res_text = cur.fetchall()
  for elem in res_text:
      print(' \n'.join(elem))
    
# Запись БД в файл JSON

cur.execute('SELECT * FROM News')
news = cur.fetchall()
list_for_json = []
title = []
for i in news:
  list_for_json.append({'date':i[0], 'title':i[2], 'text':i[3]})
for i in news:
  title.append(i[1])
dict_for_json = dict(zip(title, list_for_json))
news_json = json.dumps(dict_for_json)
with open("db/news.json", "w") as f:
    f.write(news_json)
    
# Запись БД в файл CSV

with open('db/news_SCV.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(news)
    
# Авторизация пользователя

def add_user(login: str, password: str) -> bool:
    """Добавляет пользователя в файл"""
    cur.execute('SELECT login FROM Users')
    users = cur.fetchall()  # Считываем всех пользователей из файла

    for user in users:
        args = user[0]
        if login == args:  # Если логин уже есть, пароль не проверяем, шанс взлома увеличится(кто-то мб узнает пароль)
            return False  # Тут можно написать что угодно, будь то HTML статус(409 - conflict), либо просто фразу ошибки
    UUID = str(uuid.uuid1())
    cur.execute('INSERT INTO Users (uuid, login, password) VALUES (?, ?, ?)', (UUID, login, password))
    return True


def get_user(login: str, password: str) -> bool:
    """Проверяет логин и пароль пользователя"""
    cur.execute('SELECT * FROM Users')
    users = cur.fetchall()  # Считываем всех пользователей из файла

    for user in users:
        if login == user[1] and password == user[2]:  # Если пользователь с таким логином и паролем существует
            return True
    return False


def add_favorite_news(login: str):
    show_news()
    favorite_news = input('Введите ссылку на новость, которая понравилась ')
    cur.execute('SELECT * FROM Users WHERE login LIKE ?', ('%'+login+'%',))
    user = cur.fetchall()
    for user in user:
      arg = user[0]   # Получаю UUID
    cur.execute('INSERT INTO Favorites (id, favorite_news) VALUES (?, ?)', (arg, favorite_news))
    print('Новость добавлена!')


def delete_favorite_news(login: str):
    favorite_news_for_delete = input('Введите ссылку на новость, которую хотите удалить ')
    cur.execute('SELECT * FROM Users WHERE login LIKE ?', ('%'+login+'%',))
    user = cur.fetchall()
    for user in user:
      arg = user[0]   # Получаю UUID
    cur.execute('DELETE FROM Favorites WHERE id = ? AND favorite_news = ?', (arg, favorite_news_for_delete))


def show_favorit_news(login: str):
    cur.execute('SELECT * FROM Users WHERE login LIKE ?', ('%'+login+'%',))
    user = cur.fetchall()
    for user in user:
      arg = user[0]   # Получаю UUID
    cur.execute('SELECT date, title, text, Favorites.favorite_news FROM Favorites JOIN News ON Favorites.favorite_news = News.link WHERE id = ?', (arg,))
    result = cur.fetchall()
    for res in result:
      print('\n'.join(elem))
      print('\n')


def count_favorites_news(login: str):
    cur.execute('SELECT * FROM Users WHERE login LIKE ?', ('%'+login+'%',))
    user = cur.fetchall()
    for user in user:
      arg = user[0]   # Получаю UUID
    cur.execute('SELECT COUNT(*) FROM Favorites WHERE id = ?', (arg,))
    result = cur.fetchall()
    for res in result:
      arg = res[0]
      print('Избранных новостей -  ', arg)


def show_recommended_news(login: str):
    d = datetime.now().date()
    d1 = d - relativedelta(days=20)
    cur.execute('SELECT uuid FROM Users WHERE login = ?', (login,))
    users = cur.fetchall()
    for user in users:
      arg = user[0]                     # Получаю UUID
    cur.execute('SELECT key_tag FROM Tags WHERE id = ?', (arg,))
    tags = cur.fetchall()               # Получаю избранные теги пользователя
    for tag in tags:
      pattern = tag[0]
      cur.execute("SELECT * FROM News WHERE date BETWEEN (?) AND (?) AND title LIKE ?", (d1, d, '%'+pattern+'%'))
      res_tit = cur.fetchall()
      for elem in res_tit:
        print('\n'.join(elem))
        print('\n')
      cur.execute("SELECT * FROM News WHERE date BETWEEN (?) AND (?) AND text LIKE ?", (d1, d, '%'+pattern+'%'))
      res_text = cur.fetchall()
      for elem in res_text:
        print('\n'.join(elem))
        print('\n')


def request_key_tags(login: str):
    tag = input('Введите тег (ключевое слово): ')
    cur.execute('SELECT * FROM Users WHERE login LIKE ?', ('%'+login+'%',))
    user = cur.fetchall()
    for user in user:
      arg = user[0]
    cur.execute('INSERT INTO Tags (id, key_tag) VALUES (?, ?)', (arg, tag))


def count_users():
    cur.execute('SELECT COUNT(*) FROM Users')
    result = cur.fetchall()
    for res in result:
      arg = res[0]
      print('Количество пользователей -  ', arg - 1)


def info_about_user():
    cur.execute('SELECT uuid, login FROM Users')
    users = cur.fetchall()
    for user in users:
      print(user)
    id = input('Введите UUID пользователя: ')
    print('Избранные новости пользователя')
    cur.execute('SELECT favorite_news FROM Favorites WHERE id = ?', (id, ))
    favorites = cur.fetchall()
    for favorite in favorites:
      print(favorite)
    print('Теги пользователя')
    cur.execute('SELECT key_tag FROM Tags WHERE id = ?', (id, ))
    favorites = cur.fetchall()
    for favorite in favorites:
      print(favorite)


def remove_news_from_everywhere():
    print('Все новости: ')
    show_news()
    pattern = input('Ведите ссылку на новость, которую хотите удалить: ')
    cur.execute('DELETE FROM News WHERE link LIKE ?', ('%'+pattern+'%',))
    result = cur.fetchall()
    cur.execute('SELECT * FROM News WHERE link LIKE ?', ('%'+pattern+'%',))
    result1 = cur.fetchall()
    if (len(result1) == 0):
      print("Запись удалена из общей таблицы")
    else:
      print("Запись не была удалена")
    cur.execute('DELETE FROM Favorites WHERE favorite_news LIKE ?', ('%'+pattern+'%',))
    result = cur.fetchall()
    cur.execute('SELECT * FROM Favorites WHERE favorite_news LIKE ?', ('%'+pattern+'%',))
    result1 = cur.fetchall()
    if (len(result1) == 0):
      print("Запись удалена у пользователей")
    else:
      print("Запись не была удалена")


def main_loop(login: str):
    """Главный цикл программы"""
    print(f'Привет, {login}!')  # Тут основная часть программы


while True:
    print('''Добро пожаловать! Выберите пункт меню:
    1. Вход
    2. Регистрация
    3. Зайти от имени администратора
    4. Выход
    ''')
    user_input = input()
    if user_input == '1':  # Условия можно заменить на: user_input.lower() == 'вход'
        print('Введите логин:')
        login = input()

        print('Введите пароль:')
        password = input()

        result = get_user(login, hashlib.sha256(password.encode()).hexdigest())

        if result:
            while True:
              print('''Вы вошли в систему. Выберите пункт меню:
              1. Выход
              2. Добавить запись в избранное
              3. Удалить запись из избранного
              4. Посмотреть избранное
              5. Узнать количество новостей в избранном
              6. Добавить теги (ключевые слова) для рекомендации новостей
              7. Показать рекомендованные новости
              ''')
              user_input_1 = input()
              if user_input_1 == '1':
                print('Завершение работы')
                break  # Выходим из цикла

              elif user_input_1 == '2':
                print('Добавить новость в избранное')
                add_favorite_news(login)

              elif user_input_1 == '3':
                print('Удалить новость из избранного')
                delete_favorite_news(login)

              elif user_input_1 == '4':
                print('Посмотреть свои новости')
                show_favorit_news(login)

              elif user_input_1 == '5':
                print('Узнать количество своих новостей')
                count_favorites_news(login)

              elif user_input_1 == '6':
                request_key_tags(login)

              elif user_input_1 == '7':
                show_recommended_news(login)

        else:
            print('Неверный логин или пароль')

    elif user_input == '2':
        print('Введите логин:')
        login = input()

        print('Введите пароль:')
        password = input()

        print('Повторите пароль:')
        password_repeat = input()

        if password != password_repeat:
            print('Пароли не совпадают!')
            continue

        result = add_user(login, hashlib.sha256(password.encode()).hexdigest())  # Вызываем функцию добавления пользователя. И хешируем пароль(безопасность)

        if not result:
            print('Пользователь с таким логином уже существует')
        else:
            print('Регистрация прошла успешно!')

    elif user_input == '3':
        print('Введите логин:')
        login = input()

        print('Введите пароль:')
        password = input()

        result = get_user(login, hashlib.sha256(password.encode()).hexdigest())

        if result:
            while True:
              print('''Вы вошли в систему. Выберите пункт меню:
              1. Выход
              2. Получить количество пользователей
              3. Получить информацию по UUID
              4. Удалить новость из общей базы и базы пользователей
              ''')
              admin_input = input()
              if admin_input == '1':
                print('Завершение работы')
                break  # Выходим из цикла

              elif admin_input == '2':
                count_users()

              elif admin_input == '3':
                info_about_user()

              elif admin_input == '4':
                remove_news_from_everywhere()

    elif user_input == '4':
        print('Завершение работы')
        break  # Выходим из цикла

conn.commit()

# # Автоматическое создание тегов статьи

# cur.execute('SELECT title, text FROM News')
# results = cur.fetchall()
# one_string = u''

# for res in results:
#   one_string = one_string + res[0]
# # print(one_string)
# term_extractor = TermExtractor()

# for term in term_extractor(one_string):
#   print (term.normalized, term.count)

