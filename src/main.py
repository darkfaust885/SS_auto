import json
import sqlite3
from datetime import datetime, timedelta
from os import walk
from os.path import join

import bcrypt as bcrypt
from bottle import run, template, get, static_file, post, request, install, HTTPError, delete, response
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


@get('/api/get-items')
def get_all_items():
    cur.execute("select * from auto_parts_warehouse")
    auto_parts_warehouses = cur.fetchall()

    cur.execute("select * from producer")
    producers = cur.fetchall()

    cur.execute("select * from car")
    cars = cur.fetchall()

    results = []
    for auto_parts_warehouse in auto_parts_warehouses:
        results.append({
            'id': auto_parts_warehouse[0],
            'car': next(
                ({'id': x[0], 'car_brand': x[1], 'car_model': x[2], 'years_of_cars_production': x[3]} for x in cars if
                 x[0] == auto_parts_warehouse[1]), {}),
            'producer': next(({'id': x[0], 'name_priducer': x[1], 'adress': x[2], 'phone': x[3]} for x in producers if
                              x[0] == auto_parts_warehouse[2]), {}),
            'name_auto_part': auto_parts_warehouse[3],
            'price': auto_parts_warehouse[4],
            'photo': auto_parts_warehouse[5]
        })
        
        response.content_type = 'application/json'
    return json.dumps(results)

@get('/api/get-orders', auth={"role": 1})
def get_orders(auth):
    cur.execute("select * from orders where id_client=:id_client", {'id_client': auth['user_id']})
    orders = cur.fetchall()

    cur.execute("select * from producer")
    producers = cur.fetchall()

    cur.execute("select * from auto_parts_warehouse")
    auto_parts_warehouses = cur.fetchall()

    cur.execute("select * from car")
    cars = cur.fetchall()

    results = []
    for order in orders:
        results.append({
            'id': order[0],
            'auto_part': next(({
                'id': auto_part[0],
                'car': next(
                    ({'id': x[0], 'car_brand': x[1], 'car_model': x[2], 'years_of_cars_production': x[3]} for x in cars
                     if x[0] == auto_part[1]), {}),
                'producer': next(
                    ({'id': x[0], 'name_priducer': x[1], 'adress': x[2], 'phone': x[3]} for x in producers if
                     x[0] == auto_part[2]), {}),
                'name_auto_part': auto_part[3],
                'price': auto_part[4],
                'photo': auto_part[5]
            } for auto_part in auto_parts_warehouses if auto_part[0] == order[1]), {}),
            'date_order': order[3],
            'quantity': order[4]
        })

    response.content_type = 'application/json'
    return json.dumps(results)


@post('/api/get-orders/add', auth={"role": 1})
def add_orders(auth):
    data = json.loads(request.body.read())

    id_auto_part = data['id_auto_part']
    if not id_auto_part:
        return HTTPError(400, 'id_auto_part missing')

    quantity = data.get('quantity', 1)

    cur.execute(
        "select quantity from orders where id_client=:id_client and id_auto_part=:id_auto_part",
        {'id_client': auth['user_id'], 'id_auto_part': id_auto_part}
    )
    db_quantity = cur.fetchone() or (0,)

    if db_quantity[0] > 0:
        cur.execute(
            "UPDATE orders SET quantity = quantity + :new_q where id_client=:id_client and id_auto_part=:id_auto_part",
            {'id_client': auth['user_id'], 'id_auto_part': id_auto_part, 'new_q': quantity}
        )
    else:
        cur.execute("INSERT INTO orders (id_auto_part, id_client, quantity) VALUES (?, ?, ?)",
                    (id_auto_part, auth['user_id'], quantity))

    con.commit()

    return 'ok'


@delete('/api/get-orders/all/<id>', auth={"role": 1})
def delete_order(auth, id):
    cur.execute(
        "DELETE FROM orders where id_client=:id_client and id_order=:id_order",
        {'id_client': auth['user_id'], 'id_order': id}
    )
    con.commit()
    return 'ok'


@delete('/api/get-orders/one/<id>', auth={"role": 1})
def delete_order(auth, id):
    params = {'id_client': auth['user_id'], 'id_order': id}
    cur.execute(
        "select quantity from orders where id_client=:id_client and id_order=:id_order",
        params
    )
    quantity = cur.fetchone() or 0
    if quantity > 1:
        cur.execute(
            "UPDATE orders SET quantity = quantity - 1 WHERE id_client=:id_client and id_order=:id_order",
            params
        )
    else:
        cur.execute(
            "DELETE FROM orders where id_client=:id_client and id_order=:id_order",
            params
        )
    con.commit()
    return 'ok'


@post('/api/auth')
def auth():
    data = json.loads(request.body.read())
    name = data.get("name")
    if not name:
        return HTTPError(400, 'name missing')
    cur.execute("select * from users where name=:name", {'name': name})
    db_user = cur.fetchone()
    if not db_user:
        raise HTTPError(400, "Incorrect login or password")
    password = data.get("password")
    if not password:
        return HTTPError(400, 'password missing')

    if db_user[2] == 'admin' and password == 'admin':
        pass
    elif not check_password(password, db_user[2]):
        raise HTTPError(400, "Incorrect login or password")

    exp = datetime.today() + timedelta(days=1)
    token = JwtPlugin.encode({'user_id': db_user[0], 'exp': exp})
    cur.execute("INSERT INTO auth (user_id, token) VALUES (?, ?)", (db_user[0], token))
    con.commit()
    response.content_type = 'application/json'
    return json.dumps({'token': token})


@post('/api/registration')
def registration():
    data = json.loads(request.body.read())

    name = data.get("name")
    if not name:
        return HTTPError(400, 'name missing')

    password = data.get("password")
    if not password:
        return HTTPError(400, 'password missing')

    first_name = data.get("first_name")
    if not first_name:
        return HTTPError(400, 'first_name missing')

    last_name = data.get("last_name")
    if not last_name:
        return HTTPError(400, 'last_name missing')

    middle_name = data.get("middle_name")
    if not middle_name:
        return HTTPError(400, 'middle_name missing')

    phone = data.get("phone")
    if not phone:
        return HTTPError(400, 'phone missing')

    salt = get_hashed_password(password)
    cur.execute(
        "INSERT INTO users (name, password, first_name, last_name, middle_name, phone, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, salt, first_name, last_name, middle_name, phone, 1)
    )
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
            with open(join(MIGRATIONS_PATH, filename), encoding='utf-8') as f:
                # суем как скрипт в курсор
                try:
                    cur.executescript(f.read())
                except Exception as err:
                    print(f"Migration error in '{filename}':", err)
                    exit(1)


# функция, вызываемая при проверке авторизации
def validation(auth, auth_value):
    if auth_value is not dict:
        return True
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

def get_filter(id_car):
    cur.execute("select * from auto_parts_warehouse where id_car=:id_car", {"id_car": id_car})
    id_car = cur.fetchone()

if __name__ == '__main__':
    migrate()
    install(JwtPlugin(validation, SECRET, algorithm='HS256'))
    run(host='localhost', port=8080)
