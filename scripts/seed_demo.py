"""
Скрипт для заполнения базы данных демо-данными.
Создает реалистичные данные для портфолио: заказчики, исполнители, заказы, отклики, рейтинги.
"""

import asyncio
import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Database
from app.constants import (
    CONSTRUCTION_TYPES,
    DOC_TYPES,
    EXPERIENCE_OPTIONS,
    MATCH_DECISION_LIKED,
    MATCH_DECISION_DECLINED,
    ORDER_STATUS_OPEN,
    ORDER_STATUS_CLOSED,
    SECTIONS_CAPITAL,
    SECTIONS_LINEAR,
)

# ============ РЕАЛИСТИЧНЫЕ ДАННЫЕ ============

# Компании-заказчики (строительные компании, девелоперы)
CUSTOMERS = [
    {"first_name": "Алексей", "last_name": "Воробьёв", "org": "ООО «СтройИнвест»", "phone": "+79161234567"},
    {"first_name": "Мария", "last_name": "Козлова", "org": "АО «Горжилстрой»", "phone": "+79262345678"},
    {"first_name": "Дмитрий", "last_name": "Новиков", "org": "ГК «Монолит»", "phone": "+79031234589"},
    {"first_name": "Елена", "last_name": "Соколова", "org": "ООО «ПромСтройПроект»", "phone": "+79857654321"},
    {"first_name": "Андрей", "last_name": "Петров", "org": "АО «МосИнжПроект»", "phone": "+79651237890"},
    {"first_name": "Ольга", "last_name": "Кузнецова", "org": "ООО «Девелопмент Групп»", "phone": "+79991112233"},
    {"first_name": "Сергей", "last_name": "Морозов", "org": "ПАО «Группа ЛСР»", "phone": "+79264445566"},
]

