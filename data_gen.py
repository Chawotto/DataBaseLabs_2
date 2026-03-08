import psycopg2
import random
import os
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker('ru_RU')

# --- КОНСТАНТЫ ИЗ ВАШЕГО СКРИПТА (AUTOSALON.TXT) ---

# Поставщики строго из дампа
SUPPLIERS_DB = [
    ("ООО \"БелАвтоСнаб\"", "г. Минск, ул. Промышленная, 15", 375173334455, 5),
    ("ИП \"МоторПлюс\"", "г. Гродно, ул. Заводская, 8", 375152789900, 4),
    ("ЗАО \"АвтоКомпонент\"", "г. Брест, ул. Московская, 210", 375162556677, 5),
    ("ООО \"ЕвроДеталь\"", "г. Гомель, пр. Ленина, 50", 375232112233, 3),
    ("ООО \"Надежный Поставщик\"", "г. Витебск, ул. Строителей, 3", 375212654321, 4),
    ("ООО \"ТрансЗапчасть\"", "г. Могилев, ул. Первомайская, 100", 375222987654, 4),
    ("ОДО \"Все для авто\"", "г. Минск, ул. Тимирязева, 125", 375172345678, 5),
    ("ООО \"АвтоЛайт\"", "г. Пинск, ул. Центральная, 12", 375165445566, 3),
    ("ИП \"ШинТорг\"", "г. Борисов, ул. Гагарина, 55", 375177712345, 4),
    ("ООО \"Немецкое Качество\"", "г. Минск, пр. Победителей, 111", 375173009988, 5)
]

# Логическая связка: Поставщик -> Марки машин (для реалистичности)
SUPPLIER_BRANDS = {
    "ООО \"БелАвтоСнаб\"": ["Geely"],
    "ООО \"Немецкое Качество\"": ["BMW", "Audi", "Mercedes-Benz"],
    "ООО \"Надежный Поставщик\"": ["Volkswagen", "Skoda"],
    "ООО \"ЕвроДеталь\"": ["Renault", "Kia", "Hyundai", "Peugeot"],
    "ООО \"ТрансЗапчасть\"": ["Lada", "UAZ"],
    # Остальные могут поставлять что угодно или запчасти
}

# Модели для генерации
CAR_MODELS_BASE = {
    "Geely": ["Coolray", "Atlas Pro", "Tugella", "Monjaro", "Okavango", "Emgrand"],
    "BMW": ["X5", "X3", "3-series", "5-series", "X6", "X7"],
    "Audi": ["A4", "A6", "Q5", "Q7", "Q8", "A8"],
    "Volkswagen": ["Polo", "Tiguan", "Passat", "Jetta", "Touareg", "Golf"],
    "Renault": ["Logan", "Duster", "Kaptur", "Arkana", "Sandero Stepway"],
    "Kia": ["Rio", "Sportage", "Ceed", "Seltos", "K5", "Sorento"],
    "Lada": ["Vesta", "Granta", "Largus", "Niva Travel", "Niva Legend"],
    "Skoda": ["Octavia", "Kodiaq", "Karoq", "Superb"],
    "Mercedes-Benz": ["E-Class", "C-Class", "GLE", "GLS"],
    "Hyundai": ["Solaris", "Creta", "Tucson", "Santa Fe"],
    "Peugeot": ["3008", "5008", "208"]
}

PARTS_DATA = [
    ("Фильтр масляный", 25.50, ["Bosch", "Mann-Filter"], "Высокое"),
    ("Колодки тормозные", 120.00, ["Brembo", "TRW", "ATE"], "Высокое"),
    ("Свеча зажигания", 15.00, ["NGK", "Denso"], "Высокое"),
    ("Фильтр воздушный", 35.80, ["Mann-Filter", "Filtron"], "Высокое"),
    ("Ремень ГРМ", 95.00, ["Gates", "Contitech"], "Высокое"),
    ("Аккумулятор", 280.00, ["Varta", "Exide"], "Высокое"),
    ("Масло моторное 5W-30 (4л)", 110.00, ["Motul", "Castrol"], "Высокое"),
    ("Амортизатор", 180.00, ["Kayaba", "Sachs"], "Среднее"),
    ("Шина летняя R16", 190.00, ["Continental", "Michelin"], "Высокое"),
    ("Шина зимняя R16", 220.00, ["Nokian", "Bridgestone"], "Высокое"),
    ("Сцепление (комплект)", 450.00, ["LuK", "Valeo"], "Высокое")
]

