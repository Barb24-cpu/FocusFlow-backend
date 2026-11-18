from cryptography.fernet import Fernet
from app.config import settings

# Generate a key once via: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
_fernet = Fernet(settings.FERNET_KEY.encode())


def encrypt_token(plain_token: str) -> str:
    return _fernet.encrypt(plain_token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    return _fernet.decrypt(encrypted_token.encode()).decode()