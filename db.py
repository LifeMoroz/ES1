import sqlite3

PATH = "db.db"


class Database:
    """
    Класс обертка над базой, изолирует инициализацию БД и курсора
    """
    db = None

    def __init__(self, path):
        self._conn = sqlite3.connect(path)
        self._cursor = self._conn.cursor()

    @classmethod
    def get_database(cls):  # Несовместимые с клиентами интерфейс
        return Database(PATH)

    @classmethod
    def execute(cls, sql, params=None, unescape=None):
        self = Database.get_database()
        sql = sql.format(unescape) if unescape else sql
        try:
            if params:
                return self._cursor.execute(sql, params)
            else:
                return self._cursor.execute(sql)
        finally:
            self._conn.commit()


class Field:
    """
    Класс, экземпляр которого говорит нам о том, что это поле в базе
    """
    pass


class BaseActiveRecord:
    """
    Базовый класс реализующий основную функциональность ActiveRecord
    """
    table_name = None  # Имя таблицы
    id = Field()  # PK by default

    def __init__(self, *args, **kwargs):
        # Умная сборка объекта. Все что передано проставляем в объект.
        # Наследники будут определять что должно быть.
        """
        Конструктор
        :param args: неименованные аргументы
        :param kwargs: именованные аргументы
        """
        if args:  # Если есть неименованные аргументы, то
            for i, key in enumerate(self.fields()):  # для каждого поля класса, которое является полем в базе
                setattr(self, key, args[i])  # записываем из списка неименованных аргументов значение в объект класса

        elif kwargs:  # Иначе, если есть именованные аргументы, то
            for key in self.fields():  # для каждого поля класса, которое является полем в базе
                setattr(self, key, kwargs.get(key))  # Получаем его значение из аргументов и записываем в экземляр
        else:
            raise Exception

    @classmethod  # Тоже, что и static, только первым параметром идет cls, который является ссылкой на текущий класса
    def fields(cls):
        fields = []  # Пустой список
        for key in dir(cls):  # Для всех атрибутов класса
            if isinstance(getattr(cls, key), Field):  # проверить, является ли значение атрибута класса полем в базе
                fields.append(key)  # ЗАписать в список полей
        return fields  # Вернуть список полей

    @classmethod  # Тоже, что и static, только первым параметром идет cls, который является ссылкой на текущий класса
    def find(cls, **kwargs):
        """
        Отвечает за поиск по параметрам.
        :param kwargs: именованные аргументы
        :return: list объектов типа текущего cls
        """
        where = ''  # пустая строка
        data = []  # пустой список
        for key, value in kwargs.items():  # Для всех параметров поиска, получить ключ и значение
            if where:  # Если условие не пусто
                where += ' and '  # Добавить and в sql условие
            else:  # Иначе
                where = 'WHERE '  # sql условие начинается с WHERE
            if isinstance(value, list):  # Если значение, по которому производится поиск - массив, то
                where += '{} IN ({})'.format(key, ', '.join([str(x) for x in value]))  # Искать как по списку объектов
            else:  # Иначе
                where += '{}=?'.format(key)  # Поиск по одному значению
                data.append(value)  # Записать значение параметра поиска в список параметров поиска
        sql = "SELECT {fields} FROM {table_name} {where}"  # Формируем каркас запроса
        sql = sql.format(fields=', '.join(cls.fields()), table_name=cls.table_name, where=where)  # Выставляем поля которые хотим получить, имя таблицы и условия по которым искать
        result = []  # пустой массив
        for row in Database.get_database().execute(sql, data).fetchall():  # Выполнить sql запрос в БД
            result.append(cls(*row))  # Инициалировать экземдяр класса строкой из базы
        return result  # вернуть результат

    def save(self):
        """
        Сохраняет объект в базу, если существует - обновит, если нет - выполнит вставку
        :return: self
        """
        to_save = {}  # Поля для сохранения, пустой словарь
        for key in self.fields():  # Для каждого поля в базе
            to_save[key] = getattr(self, key)  # Получить значения соответствующего поля из экземпляра
            if key == 'id' and not isinstance(to_save[key], int):  # Получаем новый id
                to_save['id'] = max([x.id for x in self.find()] or [0]) + 1  # Находим максимальный id в базе и добавляем к нему 1
                setattr(self, 'id', to_save['id'])  # Записываем в экземпляр класса
        fields = ', '.join(to_save.keys())  # Поля для вставки/обновления
        values = ':' + ', :'.join(to_save.keys())  # В каком порядке будем подставлять
        sql = "REPLACE INTO {table_name} ({fields}) VALUES ({values})"  # Каркас Sql запроса
        sql = sql.format(table_name=self.table_name, fields=fields, values=values)  # Выставляем поля которые хотим записать, имя таблицы и значения полей
        Database.get_database().execute(sql, to_save)  # Выполнить запрос в бд
        return self

    def delete(self):
        """
        Удалить объект из базы
        """
        sql = "DELETE FROM {table_name} WHERE id={id}".format(table_name=self.table_name, id=self.id)  # Каркас sql и сразу подставляем имя таблицы и id записи, которую будем удалять
        Database.get_database().execute(sql)  # Исполняем sql