# Исполнители (проектировщики, инженеры)
EXECUTORS = [
    {
        "first_name": "Игорь", "last_name": "Смирнов", "org": "ИП Смирнов И.А.",
        "phone": "+79153216547", "exp": EXPERIENCE_OPTIONS[2],
        "resume": "Главный инженер проекта с опытом работы более 12 лет. Выполнил свыше 50 проектов жилых и административных зданий. Объекты прошли экспертизу Главгосэкспертизы.",
        "construction": [CONSTRUCTION_TYPES[0]], "sections_cap": SECTIONS_CAPITAL[:8], "sections_lin": []
    },
    {
        "first_name": "Наталья", "last_name": "Федорова", "org": None,
        "phone": "+79267894561", "exp": EXPERIENCE_OPTIONS[1],
        "resume": "Инженер-проектировщик ОВиК. Специализация: системы вентиляции торговых центров и складских комплексов. 7 лет опыта.",
        "construction": [CONSTRUCTION_TYPES[0]], "sections_cap": [SECTIONS_CAPITAL[10], SECTIONS_CAPITAL[11]], "sections_lin": []
    },
    {
        "first_name": "Павел", "last_name": "Волков", "org": "ООО «ПроектЭнерго»",
        "phone": "+79034567891", "exp": EXPERIENCE_OPTIONS[2],
        "resume": "Главный специалист по электроснабжению и электроосвещению. Реализовал проекты для объектов «Газпром», «Роснефть». Аттестация НАКС.",
        "construction": CONSTRUCTION_TYPES, "sections_cap": SECTIONS_CAPITAL[14:19], "sections_lin": [SECTIONS_LINEAR[6]]
    },
    {
        "first_name": "Анна", "last_name": "Белова", "org": None,
        "phone": "+79851234509", "exp": EXPERIENCE_OPTIONS[1],
        "resume": "Архитектор. Разработка АР, АИ для бизнес-центров и жилых комплексов. Работала в компании SPEECH, затем на фрилансе.",
        "construction": [CONSTRUCTION_TYPES[0]], "sections_cap": [SECTIONS_CAPITAL[2], SECTIONS_CAPITAL[3]], "sections_lin": []
    },
    {
        "first_name": "Виктор", "last_name": "Орлов", "org": "ИП Орлов В.С.",
        "phone": "+79657891234", "exp": EXPERIENCE_OPTIONS[2],
        "resume": "Инженер-конструктор КЖ, КМ. Расчёт несущих конструкций зданий до 25 этажей. Опыт 15 лет. Работал в ПИК, ДСК-1.",
        "construction": [CONSTRUCTION_TYPES[0]], "sections_cap": [SECTIONS_CAPITAL[4], SECTIONS_CAPITAL[5], SECTIONS_CAPITAL[6]], "sections_lin": []
    },
    {
        "first_name": "Екатерина", "last_name": "Лебедева", "org": "ООО «ГеоПроект»",
        "phone": "+79261597534", "exp": EXPERIENCE_OPTIONS[1],
        "resume": "Инженер генплана. Разработка ГП, вертикальной планировки, благоустройства. Объекты: ЖК, ТЦ, логистические комплексы.",
        "construction": [CONSTRUCTION_TYPES[0]], "sections_cap": [SECTIONS_CAPITAL[1]], "sections_lin": []
    },
    {
        "first_name": "Михаил", "last_name": "Титов", "org": None,
        "phone": "+79039876543", "exp": EXPERIENCE_OPTIONS[2],
        "resume": "Специалист по инженерным изысканиям и ПОС. Организация строительства сложных объектов. Сертификат НОСТРОЙ.",
        "construction": CONSTRUCTION_TYPES, "sections_cap": [SECTIONS_CAPITAL[21]], "sections_lin": [SECTIONS_LINEAR[14]]
    },
    {
        "first_name": "Ирина", "last_name": "Жукова", "org": "ООО «АкваПроект»",
        "phone": "+79854561237", "exp": EXPERIENCE_OPTIONS[1],
        "resume": "Инженер ВК и НВК. Проектирование систем водоснабжения и канализации для жилых и промышленных объектов.",
        "construction": CONSTRUCTION_TYPES, "sections_cap": [SECTIONS_CAPITAL[8], SECTIONS_CAPITAL[9]], "sections_lin": [SECTIONS_LINEAR[9], SECTIONS_LINEAR[10]]
    },
    {
        "first_name": "Роман", "last_name": "Григорьев", "org": "ИП Григорьев Р.О.",
        "phone": "+79167894560", "exp": EXPERIENCE_OPTIONS[0],
        "resume": "Начинающий проектировщик ПЗ и ООС. Опыт работы в проектном бюро 8 месяцев. Активно развиваюсь.",
        "construction": CONSTRUCTION_TYPES, "sections_cap": [SECTIONS_CAPITAL[0], SECTIONS_CAPITAL[23]], "sections_lin": [SECTIONS_LINEAR[0], SECTIONS_LINEAR[16]]
    },
    {
        "first_name": "Олег", "last_name": "Крылов", "org": "ООО «ДорПроект»",
        "phone": "+79263217896", "exp": EXPERIENCE_OPTIONS[2],
        "resume": "Ведущий инженер по линейным объектам. Автодороги, мосты, путепроводы. Опыт работы в Мостотресте, затем частная практика.",
        "construction": [CONSTRUCTION_TYPES[1]], "sections_cap": [], "sections_lin": [SECTIONS_LINEAR[2], SECTIONS_LINEAR[3], SECTIONS_LINEAR[4], SECTIONS_LINEAR[7]]
    },
    {
        "first_name": "Светлана", "last_name": "Макарова", "org": None,
        "phone": "+79851472583", "exp": EXPERIENCE_OPTIONS[1],
        "resume": "Сметчик. Составление смет на строительство и проектирование. Работа в Гранд-Смета, АВС. Опыт 5 лет.",
        "construction": CONSTRUCTION_TYPES, "sections_cap": [SECTIONS_CAPITAL[26]], "sections_lin": [SECTIONS_LINEAR[19]]
    },
    {
        "first_name": "Денис", "last_name": "Попов", "org": "ООО «ПожПроект»",
        "phone": "+79037418529", "exp": EXPERIENCE_OPTIONS[2],
        "resume": "Инженер по пожарной безопасности. Разработка разделов МПБ, АУПТ, СОУЭ. Лицензия МЧС. Более 100 выполненных проектов.",
        "construction": CONSTRUCTION_TYPES, "sections_cap": [SECTIONS_CAPITAL[24]], "sections_lin": [SECTIONS_LINEAR[17]]
    },
]

