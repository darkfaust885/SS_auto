create table if not exists users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    password TEXT,
    role INTEGER
);

create table if not exists auth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    token TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

create table if not exists producer (
    id_producer INTEGER PRIMARY KEY AUTOINCREMENT,
    name_priducer CHAR(30),
    adress CHAR(60),
    phone CHAR(15)
);

create table if not exists client (
    id_client INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name CHAR(30),
    last_name CHAR(30),
    middle_name CHAR(30),
    phone CHAR(15)
);

create table if not exists car (
    id_car INTEGER PRIMARY KEY AUTOINCREMENT,
    car_brand CHAR(30),
    car_model CHAR(30),
    years_of_cars_production INTEGER
);

create table if not exists auto_parts_warehouse (
    id_auto_part INTEGER PRIMARY KEY AUTOINCREMENT,
    id_car INTEGER,
    id_producer INTEGER,
    name_auto_part CHAR(50),
    car_model CHAR(30),
    car_brand CHAR(30),
    years_of_cars_production INTEGER,
    name_producer CHAR(30),
    price CHAR(12),
    FOREIGN KEY (id_producer) REFERENCES producer(id_producer),
    FOREIGN KEY (id_car) REFERENCES car(id_car)
);

create table if not exists orders (
    id_order INTEGER PRIMARY KEY AUTOINCREMENT,
    id_car INTEGER,
    id_auto_part INTEGER,
    id_client INTEGER,
    date_order CHAR(20),
    name_auto_part CHAR(30),
    car_brand CHAR(30),
    car_model CHAR(30),
    years_of_cars_production CHAR(30),
    quantity INTEGER,
    FOREIGN KEY (id_client) REFERENCES client(id_client),
    FOREIGN KEY (id_auto_part) REFERENCES auto_parts_warehouse(id_auto_part),
    FOREIGN KEY (id_car) REFERENCES car(id_car)
);