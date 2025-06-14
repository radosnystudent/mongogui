import base64
import os

from cryptography.fernet import Fernet

# In a real app, store this key securely (e.g., in OS keyring or env var)
FERNET_KEY_ENV = "MONGOGUI_FERNET_KEY"


def get_fernet() -> Fernet:
    key = os.environ.get(FERNET_KEY_ENV)
    if not key:
        # Generate and print a key for setup
        key = Fernet.generate_key()
        print(f"[MongoGUI] Generated Fernet key: {key.decode()}")
        raise RuntimeError(
            f"Fernet key not set in environment variable {FERNET_KEY_ENV}"
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_password(password: str) -> str:
    f = get_fernet()
    token = f.encrypt(password.encode())
    return base64.urlsafe_b64encode(token).decode()


def decrypt_password(token_b64: str) -> str:
    f = get_fernet()
    token = base64.urlsafe_b64decode(token_b64.encode())
    return f.decrypt(token).decode()
