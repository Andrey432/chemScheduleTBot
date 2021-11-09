import json
import telebot
import threading
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC, abstractmethod


SETTINGS_FILE = 'data/settings.json'
DATA_FILE = 'data/data.json'
BASE_DIR = Path(__file__).parent


class _Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance

    @classmethod
    def create_instance(cls, allow_recreation=False):
        if not allow_recreation and cls._instance is not None:
            raise RuntimeError()
        cls._instance = cls()
        return cls._instance


class _Module(ABC):
    @abstractmethod
    def load(self):
        pass


class Settings(_Module):
    __slots__ = ('_json',)

    def __init__(self):
        self._json = None

    def load(self):
        with open(BASE_DIR / SETTINGS_FILE, 'r', encoding='utf-8') as fs:
            self._json = json.load(fs)

    def get(self, path: str):
        path = path.split('/')
        value = self._json
        for i in path:
            value = value[i]
        return value


class DataManager(_Module):
    def __init__(self):
        self._users = set()
        self._last_update = None

    def load(self):
        with open(BASE_DIR / DATA_FILE, 'r', encoding='utf-8') as fs:
            data = json.load(fs)
            self._users = set(data['users'])
            try:
                self._last_update = datetime.strptime(data['last_update'],
                                                      Core.get_instance().settings.get('system/data_st_fmt'))
            except Exception as ex:
                print(ex)
                self._last_update = datetime(1, 1, 1)

    def save(self):
        with open(BASE_DIR / DATA_FILE, 'w', encoding='utf-8') as fs:
            data = {
                'users': list(self._users),
                'last_update': self._last_update.strftime(Core.get_instance().settings.get('system/data_st_fmt'))
            }
            json.dump(data, fs, indent=4)

    def add_user(self, user_id: int):
        if user_id in self._users:
            return False
        self._users.add(user_id)
        return True

    def del_user(self, user_id: int) -> bool:
        try:
            self._users.remove(user_id)
        except KeyError:
            return False
        return True

    @property
    def users(self) -> set[int]:
        return set(self._users)

    @property
    def last_update(self) -> datetime:
        return self._last_update

    @last_update.setter
    def last_update(self, date: datetime):
        self._last_update = date


class Bot(_Module):
    __slots__ = ('_bot',)

    def __init__(self):
        self._bot = None

    def load(self):
        self._bot = telebot.TeleBot(Core.get_instance().settings.get('telegram/token'))

        self._bot.message_handler(commands=['start'])(self.command_start)
        self._bot.message_handler(commands=['delete'])(self.command_delete)

    def command_start(self, message):
        core = Core.get_instance()
        res = core.database.add_user(message.from_user.id)
        msg = 'messages/command_start_scs' if res else 'messages/command_start_err'
        self._bot.send_message(message.from_user.id, core.settings.get(msg))

    def command_delete(self, message):
        core = Core.get_instance()
        res = core.database.del_user(message.from_user.id)
        msg = 'messages/command_delete_scs' if res else 'messages/command_delete_err'
        self._bot.send_message(message.from_user.id, core.settings.get(msg))

    def listening_server(self):
        self._bot.infinity_polling()


class Core(_Singleton):
    __slots__ = ('_bot', '_settings', '_database')

    def __init__(self):
        self._settings = Settings()
        self._bot = Bot()
        self._database = DataManager()

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def database(self) -> DataManager:
        return self._database

    def load_modules(self):
        self._settings.load()
        self._database.load()
        self._bot.load()


def main():
    core = Core.create_instance()
    core.load_modules()

    threading.Thread(target=core.bot.listening_server).start()


if __name__ == '__main__':
    main()
