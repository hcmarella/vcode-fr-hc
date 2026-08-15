import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    # Session tokens are high-entropy and single-use-as-a-secret, so a plain
    # fast hash (not argon2) is fine here -- unlike passwords, there's no
    # offline low-entropy guessing risk to slow down.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