EMPLOYEE_TITLES = [
    "Директор", "Главный механик", "Менеджер по продажам", "Администратор",
    "Автомеханик", "Бухгалтер", "Специалист по диагностике",
    "Менеджер по работе с клиентами", "Автоэлектрик", "Специалист по закупкам"
]

CITIES_RB = ["г. Минск", "г. Гомель", "г. Брест", "г. Витебск", "г. Гродно", "г. Могилев", "г. Борисов", "г. Солигорск",
             "г. Жодино"]
STREETS_RB = ["ул. Ленина", "ул. Советская", "пр. Независимости", "ул. Якуба Коласа", "ул. Притыцкого",
              "ул. Московская", "ул. Кирова", "ул. Гагарина", "ул. Первомайская"]


# --- ФУНКЦИИ ---

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD')
    )


def generate_rb_phone():
    # Формат: 375 + код (29,33,44,25) + 7 цифр
    return int(f"375{random.choice([29, 33, 44, 25])}{random.randint(1000000, 9999999)}")


def generate_rb_passport():
    # Формат из вашего дампа: 7 цифр (BIGINT)
    return random.randint(1000000, 9999999)


def generate_rb_address():
    city = random.choice(CITIES_RB)
    street = random.choice(STREETS_RB)
    house = random.randint(1, 150)
    apt = random.randint(1, 200)
    # Формат: г. Минск, ул. Якуба Коласа, 28, кв. 15
    return f"{city}, {street}, {house}, кв. {apt}"


def clear_data(cur):
    print("Очистка таблиц...")
    tables = [
        '"Room-Order"', '"Service_name-Order_number"', '"Order"', '"Room"',
        '"Services"', '"Car"', '"Parts"', '"Supplier"', '"Client"', '"Employee"'
    ]
    for table in tables:
        try:
            cur.execute(f'TRUNCATE TABLE {table} CASCADE')
        except psycopg2.errors.UndefinedTable:
            pass


