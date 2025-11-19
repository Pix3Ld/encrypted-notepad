from cryptography.fernet import Fernet
from nacl.public import PrivateKey, PublicKey, SealedBox
import base64
import json
from typing import Tuple, Optional


class EncryptionService:
    """Hybrydowy serwis szyfrowania

    - Symetryczne szyfrowanie treści: Fernet (cryptography)
    - Szyfrowanie klucza sesyjnego: SealedBox (PyNaCl)
    
    Zawiera też zachowanie kompatybilne z poprzednim API: jeśli podano
    `server_key` (Fernet key), dostępne są `encrypt_server` i `decrypt_server`
    Format paczki (bytes): UTF-8 encoded JSON z polami:
      {"version":"v1","enc_key":"<base64>","ciphertext":"<base64>"}
    """

    def __init__(self, server_key: Optional[bytes] = None):
        self.server_fernet = Fernet(server_key) if server_key is not None else None

    # --- Server-side (backwards compatible) ---
    def encrypt_server(self, data: str) -> bytes:
        """Szyfruje tekst przy użyciu serwerowego klucza Fernet
        Raises ValueError jeśli `server_key` nie został dostarczony przy inicjalizacji.
        """
        if self.server_fernet is None:
            raise ValueError("nie ma klucza_server do szyfrowania po stronie serwera")
        return self.server_fernet.encrypt(data.encode())

    # Legacy compatibility methods (old code used camelCase names)
    def encryptserver(self, data: str) -> bytes:
        """wsteczna kompatybilność dla `encrypt_server`"""
        return self.encrypt_server(data)

    def decrypt_server(self, data: bytes) -> str:
        """Deszyfruje dane zaszyfrowane przez `encrypt_server`"""
        if self.server_fernet is None:
            raise ValueError("nie skonfigurowano klucza_server do deszyfrowania po stronie serwera")
        return self.server_fernet.decrypt(data).decode()

    def decryptserver(self, data: bytes) -> str:
        """wsteczna kompatybilność dla `decrypt_server`"""
        return self.decrypt_server(data)

    # --- NaCl key helpers ---
    @staticmethod
    def generate_nacl_keypair() -> Tuple[bytes, bytes]:
        """Generuje parę kluczy NaCl.
        Zwraca (private_key_bytes, public_key_bytes).
        """
        sk = PrivateKey.generate()
        pk = sk.public_key
        return sk.encode(), pk.encode()

    @staticmethod
    def private_key_from_bytes(priv_bytes: bytes) -> PrivateKey:
        return PrivateKey(priv_bytes)

    @staticmethod
    def public_key_from_bytes(pub_bytes: bytes) -> PublicKey:
        return PublicKey(pub_bytes)

    # --- Hybrid encryption API ---
    def encrypt_for_recipient(self, plaintext: str, recipient_public_key: bytes) -> bytes:
        """Hybrydowo szyfruje `plaintext` dla odbiorcy o podanym publicznym kluczu NaCl
        Zwraca JSON-ową paczkę (bytes) z zaszyfrowanym kluczem sesyjnym i ciphertext
        """
        # wygeneruj klucz sesyjny Fernet
        session_key = Fernet.generate_key()  # bytes
        f = Fernet(session_key)
        ciphertext = f.encrypt(plaintext.encode())

        # zaszyfruj klucz sesyjny SealedBox-em do publicznego klucza odbiorcy
        pub = self.public_key_from_bytes(recipient_public_key)
        sealed = SealedBox(pub).encrypt(session_key)

        package = {
            "version": "v1",
            "enc_key": base64.b64encode(sealed).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        return json.dumps(package).encode()

    def decrypt_with_private(self, package_bytes: bytes, recipient_private_key: bytes) -> str:
        """Deszyfruje paczkę wygenerowaną przez `encrypt_for_recipient`
        `recipient_private_key` to surowe 32-bajtowe bytes wygenerowane przez `generate_nacl_keypair`
        """
        try:
            package = json.loads(package_bytes.decode())
            if package.get("version") != "v1":
                raise ValueError("unsupported package version")

            sealed = base64.b64decode(package["enc_key"])
            ciphertext = base64.b64decode(package["ciphertext"])

            priv = self.private_key_from_bytes(recipient_private_key)
            session_key = SealedBox(priv).decrypt(sealed)

            f = Fernet(session_key)
            plaintext = f.decrypt(ciphertext).decode()
            return plaintext
        except Exception as e:
            raise ValueError(f"decryption failed: {e}")

    
    