import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
class Settings:
    def __init__(self):
        load_dotenv()
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

        # JWT settings
        self.JWT_SECRET = os.getenv("JWT_SECRET", "i")
        # expiration in seconds
        try:
            self.JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))
        except ValueError:
            self.JWT_EXP_SECONDS = 3600

settings = Settings()