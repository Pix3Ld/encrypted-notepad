'''tu potem będzie pobieranie kluczy env narazie jest hardcodowane i genrowane przez fernet'''
from cryptography.fernet import Fernet

class Settings:
    def __init__(self):
        # w realnej wersji: wczytanie z .env
        self.SERVER_KEY = Fernet.generate_key()

settings = Settings()