# Заказы (реальные проекты)
ORDERS = [
    {
        "name": "ЖК «Солнечный» — разделы КЖ, КМ",
        "doc_types": ["ПД", "РД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[4], SECTIONS_CAPITAL[5]],
        "sections_lin": [],
        "description": "Жилой комплекс 17 этажей, 3 секции. Требуется разработка конструктивных решений.",
        "price": "850 000 ₽",
        "expertise": True,
        "days_ago": 45,
    },
    {
        "name": "БЦ «Москва-Сити Тауэр» — раздел ОВиК",
        "doc_types": ["РД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[10]],
        "sections_lin": [],
        "description": "Бизнес-центр класса А, 32 этажа. Система вентиляции и кондиционирования.",
        "price": "1 200 000 ₽",
        "expertise": True,
        "days_ago": 30,
    },
    {
        "name": "Склад «Логистик Парк» — разделы ВК, НВК",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[8], SECTIONS_CAPITAL[9]],
        "sections_lin": [],
        "description": "Складской комплекс 25 000 м². Внутренние и наружные сети водоснабжения.",
        "price": "420 000 ₽",
        "expertise": True,
        "days_ago": 60,
    },
    {
        "name": "Реконструкция школы №127 — полный комплект",
        "doc_types": ["ПД", "РД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": SECTIONS_CAPITAL[:10],
        "sections_lin": [],
        "description": "Капитальный ремонт здания школы 1975 года постройки. Все разделы.",
        "price": "2 500 000 ₽",
        "expertise": True,
        "days_ago": 15,
    },
    {
        "name": "Газопровод высокого давления — 12 км",
        "doc_types": ["ПД", "РД"],
        "construction": [CONSTRUCTION_TYPES[1]],
        "sections_cap": [],
        "sections_lin": [SECTIONS_LINEAR[5], SECTIONS_LINEAR[14]],
        "description": "Магистральный газопровод DN 500. Требуется разработка ГСП и ПОС.",
        "price": "3 800 000 ₽",
        "expertise": True,
        "days_ago": 20,
    },
    {
        "name": "Автодорога к коттеджному посёлку",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[1]],
        "sections_cap": [],
        "sections_lin": [SECTIONS_LINEAR[2], SECTIONS_LINEAR[7]],
        "description": "Подъездная дорога 2.5 км, категория IV. Разделы АД, ТСОД.",
        "price": "650 000 ₽",
        "expertise": False,
        "days_ago": 8,
    },
    {
        "name": "ТЦ «Галерея» — раздел ЭС, ЭО",
        "doc_types": ["РД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[15], SECTIONS_CAPITAL[17]],
        "sections_lin": [],
        "description": "Торговый центр 45 000 м². Электроснабжение и освещение.",
        "price": "780 000 ₽",
        "expertise": True,
        "days_ago": 35,
    },
    {
        "name": "Котельная для ЖК — раздел ТМ",
        "doc_types": ["ПД", "РД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[11]],
        "sections_lin": [],
        "description": "Блочно-модульная котельная 6 МВт для жилого комплекса.",
        "price": "320 000 ₽",
        "expertise": True,
        "days_ago": 50,
    },
    {
        "name": "Мост через р. Клязьма",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[1]],
        "sections_cap": [],
        "sections_lin": [SECTIONS_LINEAR[4]],
        "description": "Автодорожный мост длиной 180 м. Раздел ИССО1 (мосты).",
        "price": "4 500 000 ₽",
        "expertise": True,
        "days_ago": 5,
    },
    {
        "name": "Офисное здание — раздел АР, АИ",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[2], SECTIONS_CAPITAL[3]],
        "sections_lin": [],
        "description": "Офис IT-компании, 5 этажей. Архитектура и дизайн интерьеров.",
        "price": "1 100 000 ₽",
        "expertise": False,
        "days_ago": 12,
    },
    {
        "name": "Многоуровневый паркинг — смета",
        "doc_types": ["ИД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[26]],
        "sections_lin": [],
        "description": "Подземный паркинг на 500 м/м. Составление сметной документации.",
        "price": "180 000 ₽",
        "expertise": False,
        "days_ago": 22,
    },
    {
        "name": "Пожарная безопасность — ТЦ «Мега»",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[24]],
        "sections_lin": [],
        "description": "Раздел МПБ для торгового центра. Расчёт пожарных рисков.",
        "price": "550 000 ₽",
        "expertise": True,
        "days_ago": 40,
    },
    {
        "name": "Водопровод к промзоне — 8 км",
        "doc_types": ["ПД", "РД"],
        "construction": [CONSTRUCTION_TYPES[1]],
        "sections_cap": [],
        "sections_lin": [SECTIONS_LINEAR[10]],
        "description": "Наружные сети водоснабжения промышленной зоны.",
        "price": "890 000 ₽",
        "expertise": True,
        "days_ago": 28,
    },
    {
        "name": "Детский сад — генплан",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[1]],
        "sections_lin": [],
        "description": "Детский сад на 280 мест. Разработка генерального плана участка.",
        "price": "95 000 ₽",
        "expertise": True,
        "days_ago": 18,
    },
    {
        "name": "Производственный цех — ПОС",
        "doc_types": ["ПД"],
        "construction": [CONSTRUCTION_TYPES[0]],
        "sections_cap": [SECTIONS_CAPITAL[21]],
        "sections_lin": [],
        "description": "Цех металлообработки. Проект организации строительства.",
        "price": "210 000 ₽",
        "expertise": True,
        "days_ago": 55,
    },
]

