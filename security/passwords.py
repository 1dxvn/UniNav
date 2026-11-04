from passlib.context import CryptContext

from config import BCRYPT_MAX_PASSWORD_BYTES

password_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    if not plain:
        raise ValueError("Password cannot be empty.")
    if len(plain.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Password cannot exceed {BCRYPT_MAX_PASSWORD_BYTES} bytes.")
    return password_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False