def run_generation():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        clear_data(cur)

        # 1. ПОСТАВЩИКИ (Строго из списка)
        print("1. Заполнение поставщиков...")
        for sup in SUPPLIERS_DB:
            cur.execute(
                'INSERT INTO "Supplier" ("Sup_name", "Address", "Phone", "Rating") VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
                sup
            )

        # 2. ЗАПЧАСТИ
        print("2. Заполнение запчастей...")
        parts_list = []
        for p_name, base_price, manufacturers, quality in PARTS_DATA:
            for manuf in manufacturers:
                full_name = f"{p_name} {manuf}"
                price = base_price * random.uniform(0.9, 1.2)
                # Выбираем поставщика, который мог бы это поставить (или любого)
                sup_name = random.choice(SUPPLIERS_DB)[0]

                cur.execute(
                    'INSERT INTO "Parts" ("Part_name", "Price", "Manufacturer", "Quality", "Sup_name") VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                    (full_name, round(price, 2), manuf, quality, sup_name)
                )
                parts_list.append(full_name)

        # 3. УСЛУГИ
        print("3. Заполнение услуг...")
        services_list = []
        for part in parts_list:
            if "Шина" in part:
                s_name = f"Шиномонтаж: {part}"
                duration = 60
            elif "Масло" in part:
                s_name = f"Замена масла: {part}"
                duration = 30
            else:
                s_name = f"Замена/Установка: {part}"
                duration = random.randint(40, 180)

            price_work = random.randint(30, 150)
            # Нужно найти цену запчасти
            cur.execute('SELECT "Price" FROM "Parts" WHERE "Part_name" = %s', (part,))
            part_price = cur.fetchone()[0]
            total = float(part_price) + price_work

            cur.execute(
                'INSERT INTO "Services" ("Service_name", "Price", "Total_cost", "Duration", "Part_name") VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (s_name, price_work, total, duration, part)
            )
            services_list.append(s_name)

        # 4. СОТРУДНИКИ
        print("4. Заполнение сотрудников...")
        employees_list = []
        for _ in range(20):
            phone = generate_rb_phone()
            name = fake.name()
            title = random.choice(EMPLOYEE_TITLES)
            exp = random.randint(1, 20)  # INT, так как в create_schema.sql это INT

            cur.execute(
                'INSERT INTO "Employee" ("Phone", "Name", "Title", "Experience") VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (phone, name, title, exp)
            )
            employees_list.append(phone)

        # 5. КЛИЕНТЫ
        print("5. Заполнение клиентов (РБ)...")
        clients_list = []
        for _ in range(100):
            passport = generate_rb_passport()
            name = fake.name()
            addr = generate_rb_address()
            phone = generate_rb_phone()

            cur.execute(
                'INSERT INTO "Client" ("Passport_number", "Name", "Address", "Phone") VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (passport, name, addr, phone)
            )
            clients_list.append(passport)

        # 6. АВТОМОБИЛИ (МНОГО!)
        print("6. Заполнение автомобилей (Большой объем)...")
        cars_list = []
        # Генерируем 150 автомобилей разных комплектаций
        for i in range(150):
            # Пытаемся найти подходящего поставщика
            brand_keys = list(CAR_MODELS_BASE.keys())
            brand = random.choice(brand_keys)
            model = random.choice(CAR_MODELS_BASE[brand])

            # Ищем поставщика для этого бренда
            supplier = None
            for sup_name, brands in SUPPLIER_BRANDS.items():
                if brand in brands:
                    supplier = sup_name
                    break
            if not supplier:
                supplier = random.choice(SUPPLIERS_DB)[0]  # Если нет спец. поставщика, берем любого

            year = random.randint(2018, 2024)
            base_price = 20000 if brand in ["Lada", "Renault"] else 50000
            if brand in ["BMW", "Audi", "Mercedes-Benz"]: base_price = 90000
            price = round(base_price * random.uniform(0.8, 1.5), 2)

            # Уникальное имя модели: Бренд Модель Год (ID)
            car_model_name = f"{brand} {model} {year} [ID:{1000 + i}]"

            cur.execute(
                'INSERT INTO "Car" ("Car_model", "Brand", "Year", "Price", "Sup_name") VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (car_model_name, brand, year, price, supplier)
            )
            cars_list.append(car_model_name)

        # 7. ПОМЕЩЕНИЯ
        print("7. Заполнение помещений...")
        for i in range(1, 15):
            addr = f"г. Минск, ул. Автомобилистов, 1, Бокс {i}"
            sq = random.choice([50.0, 75.0, 100.0])
            appt = random.choice(["Пост диагностики", "Пост ремонта", "Пост шиномонтажа", "Склад"])
            floor = 1
            srv = random.choice(services_list) if random.random() > 0.6 else None

            cur.execute(
                'INSERT INTO "Room" ("Address", "Square", "Appointment", "Floor", "Service_name") VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (addr, sq, appt, floor, srv)
            )

        # 8. ЗАКАЗЫ (МНОГО!)
        print("8. Генерация 500 заказов...")
        orders_generated = 0
        for i in range(1, 501):
            num = 1000 + i
            cost = round(random.uniform(50, 10000), 2)
            prio = random.randint(1, 3)
            status = random.choice(["Новый", "В работе", "Ожидает запчасть", "Выполнен", "Отменен"])

            cli = random.choice(clients_list)
            car = random.choice(cars_list)
            emp = random.choice(employees_list)

            cur.execute(
                'INSERT INTO "Order" ("Number", "Cost", "Priority", "Status", "Client_passport", "Car_model", "Employee_phone") VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (num, cost, prio, status, cli, car, emp)
            )
            orders_generated += 1

        conn.commit()
        print(f"Готово! База данных успешно заполнена реалистичными данными (Заказов: {orders_generated}).")

    except Exception as e:
        print("Ошибка:", e)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    run_generation()