REVIEWS = [
    "Отличная работа! Проект сдан в срок, экспертиза пройдена с первого раза.",
    "Профессиональный подход, рекомендую.",
    "Хорошее качество документации, небольшие замечания устранены оперативно.",
    "Всё отлично, будем работать ещё.",
    "Грамотный специалист, знает своё дело.",
    "Рекомендую! Ответственный исполнитель.",
    "Работа выполнена качественно, сроки соблюдены.",
    "Экспертиза прошла без замечаний. Спасибо!",
]


async def seed_database():
    db_path = os.path.join("data", "demo.db")
    os.makedirs("data", exist_ok=True)
    
    # Удаляем старую БД если есть
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = Database(db_path)
    await db.init()
    
    print("🚀 Создание демо-данных для Тендо.про...")
    
    # Администратор
    admin = await db.create_user(100001, "+79001234567")
    await db.update_user_profile(admin["id"], "Администратор", "Системы", None)
    await db.set_user_roles(admin["id"], is_admin=True)
    await db.add_admin_phone("+79001234567")
    print("✅ Администратор создан")
    
    # Заказчики
    customer_ids = []
    for i, c in enumerate(CUSTOMERS):
        user = await db.create_user(200000 + i, c["phone"])
        await db.update_user_profile(user["id"], c["first_name"], c["last_name"], c["org"])
        await db.set_user_roles(user["id"], is_customer=True)
        customer_ids.append(user["id"])
    print(f"✅ Создано {len(CUSTOMERS)} заказчиков")
    
    # Исполнители
    executor_ids = []
    for i, e in enumerate(EXECUTORS):
        user = await db.create_user(300000 + i, e["phone"])
        await db.update_user_profile(user["id"], e["first_name"], e["last_name"], e["org"])
        await db.set_user_roles(user["id"], is_executor=True)
        await db.upsert_executor_profile(
            user["id"],
            e["exp"],
            None,
            e["resume"],
            DOC_TYPES,
            e["construction"],
            e["sections_cap"],
            e["sections_lin"],
        )
        executor_ids.append(user["id"])
    print(f"✅ Создано {len(EXECUTORS)} исполнителей")
    
    # Заказы
    order_ids = []
    for i, o in enumerate(ORDERS):
        customer_id = customer_ids[i % len(customer_ids)]
        deadline = (datetime.now() + timedelta(days=random.randint(30, 120))).strftime("%Y-%m-%d")
        
        order = await db.create_order(customer_id, {
            "name": o["name"],
            "doc_types": o["doc_types"],
            "construction_types": o["construction"],
            "sections_capital": o["sections_cap"],
            "sections_linear": o["sections_lin"],
            "description": o["description"],
            "deadline": deadline,
            "price": o["price"],
            "expertise_required": o["expertise"],
            "files_link": "https://disk.yandex.ru/d/example",
            "status": ORDER_STATUS_OPEN if i < 10 else ORDER_STATUS_CLOSED,
        })
        order_ids.append(order["id"])
    print(f"✅ Создано {len(ORDERS)} заказов")
    
    # Матчи и отклики
    match_count = 0
    for order_id in order_ids[:10]:
        order = await db.get_order(order_id)
        # Случайные исполнители откликаются
        for exec_id in random.sample(executor_ids, min(5, len(executor_ids))):
            customer_decision = random.choice([MATCH_DECISION_LIKED, MATCH_DECISION_DECLINED, None])
            executor_decision = random.choice([MATCH_DECISION_LIKED, MATCH_DECISION_DECLINED, None])
            await db.upsert_match(order_id, exec_id, customer_decision, executor_decision)
            match_count += 1
    print(f"✅ Создано {match_count} откликов")
    
    # Назначенные исполнители для закрытых заказов
    for order_id in order_ids[10:]:
        exec_id = random.choice(executor_ids)
        await db.assign_executor(order_id, exec_id)
        await db.upsert_match(order_id, exec_id, MATCH_DECISION_LIKED, MATCH_DECISION_LIKED)
    print("✅ Назначены исполнители для закрытых заказов")
    
    # Рейтинги и отзывы
    rating_count = 0
    for order_id in order_ids[10:]:
        order = await db.get_order(order_id)
        if order.get("assigned_executor_id"):
            # Заказчик оценивает исполнителя
            await db.add_rating(
                order_id,
                order["customer_id"],
                order["assigned_executor_id"],
                random.randint(4, 5),
                random.choice(REVIEWS)
            )
            # Исполнитель оценивает заказчика
            await db.add_rating(
                order_id,
                order["assigned_executor_id"],
                order["customer_id"],
                random.randint(4, 5),
                random.choice(REVIEWS)
            )
            rating_count += 2
    print(f"✅ Создано {rating_count} оценок")
    
    # Сообщения в помощь
    await db.add_help_message(customer_ids[0], "customer", "Как изменить срок исполнения в заказе?")
    await db.add_help_message(executor_ids[0], "executor", "Не приходят уведомления о новых заказах")
    print("✅ Добавлены тестовые обращения в помощь")
    
    print("\n🎉 Демо-база данных успешно создана!")
    print(f"📁 Путь: {os.path.abspath(db_path)}")
    
    # Статистика
    stats = await db.count_stats()
    print(f"\n📊 Статистика:")
    print(f"   Пользователей: {stats['users']}")
    print(f"   Заказчиков: {stats['customers']}")
    print(f"   Исполнителей: {stats['executors']}")
    print(f"   Заказов: {stats['orders']}")
    print(f"   В работе: {stats['in_work']}")


if __name__ == "__main__":
    asyncio.run(seed_database())
