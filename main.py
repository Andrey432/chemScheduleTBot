import threading
from abc import ABC, abstractmethod
from pathlib import Path
import json
import telebot


SETTINGS_FILE = 'data/settings.json'
DATA_FILE = 'data/users.list'
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


class Bot(_Module):
    __slots__ = ('_bot',)

    def __init__(self):
        self._bot = None

    def load(self):
        self._bot = telebot.TeleBot(Core.get_instance().settings.get('telegram/token'))

    def command_start(self, message):
        pass

    def command_delete(self, message):
        pass

    def listening_server(self):
        self._bot.infinity_polling()


class Core(_Singleton):
    __slots__ = ('_bot', '_settings')

    def __init__(self):
        self._settings = Settings()
        self._bot = Bot()

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def settings(self) -> Settings:
        return self._settings

    def load_modules(self):
        self._settings.load()
        self._bot.load()


def main():
    core = Core.create_instance()
    core.load_modules()

    threading.Thread(target=core.bot.listening_server).start()


if __name__ == '__main__':
    main()
