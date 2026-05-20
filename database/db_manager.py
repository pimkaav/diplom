import os
import sys
import hashlib
import uuid
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Locate .env next to the .exe when frozen, or in the project root from source.
_env_path = (
    Path(sys.executable).parent / ".env"
    if getattr(sys, "frozen", False)
    else Path(__file__).parent.parent / ".env"
)
load_dotenv(_env_path)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/freight_exchange",
)


def hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), b"freight_salt_2024", 100_000
    ).hex()


class DatabaseManager:
    _instance = None
    _pool: "pool.SimpleConnectionPool | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _init_pool(self):
        if DatabaseManager._pool is None:
            DatabaseManager._pool = pool.SimpleConnectionPool(
                1, 10, DATABASE_URL, cursor_factory=RealDictCursor
            )

    @contextmanager
    def get_connection(self):
        """Yields a psycopg2 connection; commits on success, rolls back on error."""
        self._init_pool()
        conn = DatabaseManager._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            DatabaseManager._pool.putconn(conn)

    def initialize(self):
        with self.get_connection() as conn:
            self._create_tables(conn)
            self._seed_data(conn)

    # ── Schema ────────────────────────────────────────────────────

    def _create_tables(self, conn):
        cur = conn.cursor()
        statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                username      TEXT    UNIQUE NOT NULL,
                email         TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL CHECK(role IN ('customer','carrier','admin')),
                full_name     TEXT,
                phone         TEXT,
                city          TEXT,
                bio           TEXT,
                avatar_path   TEXT,
                rating        REAL    DEFAULT 0.0,
                rating_count  INTEGER DEFAULT 0,
                is_active     INTEGER DEFAULT 1,
                balance       REAL    DEFAULT 0.0,
                theme         TEXT    DEFAULT 'dark',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS company_profiles (
                id               SERIAL PRIMARY KEY,
                user_id          INTEGER UNIQUE NOT NULL,
                company_name     TEXT    NOT NULL,
                description      TEXT,
                truck_count      INTEGER DEFAULT 0,
                truck_categories TEXT,
                price_per_km     REAL    DEFAULT 0.0,
                operating_cities TEXT,
                phone            TEXT,
                email            TEXT,
                website          TEXT,
                inn              TEXT,
                license_number   TEXT,
                completed_orders INTEGER DEFAULT 0,
                rating           REAL    DEFAULT 0.0,
                rating_count     INTEGER DEFAULT 0,
                is_verified      INTEGER DEFAULT 0,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS trucks (
                id             SERIAL PRIMARY KEY,
                carrier_id     INTEGER NOT NULL,
                brand          TEXT    NOT NULL,
                model          TEXT    NOT NULL,
                year           INTEGER,
                plate_number   TEXT,
                cargo_type     TEXT,
                capacity_tons  REAL    DEFAULT 20.0,
                volume_m3      REAL    DEFAULT 82.0,
                is_available   INTEGER DEFAULT 1,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (carrier_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id                             SERIAL PRIMARY KEY,
                customer_id                    INTEGER NOT NULL,
                carrier_id                     INTEGER,
                invited_carrier_id             INTEGER,
                title                          TEXT    NOT NULL,
                cargo_type                     TEXT,
                cargo_weight                   REAL,
                cargo_volume                   REAL,
                from_city                      TEXT    NOT NULL,
                to_city                        TEXT    NOT NULL,
                from_address                   TEXT,
                to_address                     TEXT,
                from_lat                       REAL,
                from_lng                       REAL,
                to_lat                         REAL,
                to_lng                         REAL,
                distance                       REAL,
                pickup_date                    TEXT    NOT NULL,
                delivery_date                  TEXT,
                budget                         REAL,
                final_cost                     REAL,
                status                         TEXT DEFAULT 'new'
                    CHECK(status IN ('new','in_progress','completed','cancelled')),
                progress_status                TEXT DEFAULT 'waiting',
                driver_name                    TEXT,
                truck_number                   TEXT,
                truck_model                    TEXT,
                dispatch_confirmed_by_customer INTEGER DEFAULT 0,
                arrival_confirmed_by_customer  INTEGER DEFAULT 0,
                dispatch_confirmed_at          TIMESTAMP,
                arrival_confirmed_at           TIMESTAMP,
                comment                        TEXT,
                special_requirements           TEXT,
                created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)        REFERENCES users(id),
                FOREIGN KEY (carrier_id)         REFERENCES users(id),
                FOREIGN KEY (invited_carrier_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS order_responses (
                id             SERIAL PRIMARY KEY,
                order_id       INTEGER NOT NULL,
                carrier_id     INTEGER NOT NULL,
                message        TEXT,
                proposed_cost  REAL,
                estimated_days INTEGER,
                status         TEXT DEFAULT 'pending'
                    CHECK(status IN ('pending','accepted','rejected')),
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id)   REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (carrier_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id               SERIAL PRIMARY KEY,
                reviewer_id      INTEGER NOT NULL,
                reviewed_user_id INTEGER NOT NULL,
                order_id         INTEGER,
                rating           INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment          TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reviewer_id)      REFERENCES users(id),
                FOREIGN KEY (reviewed_user_id) REFERENCES users(id),
                FOREIGN KEY (order_id)         REFERENCES orders(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
                id              SERIAL PRIMARY KEY,
                sender_id       INTEGER NOT NULL,
                receiver_id     INTEGER NOT NULL,
                order_id        INTEGER,
                content         TEXT,
                attachment_path TEXT,
                is_read         INTEGER DEFAULT 0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id)   REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id),
                FOREIGN KEY (order_id)    REFERENCES orders(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id         SERIAL PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                type       TEXT    NOT NULL,
                title      TEXT    NOT NULL,
                message    TEXT,
                is_read    INTEGER DEFAULT 0,
                related_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS payments (
                id             SERIAL PRIMARY KEY,
                order_id       INTEGER UNIQUE NOT NULL,
                amount         REAL    NOT NULL,
                status         TEXT    DEFAULT 'pending'
                    CHECK(status IN ('pending','held','released','refunded')),
                transaction_id TEXT,
                payer_id       INTEGER,
                receiver_id    INTEGER,
                held_at        TIMESTAMP,
                released_at    TIMESTAMP,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id)    REFERENCES orders(id),
                FOREIGN KEY (payer_id)    REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
            """,
        ]
        for stmt in statements:
            cur.execute(stmt)

    # ── Seed ──────────────────────────────────────────────────────

    def _seed_data(self, conn):
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
        if cur.fetchone():
            return

        p = hash_password("pass123")

        # ── Users ─────────────────────────────────────────────────
        cur.execute(
            "INSERT INTO users (username,email,password_hash,role,full_name,city,balance,theme) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            ("admin", "admin@freight.ru", hash_password("admin123"),
             "admin", "Администратор системы", "Москва", 0.0, "dark"),
        )

        users = [
            # customers
            ("customer1", "c1@mail.ru", p, "customer", "Иван Петров",
             "+7 (999) 111-22-33", "Москва",
             "Занимаюсь регулярными перевозками производственного оборудования. "
             "Работаю с проверенными перевозчиками, ценю пунктуальность.", 75000.0),
            ("customer2", "c2@mail.ru", p, "customer", "Мария Смирнова",
             "+7 (916) 222-33-44", "Москва",
             "Малый бизнес — периодические перевозки мебели и бытовых товаров. "
             "Ценю аккуратность и бережное обращение с грузом.", 50000.0),
            ("customer3", "c3@mail.ru", p, "customer", "Алексей Козлов",
             "+7 (926) 333-44-55", "Химки",
             "Строительный бизнес. Перевожу стройматериалы, конструкции, оборудование. "
             "Объёмы большие, ищу постоянных партнёров.", 120000.0),
            ("customer4", "c4@mail.ru", p, "customer", "Ольга Новикова",
             "+7 (812) 444-55-66", "Санкт-Петербург",
             "Оптовые поставки продуктов питания в розничные сети. "
             "Требования: температурный режим, соблюдение сроков.", 85000.0),
            ("customer5", "c5@mail.ru", p, "customer", "Дмитрий Захаров",
             "+7 (343) 555-66-77", "Екатеринбург",
             "Промышленное предприятие. Перевозка тяжёлого оборудования "
             "и металлоконструкций по всей России.", 200000.0),
            ("customer6", "c6@mail.ru", p, "customer", "Светлана Морозова",
             "+7 (843) 666-77-88", "Казань",
             "Интернет-магазин. Сборные грузы, малые партии товаров. "
             "Нужна частая и надёжная доставка.", 30000.0),
            # carriers
            ("carrier1", "r1@mail.ru", p, "carrier", "ООО ТрансГрупп",
             "+7 (999) 444-55-66", "Москва",
             "Профессиональные перевозки с 2010 года. Собственный парк из 25 автомобилей. "
             "Все виды грузов, любые расстояния.", 28500.0),
            ("carrier2", "r2@mail.ru", p, "carrier", "ИП Сидоров А.В.",
             "+7 (999) 777-88-99", "Балашиха",
             "Перевозки по Московской области. Быстро, аккуратно, без посредников. "
             "3 собственных автомобиля.", 14200.0),
            ("carrier3", "r3@mail.ru", p, "carrier", "ООО ЛогистикПро",
             "+7 (495) 555-66-77", "Москва",
             "Специализация: рефрижераторные перевозки продуктов и медикаментов. "
             "GPS-мониторинг, 8 лет на рынке.", 9800.0),
            ("carrier4", "r4@mail.ru", p, "carrier", "ИП Никитин Е.В.",
             "+7 (903) 666-77-88", "Подольск",
             "Негабаритные и тяжеловесные грузы. Манипулятор до 10 т. "
             "Все разрешения имеются.", 0.0),
            ("carrier5", "r5@mail.ru", p, "carrier", "ВолгаТранс",
             "+7 (831) 777-88-99", "Нижний Новгород",
             "Грузоперевозки по Поволжью и всей России. 18 автомобилей. "
             "Работаем с юр. и физ. лицами, договоры, НДС.", 42000.0),
            ("carrier6", "r6@mail.ru", p, "carrier", "СибЭкспресс",
             "+7 (383) 888-99-00", "Новосибирск",
             "Перевозки по Сибири и Дальнему Востоку. 22 автомобиля. "
             "Зерновозы, рефрижераторы, тенты.", 17600.0),
        ]
        cur.executemany(
            "INSERT INTO users "
            "(username,email,password_hash,role,full_name,phone,city,bio,balance) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            users,
        )

        def uid(uname: str) -> int:
            cur.execute("SELECT id FROM users WHERE username=%s", (uname,))
            return cur.fetchone()["id"]

        cu1, cu2, cu3, cu4, cu5, cu6 = (uid(f"customer{i}") for i in range(1, 7))
        c1, c2, c3, c4, c5, c6 = (uid(f"carrier{i}") for i in range(1, 7))

        # ── Company profiles ───────────────────────────────────────
        companies = [
            (c1, "ТрансГрупп",
             "Перевозим любые грузы по Москве, МО и всей России. Работаем с 2010 года. "
             "Собственный автопарк из 25 автомобилей. Полное страхование груза. "
             "Более 87 успешных доставок. Клиенты — крупные предприятия и торговые сети.",
             25, "Тентованные, Рефрижераторы, Бортовые, Фургоны", 42.0,
             "Москва, Санкт-Петербург, Нижний Новгород, Казань, Екатеринбург, Краснодар",
             "+7 (999) 444-55-66", "info@transgroup.ru", "https://transgroup.ru",
             87, 4.7, 23, 1),
            (c2, "ИП Сидоров",
             "Перевозки по Московской области и соседним регионам. "
             "Аккуратно и в срок. Работаем с физическими и юридическими лицами. "
             "3 собственных грузовика, все в отличном техническом состоянии.",
             3, "Тентованные, Бортовые, Фургоны", 35.0,
             "Балашиха, Электросталь, Ногинск, Щёлково, Реутов, Жуковский",
             "+7 (999) 777-88-99", "sidorov@mail.ru", "",
             34, 4.4, 11, 0),
            (c3, "ЛогистикПро",
             "Рефрижераторные перевозки продуктов питания и медикаментов. "
             "Сертифицированный автопарк, GPS-мониторинг, 8 лет опыта. "
             "Маршруты: Москва — СПб — Нижний — Казань. HACCP-сертификат.",
             12, "Рефрижераторы, Изотермы", 55.0,
             "Москва, Санкт-Петербург, Нижний Новгород, Казань, Тверь",
             "+7 (495) 555-66-77", "info@logistpro.ru", "https://logistpro.ru",
             56, 4.8, 18, 1),
            (c4, "ИП Никитин — Негабарит",
             "Специализация: негабаритные и тяжеловесные грузы. "
             "Разрешения на все типы грузов. Манипулятор до 10 т, платформа до 40 т. "
             "Перевозим станки, конструкции, строительную технику.",
             5, "Негабаритные, Манипулятор, Платформа, Тяжеловесные", 68.0,
             "Москва, Подольск, Серпухов, Тула, Рязань",
             "+7 (903) 666-77-88", "nikitin@mail.ru", "",
             19, 4.2, 7, 0),
            (c5, "ВолгаТранс",
             "Грузоперевозки по Поволжью и всей России с 2014 года. "
             "18 автомобилей: тенты, рефрижераторы, бортовые. "
             "Заключаем договоры, НДС, полная документация. "
             "Более 63 успешных рейсов.",
             18, "Тентованные, Рефрижераторы, Бортовые", 38.0,
             "Нижний Новгород, Казань, Самара, Уфа, Москва, Саратов",
             "+7 (831) 777-88-99", "info@volgatrans.ru", "https://volgatrans.ru",
             63, 4.6, 17, 1),
            (c6, "СибЭкспресс",
             "Перевозки по Сибири, Уралу и Дальнему Востоку. "
             "22 автомобиля: зерновозы, рефрижераторы, тентованные. "
             "Работаем с сельхозпредприятиями, торговыми сетями, заводами.",
             22, "Тентованные, Рефрижераторы, Зерновозы, Самосвалы", 45.0,
             "Новосибирск, Омск, Томск, Кемерово, Барнаул, Красноярск, Иркутск",
             "+7 (383) 888-99-00", "info@sibexpress.ru", "",
             41, 4.5, 14, 0),
        ]
        cur.executemany(
            """INSERT INTO company_profiles
               (user_id,company_name,description,truck_count,truck_categories,
                price_per_km,operating_cities,phone,email,website,
                completed_orders,rating,rating_count,is_verified)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            companies,
        )

        # ── Trucks ────────────────────────────────────────────────
        trucks = [
            # ТрансГрупп (c1)
            (c1, "Mercedes-Benz", "Actros 1845", 2022, "А 123 МК 77", "Тентованные", 20.0, 92.0, 1),
            (c1, "Volvo", "FH 500", 2021, "В 456 НП 77", "Тентованные", 20.0, 92.0, 0),
            (c1, "MAN", "TGX 18.500", 2020, "С 789 ОР 77", "Рефрижераторы", 20.0, 82.0, 1),
            (c1, "Scania", "R 500", 2021, "Т 012 СТ 77", "Бортовые", 20.0, 0.0, 1),
            (c1, "DAF", "XF 480", 2023, "У 345 УФ 77", "Тентованные", 20.0, 92.0, 1),
            # ИП Сидоров (c2)
            (c2, "Газель", "Next БИЗНЕС", 2020, "Е 567 ОП 50", "Бортовые", 1.5, 9.0, 1),
            (c2, "ГАЗ", "Газон Next", 2019, "Ж 890 РС 50", "Тентованные", 4.0, 18.0, 0),
            (c2, "КАМАЗ", "5490-S5", 2021, "И 123 ТУ 50", "Бортовые", 20.0, 0.0, 1),
            # ЛогистикПро (c3)
            (c3, "Schmitz Cargobull", "SKO 24", 2022, "К 456 ФХ 77", "Рефрижераторы", 22.0, 82.0, 1),
            (c3, "Кrone", "Cool Liner", 2021, "Л 789 ЦЧ 77", "Рефрижераторы", 22.0, 82.0, 0),
            (c3, "Thermoking", "MD-200", 2020, "М 012 ШЩ 77", "Изотермы", 10.0, 40.0, 1),
            # ИП Никитин (c4)
            (c4, "КАМАЗ", "65117-48", 2019, "Н 345 ЪЫ 50", "Платформа", 20.0, 0.0, 1),
            (c4, "Liebherr", "LTF 1045", 2018, "О 678 ЬЭ 50", "Манипулятор", 12.0, 0.0, 1),
            # ВолгаТранс (c5)
            (c5, "Volvo", "FM 410", 2021, "П 901 ЮЯ 52", "Тентованные", 20.0, 92.0, 1),
            (c5, "Mercedes-Benz", "Atego 1524", 2020, "Р 234 АБ 52", "Бортовые", 8.0, 0.0, 0),
            (c5, "Schmitz Cargobull", "SFR 24", 2022, "С 567 ВГ 52", "Рефрижераторы", 22.0, 82.0, 1),
            # СибЭкспресс (c6)
            (c6, "КАМАЗ", "6520-73", 2020, "Т 890 ДЕ 54", "Самосвалы", 20.0, 0.0, 1),
            (c6, "Scania", "G 410", 2021, "У 123 ЖЗ 54", "Тентованные", 20.0, 92.0, 1),
            (c6, "MAN", "TGS 18.360", 2019, "Ф 456 ИЙ 54", "Зерновозы", 24.0, 0.0, 0),
        ]
        cur.executemany(
            """INSERT INTO trucks
               (carrier_id,brand,model,year,plate_number,cargo_type,
                capacity_tons,volume_m3,is_available)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            trucks,
        )

        # ── Orders ────────────────────────────────────────────────
        orders = [
            # cu1: 2 new, 1 in_progress, 1 completed
            (cu1, None, "Перевозка производственного оборудования",
             "Промышленное оборудование", 8.5, 22.0,
             "Москва", "Санкт-Петербург", 710.0,
             "2026-05-20", "2026-05-22", 85000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Хрупкое оборудование, требуется бережная погрузка"),

            (cu1, None, "Сборный груз Москва — Екатеринбург",
             "Сборные грузы", 3.0, 14.0,
             "Москва", "Екатеринбург", 1800.0,
             "2026-05-28", "2026-06-02", 45000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Сборный груз из нескольких мест, паллеты"),

            (cu1, c1, "Доставка мебели для офиса",
             "Генеральные грузы", 3.2, 18.0,
             "Москва", "Балашиха", 28.0,
             "2026-05-12", "2026-05-13", 22000.0,
             "in_progress", "in_transit", "Иванов П.С.", "А 123 МК 77",
             1, 0, 21500.0,
             "Мебель в разобранном виде, требуется подъём на 4 этаж"),

            (cu1, c2, "Строительные материалы Москва-Подольск",
             "Строительные материалы", 12.0, 30.0,
             "Москва", "Подольск", 42.0,
             "2026-04-28", "2026-04-29", 18000.0,
             "completed", "completed", "Сидоров А.В.", "Е 567 ОП 50",
             1, 1, 17500.0, ""),

            # cu2: 1 new, 2 in_progress, 1 completed
            (cu2, None, "Перевозка продуктов питания Москва-Казань",
             "Продукты питания", 6.0, 24.0,
             "Москва", "Казань", 820.0,
             "2026-05-25", "2026-05-27", 95000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Рефрижератор обязателен, температура +2...+6°C"),

            (cu2, c1, "Медицинское оборудование в клинику",
             "Промышленное оборудование", 2.1, 8.5,
             "Москва", "Химки", 22.0,
             "2026-05-14", "2026-05-14", 35000.0,
             "in_progress", "dispatched", "Петров В.А.", "В 456 НП 77",
             0, 0, 33000.0,
             "Хрупкое, стерильная упаковка"),

            (cu2, c5, "Товары для магазина в Нижний Новгород",
             "Генеральные грузы", 5.0, 20.0,
             "Москва", "Нижний Новгород", 410.0,
             "2026-05-10", "2026-05-11", 38000.0,
             "in_progress", "vehicle_assigned", "Громов К.И.", "П 901 ЮЯ 52",
             0, 0, 37000.0,
             "Хрупкие товары, упакованы в коробки"),

            (cu2, c3, "Замороженные продукты для сети ресторанов",
             "Рефрижераторные", 4.5, 14.0,
             "Москва", "Нижний Новгород", 410.0,
             "2026-04-20", "2026-04-22", 62000.0,
             "completed", "completed", "Громов И.Д.", "К 456 ФХ 77",
             1, 1, 60000.0,
             "Температурный режим -18°C строго"),

            # cu3: 1 new, 1 in_progress, 1 completed
            (cu3, None, "Металлоконструкции на склад",
             "Строительные материалы", 18.0, 35.0,
             "Москва", "Мытищи", 20.0,
             "2026-05-22", "2026-05-22", 28000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Длинномер до 12 м"),

            (cu3, c4, "Строительный кран на объект",
             "Негабаритные", 25.0, 0.0,
             "Москва", "Тула", 175.0,
             "2026-05-15", "2026-05-16", 55000.0,
             "in_progress", "dispatched", "Никитин Е.В.", "Н 345 ЪЫ 50",
             1, 0, 54000.0,
             "Негабаритный груз, ширина 4.2 м"),

            (cu3, c3, "Замороженные продукты для ресторанов",
             "Рефрижераторные", 4.5, 14.0,
             "Москва", "Нижний Новгород", 410.0,
             "2026-04-20", "2026-04-22", 62000.0,
             "completed", "completed", "Громов И.Д.", "Л 789 ЦЧ 77",
             1, 1, 60000.0,
             "Температурный режим -18°C строго"),

            # cu4: 1 new, 1 in_progress, 1 completed
            (cu4, None, "Молочная продукция СПб — Москва",
             "Продукты питания", 8.0, 30.0,
             "Санкт-Петербург", "Москва", 710.0,
             "2026-05-26", "2026-05-27", 72000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Рефрижератор +2...+6°C, срок хранения ограничен"),

            (cu4, c3, "Морепродукты СПб — Нижний Новгород",
             "Рефрижераторные", 5.0, 18.0,
             "Санкт-Петербург", "Нижний Новгород", 1100.0,
             "2026-05-13", "2026-05-15", 88000.0,
             "in_progress", "in_transit", "Орлов Д.В.", "М 012 ШЩ 77",
             1, 0, 85000.0,
             "Температура -5°C, срочная доставка"),

            (cu4, c5, "Бакалея в Казань",
             "Генеральные грузы", 12.0, 40.0,
             "Санкт-Петербург", "Казань", 1540.0,
             "2026-04-10", "2026-04-13", 95000.0,
             "completed", "completed", "Громов К.И.", "С 567 ВГ 52",
             1, 1, 93000.0, ""),

            # cu5: 2 new, 1 in_progress
            (cu5, None, "Токарный станок Екатеринбург — Москва",
             "Промышленное оборудование", 12.0, 15.0,
             "Екатеринбург", "Москва", 1800.0,
             "2026-06-01", "2026-06-04", 120000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Тяжёлый станок 12 т, нужен манипулятор"),

            (cu5, None, "Металлопрокат на завод",
             "Строительные материалы", 22.0, 0.0,
             "Екатеринбург", "Тюмень", 330.0,
             "2026-05-30", "2026-05-30", 35000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Листовой металл 12м, длинномер"),

            (cu5, c4, "Промышленный компрессор",
             "Промышленное оборудование", 8.0, 12.0,
             "Москва", "Екатеринбург", 1800.0,
             "2026-05-08", "2026-05-12", 110000.0,
             "in_progress", "in_transit", "Никитин Е.В.", "О 678 ЬЭ 50",
             1, 0, 105000.0,
             "Хрупкое, манипулятор при выгрузке"),

            # cu6: 1 new, 1 completed
            (cu6, None, "Товары для маркетплейса — Казань — Москва",
             "Сборные грузы", 0.5, 2.0,
             "Казань", "Москва", 820.0,
             "2026-05-27", "2026-05-29", 8000.0,
             "new", "waiting", None, None, 0, 0, None,
             "Мелкий груз, возможна доставка попутно"),

            (cu6, c5, "Электроника в Нижний Новгород",
             "Генеральные грузы", 0.8, 3.0,
             "Казань", "Нижний Новгород", 415.0,
             "2026-04-15", "2026-04-16", 12000.0,
             "completed", "completed", "Громов К.И.", "Р 234 АБ 52",
             1, 1, 11500.0,
             "Хрупкое, ноутбуки и планшеты"),
        ]
        cur.executemany(
            """INSERT INTO orders
               (customer_id,carrier_id,title,cargo_type,cargo_weight,cargo_volume,
                from_city,to_city,distance,pickup_date,delivery_date,budget,
                status,progress_status,driver_name,truck_number,
                dispatch_confirmed_by_customer,arrival_confirmed_by_customer,
                final_cost,comment)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            orders,
        )

        def oid(prefix: str) -> int:
            cur.execute("SELECT id FROM orders WHERE title LIKE %s", (prefix + "%",))
            return cur.fetchone()["id"]

        o_equip   = oid("Перевозка производственного")
        o_sborny  = oid("Сборный груз Москва")
        o_mebel   = oid("Доставка мебели")
        o_stroit  = oid("Строительные материалы Москва-Подольск")
        o_prod    = oid("Перевозка продуктов питания")
        o_med     = oid("Медицинское оборудование")
        o_tovary  = oid("Товары для магазина в Нижний")
        o_zamor2  = oid("Замороженные продукты для сети")
        o_metal   = oid("Металлоконструкции на склад")
        o_kran    = oid("Строительный кран")
        o_zamor3  = oid("Замороженные продукты для ресторанов")
        o_moloko  = oid("Молочная продукция")
        o_more    = oid("Морепродукты")
        o_bakalea = oid("Бакалея")
        o_stanok  = oid("Токарный станок")
        o_metprok = oid("Металлопрокат")
        o_kompr   = oid("Промышленный компрессор")
        o_market  = oid("Товары для маркетплейса")
        o_elektr  = oid("Электроника в Нижний Новгород")

        # ── Responses ─────────────────────────────────────────────
        responses = [
            # new orders: pending responses
            (o_equip, c1, "Готовы выполнить! Работаем по данному маршруту регулярно. "
             "Собственный рефрижератор, GPS-мониторинг. Гарантируем сохранность.", 78000.0, 2, "pending"),
            (o_equip, c5, "Можем взять в работу. Есть свободный тентованный тягач. "
             "Цена включает страхование груза.", 82000.0, 3, "pending"),
            (o_sborny, c1, "Знаем маршрут, выполним быстро.", 43000.0, 5, "pending"),
            (o_sborny, c5, "Сборные грузы — наш профиль. Доставим в срок.", 41000.0, 6, "pending"),
            (o_prod, c3, "Рефрижератор в наличии, нужный температурный режим обеспечим. "
             "Опыт 8 лет в перевозке продуктов.", 92000.0, 2, "pending"),
            (o_prod, c1, "Также можем выполнить перевозку, есть реф-фура.", 94000.0, 3, "pending"),
            (o_metal, c4, "Специализируемся на длинномерах, берём.", 26500.0, 1, "pending"),
            (o_metal, c1, "Есть бортовой автомобиль, справимся.", 27000.0, 1, "pending"),
            (o_moloko, c3, "Рефрижератор свободен, нужный температурный режим гарантируем.", 68000.0, 1, "pending"),
            (o_stanok, c4, "Наш профиль — тяжеловесные грузы. Манипулятор есть.", 118000.0, 3, "pending"),
            (o_metprok, c4, "Длинномер в наличии, берём.", 33000.0, 1, "pending"),
            (o_market, c5, "Попутный груз — берём. Цена минимальная.", 7500.0, 2, "pending"),
            # accepted for in_progress orders
            (o_mebel, c1, "Берём в работу, знаем маршрут.", 21500.0, 1, "accepted"),
            (o_med,   c1, "Выполним аккуратно.", 33000.0, 1, "accepted"),
            (o_tovary, c5, "Знакомый маршрут, доставим в срок.", 37000.0, 1, "accepted"),
            (o_kran,  c4, "Наш профиль, негабарит возим регулярно.", 54000.0, 1, "accepted"),
            (o_more,  c3, "Рефрижератор готов, выезжаем.", 85000.0, 1, "accepted"),
            (o_kompr, c4, "Оборудование перевозим с манипулятором.", 105000.0, 4, "accepted"),
        ]
        cur.executemany(
            """INSERT INTO order_responses
               (order_id,carrier_id,message,proposed_cost,estimated_days,status)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            responses,
        )

        # ── Payments ──────────────────────────────────────────────
        def tx() -> str:
            return str(uuid.uuid4())[:16].upper()

        payments = [
            (o_mebel,   21500.0, cu1, c1, tx(), "held"),
            (o_stroit,  17500.0, cu1, c2, tx(), "released"),
            (o_med,     33000.0, cu2, c1, tx(), "held"),
            (o_tovary,  37000.0, cu2, c5, tx(), "held"),
            (o_zamor2,  60000.0, cu2, c3, tx(), "released"),
            (o_kran,    54000.0, cu3, c4, tx(), "held"),
            (o_zamor3,  60000.0, cu3, c3, tx(), "released"),
            (o_more,    85000.0, cu4, c3, tx(), "held"),
            (o_bakalea, 93000.0, cu4, c5, tx(), "released"),
            (o_kompr,  105000.0, cu5, c4, tx(), "held"),
            (o_elektr,  11500.0, cu6, c5, tx(), "released"),
        ]
        cur.executemany(
            """INSERT INTO payments
               (order_id,amount,payer_id,receiver_id,transaction_id,status)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT DO NOTHING""",
            payments,
        )

        # ── Reviews ───────────────────────────────────────────────
        reviews = [
            (cu1, c2, o_stroit, 5,
             "Отличная работа! Всё привезли точно в срок, груз без повреждений. "
             "Водитель очень вежливый и профессиональный, помог с разгрузкой. "
             "Стоимость соответствует качеству. Однозначно рекомендую!"),
            (cu2, c3, o_zamor2, 5,
             "Профессионалы своего дела! Строгий температурный режим соблюдён, "
             "продукты доставлены в идеальном состоянии. GPS-трекинг работал отлично, "
             "всегда знала где груз. Цена справедливая."),
            (cu3, c3, o_zamor3, 5,
             "Работаем с ЛогистикПро уже второй раз — всё на высшем уровне. "
             "Рефрижератор современный, документы в порядке, водитель пунктуален."),
            (cu4, c5, o_bakalea, 4,
             "В целом хорошая компания. Груз доставили, документы оформили правильно. "
             "Небольшая задержка из-за пробок, но предупредили заранее. "
             "Порекомендовал бы для дальних маршрутов."),
            (cu6, c5, o_elektr, 5,
             "Быстро и аккуратно! Груз — хрупкая электроника — дошёл в целости. "
             "Менеджер всегда на связи, подтвердили доставку фото. Спасибо!"),
            # carrier reviews of customers
            (c2, cu1, o_stroit, 5,
             "Приятный клиент, чёткие инструкции, груз был хорошо упакован. "
             "Оплата без задержек. Рекомендую для дальнейшего сотрудничества."),
            (c3, cu2, o_zamor2, 5,
             "Заказчик знает что хочет. Все требования чётко прописаны, "
             "документация готова заранее. Работать приятно."),
            (c5, cu4, o_bakalea, 4,
             "Хороший заказчик, оперативно выходит на связь. "
             "Загрузка прошла по плану, никаких проблем."),
        ]
        cur.executemany(
            """INSERT INTO reviews (reviewer_id,reviewed_user_id,order_id,rating,comment)
               VALUES (%s,%s,%s,%s,%s)""",
            reviews,
        )

        # update company ratings
        cur.execute("UPDATE company_profiles SET rating=4.4,rating_count=12 WHERE user_id=%s", (c2,))
        cur.execute("UPDATE company_profiles SET rating=4.8,rating_count=21 WHERE user_id=%s", (c3,))
        cur.execute("UPDATE company_profiles SET rating=4.6,rating_count=18 WHERE user_id=%s", (c5,))

        # ── Messages ──────────────────────────────────────────────
        msgs = [
            # cu1 ↔ c1 (мебель в работе)
            (cu1, c1, o_mebel, "Добрый день! Подтверждаете готовность забрать мебель завтра с 10:00?"),
            (c1, cu1, o_mebel,
             "Добрый день, Иван Александрович! Да, подтверждаем. Машина будет в 10:15. "
             "Водитель — Иванов П.С., телефон +7 (916) 100-20-30. "
             "Авто: Mercedes Actros, гос. номер А 123 МК 77."),
            (cu1, c1, o_mebel, "Отлично, спасибо! Буду ждать. Подъезд с торца здания, домофон #24."),
            (c1, cu1, o_mebel, "Принято! Водитель в курсе. Фото груза пришлём после загрузки."),

            # cu2 ↔ c1 (медоборудование)
            (cu2, c1, o_med,
             "Здравствуйте! Уточните, пожалуйста, текущий статус доставки медицинского оборудования в Химки?"),
            (c1, cu2, o_med,
             "Добрый день, Мария Ивановна! Груз погружен, выезжаем через 20 минут. "
             "Ориентировочное время прибытия — 14:30. "
             "Трекер: https://transgroup.ru/track (номер рейса: TG-2405)."),
            (cu2, c1, o_med, "Спасибо за оперативность! Встретим на месте."),
            (c1, cu2, o_med, "Хорошо, водитель позвонит за 30 минут до прибытия."),

            # cu2 ↔ c5 (товары в Н.Новгород)
            (cu2, c5, o_tovary, "Добрый день! Когда планируете загрузку?"),
            (c5, cu2, o_tovary,
             "Здравствуйте! Загрузка сегодня в 16:00, выезд завтра утром в 6:00. "
             "Приедет Громов К.И. на Volvo FM 410, номер П 901 ЮЯ 52."),
            (cu2, c5, o_tovary, "Принято. Склад работает до 18:00, адрес в заявке верный."),

            # cu3 ↔ c4 (кран)
            (cu3, c4, o_kran,
             "Нужно уточнить маршрут — на трассе М2 ограничение 3.5 м по высоте. "
             "Есть ли у вас разрешение на негабарит?"),
            (c4, cu3, o_kran,
             "Да, все разрешения оформлены, сопровождение включено. "
             "Едем через объезд по А108, там нет ограничений. Выезд завтра в 5:00."),
            (cu3, c4, o_kran, "Хорошо, на месте вас встретит прораб Семёнов, тел. +7 (910) 200-30-40."),
            (c4, cu3, o_kran, "Принято! Фото перед отправкой и после выгрузки — пришлём."),

            # cu4 ↔ c3 (морепродукты)
            (cu4, c3, o_more,
             "Добрый день! Груз — свежие морепродукты, критична скорость. "
             "Успеете до 18:00 четверга в Нижний?"),
            (c3, cu4, o_more,
             "Да, выезжаем сегодня в 22:00, прибудем к 08:00 четверга. "
             "Рефрижератор настроен на -5°C, GPS-мониторинг онлайн."),
            (cu4, c3, o_more, "Отлично! Контакт на месте: Петров Д., тел. +7 (831) 300-40-50."),

            # cu5 ↔ c4 (компрессор)
            (cu5, c4, o_kompr, "Как продвигается доставка? Мы ждём оборудование на объекте."),
            (c4, cu5, o_kompr,
             "Добрый день! Сейчас на перегоне Казань—Ижевск, идём по графику. "
             "Прибытие в Екатеринбург ожидается завтра в 14:00."),
            (cu5, c4, o_kompr, "Хорошо, кран-балка будет готов к разгрузке. Спасибо за обновление!"),

            # переговоры по новым заявкам
            (c1, cu1, o_equip,
             "Добрый день! Изучили вашу заявку на перевозку оборудования в СПб. "
             "Готовы взяться, можем выехать 20-го в 7:00. Цена — 78 000 ₽."),
            (cu1, c1, o_equip, "Спасибо за отклик! Подскажите, есть ли у вас страхование груза?"),
            (c1, cu1, o_equip, "Да, страхование включено, лимит 5 млн рублей. Договор пришлём по email."),

            (c3, cu2, o_prod,
             "Здравствуйте! По вашей заявке на перевозку продуктов в Казань — "
             "у нас есть свободный рефрижератор. Поддерживаем +2...+6°C, GPS."),
            (cu2, c3, o_prod, "Добрый день! А сколько машин у вас на маршруте Москва-Казань?"),
            (c3, cu2, o_prod, "2 рейса в неделю. Следующий выезд 25-го числа, как раз под вашу дату."),

            (c5, cu4, o_moloko,
             "Добрый день! Видим вашу заявку по молочной продукции СПб→Москва. "
             "У нас есть рефрижератор, нужный режим обеспечим. Цена: 68 000 ₽."),
            (cu4, c5, o_moloko, "Хорошо, а какой год выпуска рефрижератора?"),
            (c5, cu4, o_moloko, "2022 год, Schmitz SFR 24, агрегат Thermo King. Полностью исправен."),
        ]
        cur.executemany(
            """INSERT INTO messages (sender_id,receiver_id,order_id,content)
               VALUES (%s,%s,%s,%s)""",
            msgs,
        )

        # ── Notifications ─────────────────────────────────────────
        notifs = [
            # для cu1
            (cu1, "new_response", "Новый отклик на заявку",
             "ТрансГрупп откликнулись на «Перевозка производственного оборудования».\n"
             "Предложенная цена: 78 000 ₽.", o_equip),
            (cu1, "new_response", "Новый отклик на заявку",
             "ВолгаТранс откликнулись на «Перевозка производственного оборудования».\n"
             "Предложенная цена: 82 000 ₽.", o_equip),
            (cu1, "order_accepted", "Отклик принят",
             "Вы приняли отклик ТрансГрупп на заявку «Доставка мебели для офиса».\n"
             "Средства удержаны. Ожидайте отправку.", o_mebel),
            (cu1, "message", "Новое сообщение от ТрансГрупп",
             "ТрансГрупп: «Добрый день, Иван Александрович! Да, подтверждаем...»", o_mebel),
            # для cu2
            (cu2, "new_response", "Новый отклик на заявку",
             "ЛогистикПро откликнулись на «Перевозка продуктов питания».\n"
             "Предложенная цена: 92 000 ₽.", o_prod),
            (cu2, "order_accepted", "Отклик принят",
             "Вы приняли отклик ВолгаТранс на заявку «Товары для магазина».\n"
             "Средства удержаны.", o_tovary),
            (cu2, "message", "Новое сообщение",
             "ТрансГрупп: «Добрый день, Мария Ивановна! Груз погружен...»", o_med),
            # для cu3
            (cu3, "new_response", "Новый отклик на заявку",
             "ИП Никитин откликнулся на «Металлоконструкции на склад».", o_metal),
            (cu3, "order_accepted", "Отклик принят",
             "Вы приняли отклик ИП Никитин на «Строительный кран».", o_kran),
            # для cu4
            (cu4, "new_response", "Новый отклик",
             "ЛогистикПро откликнулись на «Молочная продукция СПб—Москва».", o_moloko),
            # для c1
            (c1, "order_accepted", "Ваш отклик принят!",
             "Заказчик принял ваш отклик на «Доставка мебели для офиса».\n"
             "Стоимость: 21 500 ₽. Средства удержаны системой.", o_mebel),
            (c1, "order_accepted", "Ваш отклик принят!",
             "Заказчик принял ваш отклик на «Медицинское оборудование в клинику».\n"
             "Стоимость: 33 000 ₽.", o_med),
            (c1, "message", "Новое сообщение от заказчика",
             "Иван Петров интересуется страхованием груза.", o_equip),
            # для c3
            (c3, "order_accepted", "Ваш отклик принят!",
             "Заказчик принял ваш отклик на «Морепродукты СПб—Нижний».\n"
             "Стоимость: 85 000 ₽.", o_more),
            # для c4
            (c4, "order_accepted", "Ваш отклик принят!",
             "Заказчик принял ваш отклик на «Строительный кран».\n"
             "Стоимость: 54 000 ₽.", o_kran),
            (c4, "order_accepted", "Ваш отклик принят!",
             "Заказчик принял ваш отклик на «Промышленный компрессор».\n"
             "Стоимость: 105 000 ₽.", o_kompr),
            # для c5
            (c5, "order_accepted", "Ваш отклик принят!",
             "Заказчик принял ваш отклик на «Товары для магазина».", o_tovary),
            (c5, "payment_released", "Оплата поступила!",
             "Заказчик подтвердил доставку «Бакалея в Казань». "
             "На ваш баланс зачислено 93 000 ₽.", o_bakalea),
        ]
        cur.executemany(
            """INSERT INTO notifications (user_id,type,title,message,related_id)
               VALUES (%s,%s,%s,%s,%s)""",
            notifs,
        )
