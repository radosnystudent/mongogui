import base64
import os
from cryptography.fernet import Fernet

FERNET_KEY_ENV = "MONGOGUI_FERNET_KEY"


def get_fernet() -> Fernet:
    key = os.environ.get(FERNET_KEY_ENV)
    if not key:
        generated_key = Fernet.generate_key()
        print(f"[MongoGUI] Generated Fernet key: {generated_key.decode()}")
        raise RuntimeError(
            f"Fernet key not set in environment variable {FERNET_KEY_ENV}"
        )
    key_bytes: bytes = key.encode() if isinstance(key, str) else key
    return Fernet(key_bytes)


def encrypt_password(password: str) -> str:
    f = get_fernet()
    token = f.encrypt(password.encode())
    return base64.urlsafe_b64encode(token).decode()


def decrypt_password(token_b64: str) -> str:
    f = get_fernet()
    token = base64.urlsafe_b64decode(token_b64.encode())
    return f.decrypt(token).decode()
