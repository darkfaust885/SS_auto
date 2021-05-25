import json
import sqlite3
from datetime import datetime, timedelta
from os import walk
from os.path import join

import bcrypt as bcrypt
from bottle import run, template, get, static_file, post, request, install, HTTPError
from bottlejwt import JwtPlugin

SECRET = "inerg908243ng23gf"
MIGRATIONS_PATH = "migrations"
STATIC_PATH = "static"

con = sqlite3.connect('data.db')
cur = con.cursor()
cur.execute('PRAGMA encoding="UTF-8";')

def get_hashed_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password.encode(), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password.encode(), hashed_password)


# пример метода, требующий авторизацию и роль не меньше 1
@get('/hello-auth/<name>', auth={"role": 1})
def index(auth, name):
    print(auth)
    return json.dumps({'text': f"Hello {name}!"})


# пример метода, не требующий авторизацию
@get('/hello/<name>')
def index2(name):
    return template('<b>Hello {{name}}</b>!', name=name)


@post('/api/auth')
def auth():
    data = json.loads(request.body.read())
    name = data.get("name")
    cur.execute("select * from users where name=:name", {'name': name})
    db_user = cur.fetchone()
    if not db_user:
        raise HTTPError(400, "Incorrect login or password")
    password = data.get("password")

    if db_user[2] == 'admin' and password == 'admin':
        pass
    elif not check_password(password, db_user[2]):
        raise HTTPError(400, "Incorrect login or password")

    exp = datetime.today() + timedelta(days=1)
    token = JwtPlugin.encode({'user_id': db_user[0], 'exp': exp})
    cur.execute("INSERT INTO auth (user_id, token) VALUES (?, ?)", (db_user[0], token))
    con.commit()
    return json.dumps({'token': token})


@post('/api/registration')
def registration():
    data = json.loads(request.body.read())
    name = data.get("name")
    password = data.get("password")
    salt = get_hashed_password(password)
    cur.execute("INSERT INTO users (name, password, role) VALUES (?, ?, ?)", (name, salt, 1))
    con.commit()
    return "ok"


# маппинг для статики
@get("<filepath:path>")
def static(filepath):
    # если пользователь зрит в корень - достаем из статики index.html
    if filepath == "/":
        filepath += "index.html"
    return static_file(filepath, root=STATIC_PATH)


# функция, для накатывания миграций
def migrate():
    # достаем файлы из папки с миграциями
    for (_, _, filenames) in walk(MIGRATIONS_PATH):
        # сортируем и идем по ним
        filenames.sort()
        for filename in filenames:
            # читаем каждый
            with open(join(MIGRATIONS_PATH, filename)) as f:
                # суем как скрипт в курсор
                cur.executescript(f.read())


# функция, вызываемая при проверке авторизации
def validation(auth, auth_value):
    # проверяем что токен свеж
    if datetime.fromtimestamp(auth['exp']) < datetime.now():
        return False
    # достаем последний токен из БД
    cur.execute("select * from auth where user_id=:user_id ORDER BY id DESC LIMIT 1", {"user_id": auth["user_id"]})
    db_auth = cur.fetchone()
    # если нет - говорим что авторизация не пройдена
    if not db_auth:
        return False
    # достаем юзера из БД
    cur.execute("select * from users where id=:id", {"id": db_auth[1]})
    db_user = cur.fetchone()
    # если нет - говорим что авторизация не пройдена
    if not db_user:
        return False
    # если есть роль в атрибуте декоратора, проверяем равна ли (или выше) требуемой роли у пользователя
    if auth_value['role']:
        return db_user[3] >= auth_value['role']
    else:
        # Иначе мы прошли авторизацию
        return True


if __name__ == '__main__':
    migrate()
    install(JwtPlugin(validation, SECRET, algorithm='HS256'))
    run(host='localhost', port=8080)