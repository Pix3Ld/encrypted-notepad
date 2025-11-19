import os
from cryptography.fernet import Fernet

class Settings:
    def __init__(self):
        env_key = os.getenv("SERVER_KEY")
        if env_key:
            # oczekujemy base64-encoded key (string)
            self.SERVER_KEY = env_key.encode()
        else:
            # fallback dla dev: wygeneruj i wypisz instrukcję
            key = Fernet.generate_key()
            self.SERVER_KEY = key
            print("WARNING: No SERVER_KEY in environment — generated ephemeral key.")
            print("Set SERVER_KEY env to persist across restarts:", key.decode())

settings = Settings()